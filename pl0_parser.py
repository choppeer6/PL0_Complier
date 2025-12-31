# 实现：使用 SLR 算法进行纯语法分析（无语义动作、无代码生成）
# 输入：tokens 列表，元素为 (sym_type, sym_val)
from collections import defaultdict, deque

class SLRParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.terminals = set()
        self.nonterminals = set()
        self.productions = []  # list of (LHS, RHS_list)
        self.start_symbol = 'S'
        self._build_grammar()
        self._collect_symbols()
        self._augment_grammar()
        self.states = []
        self.goto_table = {}
        self.action = {}
        self._build_canonical_collection()
        self._compute_first_follow()
        self._build_parsing_table()

    # -------------------- 语法定义（简化 PL/0 子集） --------------------
    def _build_grammar(self):
        # 非终结符和产生式（简化版 PL/0 语法，主要用于语法分析验证）
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
            ('statement', []),  # empty statement allowed
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
        # store productions
        self.productions = G

    def _collect_symbols(self):
        for lhs, rhs in self.productions:
            self.nonterminals.add(lhs)
            for sym in rhs:
                if sym.isupper() and sym not in ('=', '+', '-', '*', '/', ',', ';', '.', '(', ')', '<=', '>=', '<', '>', '#'):
                    pass
        all_rhs_syms = set(sym for _, rhs in self.productions for sym in rhs)
        # terminals = rhs_symbols - nonterminals
        self.terminals = set(s for s in all_rhs_syms if s not in self.nonterminals)

    def _augment_grammar(self):
        # add S' -> S
        self.productions.insert(0, (self.start_symbol, ['program']))
        # ensure start symbol is known as a nonterminal
        self.nonterminals.add(self.start_symbol)
        # keep track: productions indexed
        self.prod_index = list(range(len(self.productions)))

    # -------------------- LR(0) items / 状态集合构造 --------------------
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
        # productions need to be tuples for items
        prods = [(lhs, tuple(rhs)) for lhs, rhs in self.productions]
        # initial item S' -> . program
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
                if J is None:
                    continue
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

    # -------------------- FIRST / FOLLOW 计算 --------------------
    def _compute_first_follow(self):
        # FIRST
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
                    if '' in self.FIRST[sym]:
                        continue
                    else:
                        break
                else:
                  
                    res.add(sym)
                    break
            else:
                res.add('')
            return res

        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                lhs = lhs
                rhs_list = list(rhs)
                before = set(self.FIRST[lhs])
                if not rhs_list:
                    self.FIRST[lhs].add('')
                else:
                    fo = first_of_sequence(rhs_list)
                    self.FIRST[lhs] |= fo
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
                        first_beta = set()
                        if beta:
                            for sym in beta:
                                if sym in self.terminals:
                                    first_beta.add(sym)
                                    break
                                elif sym in self.nonterminals:
                                    first_beta |= (self.FIRST[sym] - set(['']))
                                    if '' in self.FIRST[sym]:
                                        continue
                                    else:
                                        break
                                else:
                                    first_beta.add(sym)
                                    break
                            else:
                                first_beta.add('')
                        else:
                            first_beta.add('')
                        before = set(self.FOLLOW[B])
                        if '' in first_beta:
                            self.FOLLOW[B] |= (self.FOLLOW[lhs] | (first_beta - set([''])))
                        else:
                            self.FOLLOW[B] |= first_beta
                        if self.FOLLOW[B] != before:
                            changed = True

    # -------------------- 构建 ACTION / GOTO 表 (SLR) --------------------
    def _build_parsing_table(self):
        # init
        N = len(self.states)
        self.action = [defaultdict(lambda: None) for _ in range(N)]
        self.goto = [defaultdict(lambda: None) for _ in range(N)]


        prod_list = list(self.productions)

        for i, I in enumerate(self.states):

            symbols_after_dot = set()
            for (lhs, rhs, dot) in I:
                if dot < len(rhs):
                    a = rhs[dot]
                    if a in self.terminals or a not in self.nonterminals:
                        # terminal
                        to_state = self.transitions.get((i, a))
                        if to_state is not None:
                            self.action[i][a] = ('s', to_state)
                else:

                    if lhs == self.start_symbol:
                        # accept on $
                        self.action[i]['$'] = ('acc',)
                    else:

                        for idx, prod in enumerate(prod_list):
                            if prod[0] == lhs and tuple(prod[1]) == tuple(rhs):
                                prod_idx = idx
                                break
                        else:
                            continue
                        for a in self.FOLLOW[lhs]:

                            if self.action[i][a] is None:
                                self.action[i][a] = ('r', prod_idx)

            for A in self.nonterminals:
                to = self.transitions.get((i, A))
                if to is not None:
                    self.goto[i][A] = to

    # -------------------- 解析接口 --------------------
    def _token_to_terminal(self, token):
        # token: (sym_type, sym_val)
        if token is None:
            return '$'
        sym_type, sym_val = token
        if sym_type == 'SYMBOL':
            return sym_val  # use actual punctuation as terminal
        return sym_type

    def parse(self):
        terms = [self._token_to_terminal(t) for t in self.tokens]
        terms.append('$')
        stack = [0]
        ip = 0
        while True:
            state = stack[-1]
            a = terms[ip]
            act = self.action[state].get(a)
            if act is None:
                # 优先尝试从 token 中提取行号信息，若存在则在错误信息中显示行号
                tok = self.tokens[ip] if ip < len(self.tokens) else None
                line_no = None
                try:
                    if isinstance(tok, (tuple, list)):
                        # 常见约定： (type, value, line) 或 (type, value, ..., line)
                        for idx in range(2, min(len(tok), 6)):
                            if isinstance(tok[idx], int):
                                line_no = tok[idx]
                                break
                    elif isinstance(tok, dict):
                        for k in ('line', 'lineno', 'start_line', 'row', 'line_no'):
                            if k in tok and isinstance(tok[k], int):
                                line_no = tok[k]
                                break
                    else:
                        for attr in ('line', 'lineno', 'start_line', 'row', 'line_no'):
                            ln = getattr(tok, attr, None)
                            if isinstance(ln, int):
                                line_no = ln
                                break
                except Exception:
                    line_no = None

                if line_no is not None:
                    raise SyntaxError(f"Unexpected token {tok} at line {line_no}")
                else:
                    raise SyntaxError(f"Unexpected token {tok} at position {ip}")
            if act[0] == 's':
                stack.append(act[1])
                ip += 1
            elif act[0] == 'r':
                prod_idx = act[1]
                lhs, rhs = self.productions[prod_idx]
                rhs_len = len(rhs)
                if rhs_len > 0:
                    for _ in range(rhs_len):
                        stack.pop()
                state_t = stack[-1]
                goto_state = self.goto[state_t].get(lhs)
                if goto_state is None:
                    raise SyntaxError(f"Invalid goto after reduction by {lhs} -> {list(rhs)}")
                stack.append(goto_state)
            elif act[0] == 'acc':
                return True
            else:
                raise SyntaxError("Unknown action in parsing table")

# -------------------- 对外接口 --------------------
def parse_tokens_with_slr(tokens):
    """
    tokens: list of (sym_type, sym_val)
    返回: True 表示语法合法，抛出 SyntaxError 表示语法错误
    """
    parser = SLRParser(tokens)
    return parser.parse()

# 若作为模块直接运行，做一个简单自检（不会执行实际文件操作）
if __name__ == "__main__":
    # 简单测试：一个非常简化的程序 token 序列 (对应: BEGIN END .)
    sample = [
        ('BEGIN', 'BEGIN'),
        ('END', 'END'),
        ('SYMBOL', '.'),
    ]
    try:
        ok = parse_tokens_with_slr(sample)
        print("Parse OK" if ok else "Parse Failed")
    except Exception as e:
        print("Parse error:", e)