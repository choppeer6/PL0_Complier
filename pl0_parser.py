from pl0_types import OpCode, Instruction, OPR_MAP

class Symbol:
    def __init__(self,name, kind, level=0, addr=0, val=0):
        self.name = name
        self.kind = kind  # 'const', 'var', 'proc'
        self.level = level
        self.addr = addr
        self.val = val

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.idx = 0
        self.code = []       # 生成的目标代码
        self.sym_table = []  # 符号表
        self.error_msg = ""
        
        # 当前 Token
        self.curr_sym = None
        self.curr_val = None
        self.advance()

    def advance(self):
        if self.idx < len(self.tokens):
            self.curr_sym, self.curr_val = self.tokens[self.idx]
            self.idx += 1
        else:
            self.curr_sym = None

    def gen(self, f, l, a):
        """生成一条 P-code 指令"""
        self.code.append(Instruction(f, l, a))

    def error(self, msg):
        raise Exception(f"Syntax Error: {msg} at token {self.curr_val}")

    def accept(self, sym_type):
        if self.curr_sym == sym_type:
            self.advance()
            return True
        return False

    def expect(self, sym_type):
        if self.curr_sym == sym_type:
            self.advance()
        else:
            self.error(f"Expected {sym_type}")

    # --- 语法规则实现 ---

    def block(self, level, tx):

        dx = 3 # 栈帧保留空间：Static Link, Dynamic Link, Return Address
        tx0 = tx # 保存当前符号表指针
        
        self.sym_table[tx].addr = len(self.code) # 记录过程入口地址
        
        # 【修复点】：必须先生成一条占位的 INT 指令，否则列表长度不够，后面回填会报错
        self.gen(OpCode.INT, 0, 0)
        if self.curr_sym == 'CONST':
            self.advance()
            while True:
                name = self.curr_val; self.expect('ID')
                self.expect('SYMBOL'); num = int(self.curr_val); self.expect('NUMBER')
                #self.sym_table.append(Symbol('const', val=num)) # 入符号表
                self.sym_table.append(Symbol(name, 'const', val=num)) 
                if not self.accept('SYMBOL'): break

        if self.curr_sym == 'VAR':
            self.advance()
            while True:
                name = self.curr_val
                self.expect('ID')
                self.sym_table.append(Symbol(name,'var', level, dx))
                dx += 1
                
                # 核心修改：明确检查是逗号还是分号
                if self.curr_sym == 'SYMBOL' and self.curr_val == ',':
                    self.advance() # 吃掉逗号，继续循环解析下一个变量
                    continue
                elif self.curr_sym == 'SYMBOL' and self.curr_val == ';':
                    self.advance() # 吃掉分号，结束变量声明
                    break
                else:
                    self.error("Expected ',' or ';' in var declaration")
        while self.curr_sym == 'PROCEDURE':
            self.advance()
            name = self.curr_val; self.expect('ID'); self.expect('SYMBOL') # ';'
            self.sym_table.append(Symbol('proc', level, len(self.code))) # 记录过程
            self.block(level + 1, len(self.sym_table) - 1) # 递归编译过程
            self.expect('SYMBOL') # ';'
        
        # 修正过程调用的跳转地址 (回填)
        # 这是一个简化版，完整的 PL/0 会在过程开始生成 JMP，这里直接生成 INT
        self.code[self.sym_table[tx0].addr] = Instruction(OpCode.INT, 0, dx)
        self.statement(level)
        self.gen(OpCode.OPR, 0, 0) # Return

    def statement(self, level):
        if self.curr_sym == 'ID': # Assignment
            # 查找符号表
            #sym = next((s for s in reversed(self.sym_table) if isinstance(s, Symbol)), None)
            # 简化：假设找到了并且是 var (实际需按名字查找)
            # 真实实现需遍历符号表匹配 name
            
            # 为了演示，这里做极其简化的处理：假设最近的一个ID匹配
            # 实际代码需要完善符号查找逻辑 (find_symbol)
            pass 
            # self.expression(level)
            # self.gen(OpCode.STO, level - sym.level, sym.addr)
            name = self.curr_val
            # 由于符号表查找逻辑较长，这里仅展示结构
            self.advance()
            self.expect('ASSIGN')
            self.expression(level)

            sym = self.find_symbol(name)
            if sym.kind != 'var': self.error("Assignment to non-variable")
            self.gen(OpCode.STO, level - sym.level, sym.addr)

        elif self.curr_sym == 'CALL':
            self.advance(); self.expect('ID')
            self.gen(OpCode.CAL, 0, 0) # 同样需要符号表查找地址

        elif self.curr_sym == 'BEGIN':
            self.advance()
            self.statement(level)
            while self.curr_sym == 'SYMBOL' and self.curr_val == ';':
                self.advance()
                self.statement(level)
            self.expect('END')

        elif self.curr_sym == 'IF':
            self.advance(); self.condition(level); self.expect('THEN')
            cx1 = len(self.code); self.gen(OpCode.JPC, 0, 0)
            self.statement(level)
            self.code[cx1].a = len(self.code) # 回填地址

        elif self.curr_sym == 'WHILE':
            cx1 = len(self.code)
            self.advance(); self.condition(level); self.expect('DO')
            cx2 = len(self.code); self.gen(OpCode.JPC, 0, 0)
            self.statement(level)
            self.gen(OpCode.JMP, 0, cx1)
            self.code[cx2].a = len(self.code)
        
        elif self.curr_sym == 'READ':
             self.advance(); self.expect('SYMBOL'); # '('
             self.expect('ID'); # 实际应查找变量
             self.expect('SYMBOL'); # ')'
             self.gen(OpCode.RED, 0, 0) # Read into stack top
             self.gen(OpCode.STO, 0, 0) # Store to var

        elif self.curr_sym == 'WRITE':
            self.advance(); self.expect('SYMBOL'); 
            self.expression(level)
            self.expect('SYMBOL')
            self.gen(OpCode.WRT, 0, 0)

    def expression(self, level):
        # 简单处理：term { + term }
        self.term(level)
        while self.curr_sym == 'SYMBOL' and self.curr_val in ['+', '-']:
            op = self.curr_val
            self.advance()
            self.term(level)
            self.gen(OpCode.OPR, 0, OPR_MAP[op])

    def term(self, level):
        self.factor(level)
        while self.curr_sym == 'SYMBOL' and self.curr_val in ['*', '/']:
            op = self.curr_val
            self.advance()
            self.factor(level)
            self.gen(OpCode.OPR, 0, OPR_MAP[op])

    def factor(self, level):
        if self.curr_sym == 'ID':
            name = self.curr_val
            sym = self.find_symbol(name)
            
            # --- 修复开始：补充缺失的代码生成和指针移动 ---
            if sym.kind == 'const':
                self.gen(OpCode.LIT, 0, sym.val)
            elif sym.kind == 'var':
                self.gen(OpCode.LOD, level - sym.level, sym.addr)
            
            self.advance() # <--- 关键！必须吃掉这个变量名，进入下一个 Token
            # --- 修复结束 ---
            
        elif self.curr_sym == 'NUMBER':
            self.gen(OpCode.LIT, 0, int(self.curr_val))
            self.advance()
        elif self.curr_sym == 'SYMBOL' and self.curr_val == '(':
            self.advance()
            self.expression(level)
            self.expect('SYMBOL') # ')'

    def condition(self, level):
        if self.curr_sym == 'ODD':
            self.advance(); self.expression(level); self.gen(OpCode.OPR, 0, 6)
        else:
            self.expression(level)
            if self.curr_sym == 'SYMBOL' and self.curr_val in ['=', '#', '<', '>', '<=', '>=']:
                op = self.curr_val
                self.advance()
                self.expression(level)
                self.gen(OpCode.OPR, 0, OPR_MAP[op])

    def parse(self):
        # 初始化主程序 Block
        # 符号表 placeholder
        self.sym_table.append(Symbol('proc', -1, 0)) 
        
        # JMP to main entry (will be fixed later)
        self.gen(OpCode.JMP, 0, 0) 
        
        # 这里为了演示，我们只解析一个 Block
        # 真正的 PL/0 应该在 Block 之后加 "."
        self.block(0, 0)
        self.code[0].a = 1 # Update jump to main block start
        return self.code
    
    #符号查找逻辑
    def find_symbol(self, name):
        # 倒序查找，保证最近的作用域优先
        for sym in reversed(self.sym_table):
            if sym.name == name:
                return sym
        self.error(f"Undefined symbol: {name}")