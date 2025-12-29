from collections import defaultdict, deque

class SLRParser:
    def __init__(self, tokens):
        # tokens 格式期望为 [(type, value, line), ...]
        self.tokens = tokens
        self.terminals = set()
        self.nonterminals = set()
        self.productions = []
        self.start_symbol = 'S'
        
        # 初始化构建过程
        self._build_grammar()
        self._collect_symbols()
        self._augment_grammar()
        self.states = []
        self.goto_table = {}
        self.action = {}
        self._build_canonical_collection()
        self._compute_first_follow()
        self._build_parsing_table()

    def _build_grammar(self):
        """定义 PL/0 的简化文法产生式 (LHS -> RHS list)"""
        G = [
            ('program', ['block', '.']),
            ('block', ['consts', 'vars', 'procs', 'statement']),
            ('consts', []),
            ('consts', ['CONST', 'const_list', ';']),
            ('const_list', ['ID', '=', 'NUMBER', 'const_list_tail']),
            ('const_list_tail', []),
            ('const_list_tail', [',', 'ID', '=', 'NUMBER', 'const_list_tail']),
            ('vars', []),
            ('vars', ['VAR', 'id_list', ';']),
            ('id_list', ['ID', 'id_list_tail']),
            ('id_list_tail', []),
            ('id_list_tail', [',', 'ID', 'id_list_tail']),
            ('procs', []),
            ('procs', ['PROCEDURE', 'ID', ';', 'block', ';', 'procs']),
            ('statement', []),  # 允许空语句
            ('statement', ['ID', 'ASSIGN', 'expression']),
            ('statement', ['CALL', 'ID']),
            ('statement', ['BEGIN', 'stmt_list', 'END']),
            ('statement', ['IF', 'condition', 'THEN', 'statement']),
            ('statement', ['WHILE', 'condition', 'DO', 'statement']),
            ('statement', ['READ', '(', 'ID', ')']),
            ('statement', ['WRITE', '(', 'expression', ')']),
            ('stmt_list', ['statement', 'stmt_list_tail']),
            ('stmt_list_tail', []),
            ('stmt_list_tail', [';', 'statement', 'stmt_list_tail']),
            ('expression', ['term', 'expression_tail']),
            ('expression_tail', []),
            ('expression_tail', ['+', 'term', 'expression_tail']),
            ('expression_tail', ['-', 'term', 'expression_tail']),
            ('term', ['factor', 'term_tail']),
            ('term_tail', []),
            ('term_tail', ['*', 'factor', 'term_tail']),
            ('term_tail', ['/', 'factor', 'term_tail']),
            ('factor', ['ID']),
            ('factor', ['NUMBER']),
            ('factor', ['(', 'expression', ')']),
            ('condition', ['ODD', 'expression']),
            ('condition', ['expression', 'relop', 'expression']),
            ('relop', ['=']),
            ('relop', ['#']),
            ('relop', ['<']),
            ('relop', ['>']),
            ('relop', ['<=']),
            ('relop', ['>=']),
        ]
        self.productions = G

    def _collect_symbols(self):
        """收集所有的终结符和非终结符"""
        for lhs, rhs in self.productions:
            self.nonterminals.add(lhs)
            for sym in rhs:
                # 简单的大写判断法，排除特定的运算符符号
                if sym.isupper() and sym not in ('=', '+', '-', '*', '/', ',', ';', '.', '(', ')', '<=', '>=', '<', '>', '#'):
                    pass 
        
        all_rhs_syms = set(sym for _, rhs in self.productions for sym in rhs)
        self.terminals = set(s for s in all_rhs_syms if s not in self.nonterminals)

    def _augment_grammar(self):
        """拓广文法：添加 S' -> program"""
        self.productions.insert(0, (self.start_symbol, ['program']))
        self.nonterminals.add(self.start_symbol)

    # --- LR(0) 项集族构建逻辑 ---
    def _closure(self, items):
        closure = set(items)
        added = True
        while added:
            added = False
            new_items = set()
            for (lhs, rhs, dot) in closure:
                if dot < len(rhs):
                    B = rhs[dot]
                    if B in self.nonterminals:
                        for (p_lhs, p_rhs) in self.productions:
                            if p_lhs == B:
                                itm = (p_lhs, tuple(p_rhs), 0)
                                if itm not in closure:
                                    new_items.add(itm)
            if new_items:
                closure |= new_items
                added = True
        return frozenset(closure)

    def _goto(self, state, X):
        moved = set()
        for (lhs, rhs, dot) in state:
            if dot < len(rhs) and rhs[dot] == X:
                moved.add((lhs, rhs, dot + 1))
        if not moved:
            return None
        return self._closure(moved)

    def _items(self):
        start_item = (self.start_symbol, tuple(self.productions[0][1]), 0)
        I0 = self._closure([start_item])
        C = [I0]
        queue = deque([I0])
        transitions = {}
        
        while queue:
            I = queue.popleft()
            syms = set()
            for (lhs, rhs, dot) in I:
                if dot < len(rhs):
                    syms.add(rhs[dot])
            for X in syms:
                J = self._goto(I, X)
                if J is None: continue
                if J not in C:
                    C.append(J)
                    queue.append(J)
                transitions[(C.index(I), X)] = C.index(J)
        return C, transitions

    def _build_canonical_collection(self):
        self.productions = [(lhs, tuple(rhs)) for lhs, rhs in self.productions]
        C, transitions = self._items()
        self.states = C
        self.transitions = transitions

    # --- First & Follow 集计算 ---
    def _compute_first_follow(self):
        self.FIRST = {nt: set() for nt in self.nonterminals}
        
        def first_of_sequence(seq):
            res = set()
            if not seq:
                res.add('')
                return res
            for sym in seq:
                if sym in self.terminals:
                    res.add(sym)
                    break
                elif sym in self.nonterminals:
                    res |= (self.FIRST[sym] - set(['']))
                    if '' not in self.FIRST[sym]:
                        break
                else: 
                    res.add(sym)
                    break
            else:
                res.add('')
            return res

        # FIRST
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                before = set(self.FIRST[lhs])
                if not rhs:
                    self.FIRST[lhs].add('')
                else:
                    self.FIRST[lhs] |= first_of_sequence(rhs)
                if self.FIRST[lhs] != before:
                    changed = True

        # FOLLOW
        self.FOLLOW = {nt: set() for nt in self.nonterminals}
        self.FOLLOW[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                rhs_list = list(rhs)
                for i, B in enumerate(rhs_list):
                    if B in self.nonterminals:
                        beta = rhs_list[i+1:]
                        first_beta = first_of_sequence(beta)
                        before = set(self.FOLLOW[B])
                        self.FOLLOW[B] |= (first_beta - set(['']))
                        if '' in first_beta:
                            self.FOLLOW[B] |= self.FOLLOW[lhs]
                        if self.FOLLOW[B] != before:
                            changed = True

    # --- 构建 Action 和 Goto 表 ---
    def _build_parsing_table(self):
        N = len(self.states)
        self.action = [defaultdict(lambda: None) for _ in range(N)]
        self.goto = [defaultdict(lambda: None) for _ in range(N)]
        prod_list = list(self.productions)

        for i, I in enumerate(self.states):
            for (lhs, rhs, dot) in I:
                if dot < len(rhs):
                    a = rhs[dot]
                    if a in self.terminals:
                        to_state = self.transitions.get((i, a))
                        if to_state is not None:
                            self.action[i][a] = ('s', to_state)
                else:
                    if lhs == self.start_symbol:
                        self.action[i]['$'] = ('acc',)
                    else:
                        prod_idx = -1
                        for idx, prod in enumerate(prod_list):
                            if prod[0] == lhs and prod[1] == rhs:
                                prod_idx = idx
                                break
                        for a in self.FOLLOW[lhs]:
                            if self.action[i][a] is None:
                                self.action[i][a] = ('r', prod_idx)
            
            for A in self.nonterminals:
                to = self.transitions.get((i, A))
                if to is not None:
                    self.goto[i][A] = to

    # --- 核心解析方法 ---
    def _token_to_terminal(self, token):
        """将 Token 对象转换为文法终结符字符串"""
        if token is None: return '$'
        # Token 格式: (type, value, line)
        sym_type, sym_val, _ = token
        
        if sym_type == 'SYMBOL':
            return sym_val 
        return sym_type

    def parse(self):
        """
        执行语法分析
        :return: True (如果成功)
        :raise: SyntaxError (如果失败，包含行号)
        """
        terms = [self._token_to_terminal(t) for t in self.tokens]
        terms.append('$')
        
        stack = [0]
        ip = 0 # 输入指针
        
        while True:
            state = stack[-1]
            a = terms[ip]
            act = self.action[state].get(a)

            # --- 错误捕获 ---
            if act is None:
                current_token = self.tokens[ip] if ip < len(self.tokens) else None
                if current_token:
                    t_type, t_val, t_line = current_token
                    raise SyntaxError(f"在第 {t_line} 行附近发现语法错误: 意外的 Token '{t_val}'")
                else:
                    raise SyntaxError("语法错误: 文件意外结束 (Incomplete input)")

            # --- 动作执行 ---
            if act[0] == 's': # 移进
                stack.append(act[1])
                ip += 1
            elif act[0] == 'r': # 归约
                prod_idx = act[1]
                lhs, rhs = self.productions[prod_idx]
                rhs_len = len(rhs)
                if rhs_len > 0:
                    for _ in range(rhs_len):
                        stack.pop()
                
                state_t = stack[-1]
                goto_state = self.goto[state_t].get(lhs)
                if goto_state is None:
                    raise SyntaxError(f"严重错误: 归约后无法进行状态转移 {lhs}")
                stack.append(goto_state)
            elif act[0] == 'acc': # 接受
                return True
            else:
                raise SyntaxError("未知解析动作")