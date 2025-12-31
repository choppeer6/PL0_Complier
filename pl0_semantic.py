"""
PL/0 语义分析与中间代码生成模块（四元式形式）
实现功能：
1. 符号表管理（常量、变量、过程）
2. 语义检查（类型检查、作用域检查、声明检查）
3. 中间代码生成（四元式）
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum

# ==========================================
# 1. 符号表相关定义
# ==========================================

class SymbolType(Enum):
    """符号类型"""
    CONST = "常量"
    VAR = "变量"
    PROCEDURE = "过程"

class Symbol:
    """符号表项"""
    def __init__(self, name: str, sym_type: SymbolType, level: int, 
                 value: int = 0, address: int = 0):
        self.name = name           # 符号名称
        self.type = sym_type       # 符号类型
        self.level = level         # 所在层次
        self.value = value         # 常量值（仅对常量有效）
        self.address = address     # 地址/偏移量
    
    def __repr__(self):
        if self.type == SymbolType.CONST:
            return f"{self.name}\t{self.type.value}\t{self.level}\t{self.value}\t-"
        elif self.type == SymbolType.VAR:
            return f"{self.name}\t{self.type.value}\t{self.level}\t-\t{self.address}"
        else:
            return f"{self.name}\t{self.type.value}\t{self.level}\t{self.address}\t-"

class SymbolTable:
    """符号表管理器"""
    def __init__(self):
        self.symbols: List[Symbol] = []
        self.level = 0              # 当前层次
        self.address_stack = [0]    # 每层的地址分配栈
    
    def enter_scope(self):
        """进入新的作用域（层次+1）"""
        self.level += 1
        self.address_stack.append(0)
    
    def exit_scope(self):
        """退出当前作用域"""
        self.symbols = [s for s in self.symbols if s.level < self.level]
        self.level -= 1
        self.address_stack.pop()
    
    def define_const(self, name: str, value: int):
        """定义常量"""
        if self._lookup_current_level(name):
            raise SemanticError(f"常量 '{name}' 在当前层次已定义")
        
        symbol = Symbol(name, SymbolType.CONST, self.level, value=value)
        self.symbols.append(symbol)
    
    def define_var(self, name: str) -> int:
        """定义变量，返回分配的地址"""
        if self._lookup_current_level(name):
            raise SemanticError(f"变量 '{name}' 在当前层次已定义")
        
        address = self.address_stack[-1]
        self.address_stack[-1] += 1
        
        symbol = Symbol(name, SymbolType.VAR, self.level, address=address)
        self.symbols.append(symbol)
        return address
    
    def define_procedure(self, name: str, entry_address: int):
        """定义过程"""
        if self._lookup_current_level(name):
            raise SemanticError(f"过程 '{name}' 在当前层次已定义")
        
        symbol = Symbol(name, SymbolType.PROCEDURE, self.level, address=entry_address)
        self.symbols.append(symbol)
        return symbol
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """查找符号（从内向外查找）"""
        for symbol in reversed(self.symbols):
            if symbol.name == name:
                return symbol
        return None
    
    def _lookup_current_level(self, name: str) -> Optional[Symbol]:
        """仅在当前层次查找符号"""
        for symbol in reversed(self.symbols):
            if symbol.level < self.level:
                break
            if symbol.name == name:
                return symbol
        return None
    
    def print_table(self):
        """打印符号表"""
        print("\n符号表:")
        print(f"{'名字':<10} {'类型':<8} {'层次':<6} {'值':<8} {'地址'}")
        print("-" * 50)
        for symbol in self.symbols:
            print(symbol)

# ==========================================
# 2. 四元式定义
# ==========================================

class Quadruple:
    """四元式 (op, arg1, arg2, result)"""
    def __init__(self, op: str, arg1: str = "-", arg2: str = "-", result: str = "-"):
        self.op = op          # 操作符
        self.arg1 = arg1      # 第一个操作数
        self.arg2 = arg2      # 第二个操作数
        self.result = result  # 结果
    
    def __repr__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"
    
    def to_string(self, index: int) -> str:
        """格式化输出"""
        return f"{index}\t{self.op}\t{self.arg1}\t{self.arg2}\t{self.result}"

# ==========================================
# 3. 语义错误定义
# ==========================================

class SemanticError(Exception):
    """语义错误"""
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line
        super().__init__(self.format_message())
    
    def format_message(self):
        if self.line > 0:
            return f"语义错误 (行 {self.line}): {self.message}"
        return f"语义错误: {self.message}"

# ==========================================
# 4. 递归下降语法分析器 + 四元式生成器
# ==========================================

class SemanticAnalyzer:
    """语义分析器，生成四元式中间代码"""
    
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = None
        self.symbol_table = SymbolTable()
        self.quadruples: List[Quadruple] = []  # 四元式列表
        self.temp_count = 0  # 临时变量计数器
        self.label_count = 0  # 标签计数器
        self.errors: List[str] = []
        
        if self.tokens:
            self.current_token = self.tokens[0]
    
    # -------------------- 辅助方法 --------------------
    
    def new_temp(self) -> str:
        """生成新的临时变量"""
        temp = f"T{self.temp_count}"
        self.temp_count += 1
        return temp
    
    def new_label(self) -> str:
        """生成新的标签"""
        label = f"L{self.label_count}"
        self.label_count += 1
        return label
    
    def emit(self, op: str, arg1: str = "-", arg2: str = "-", result: str = "-"):
        """生成一条四元式"""
        quad = Quadruple(op, arg1, arg2, result)
        self.quadruples.append(quad)
        return len(self.quadruples) - 1  # 返回四元式的索引
    
    def backpatch(self, index: int, label: str):
        """回填标签"""
        if 0 <= index < len(self.quadruples):
            self.quadruples[index].result = label
    
    def error(self, message: str):
        """记录错误"""
        line = self._get_current_line()
        error_msg = f"错误 (行 {line}): {message}"
        self.errors.append(error_msg)
        raise SemanticError(message, line)
    
    def _get_current_line(self) -> int:
        """获取当前token的行号"""
        if self.current_token:
            if isinstance(self.current_token, (tuple, list)) and len(self.current_token) > 2:
                for i in range(2, len(self.current_token)):
                    if isinstance(self.current_token[i], int):
                        return self.current_token[i]
        return 0
    
    def advance(self):
        """移动到下一个token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None
    
    def expect(self, expected_type: str, expected_value: str = None):
        """检查当前token是否符合预期"""
        if not self.current_token:
            self.error(f"期望 {expected_type}，但已到达文件末尾")
        
        token_type, token_value = self.current_token[0], self.current_token[1]
        
        if token_type != expected_type:
            self.error(f"期望 {expected_type}，但得到 {token_type}")
        
        if expected_value and token_value != expected_value:
            self.error(f"期望 '{expected_value}'，但得到 '{token_value}'")
        
        self.advance()
    
    def check(self, token_type: str, token_value: str = None) -> bool:
        """检查当前token是否匹配（不移动）"""
        if not self.current_token:
            return False
        
        t_type, t_value = self.current_token[0], self.current_token[1]
        
        if token_value:
            return t_type == token_type and t_value == token_value
        return t_type == token_type
    
    # -------------------- 语法分析与四元式生成 --------------------
    
    def analyze(self) -> List[Quadruple]:
        """程序入口：program -> block '.'"""
        try:
            self.block()
            
            # 期望程序以 '.' 结束
            if not self.check('SYMBOL', '.'):
                self.error("程序必须以 '.' 结束")
            
            # 生成程序结束标记
            self.emit("END", "-", "-", "-")
            
            return self.quadruples
        
        except SemanticError as e:
            print(f"编译失败: {e}")
            raise
    
    def block(self):
        """block -> [const_decl] [var_decl] [proc_decl] statement"""
        
        # 1. 常量声明
        if self.check('CONST'):
            self.const_declaration()
        
        # 2. 变量声明
        if self.check('VAR'):
            self.var_declaration()
        
        # 3. 过程声明
        while self.check('PROCEDURE'):
            self.procedure_declaration()
        
        # 4. 语句
        self.statement()
    
    def const_declaration(self):
        """const_decl -> 'const' const_def {',' const_def} ';'"""
        self.expect('CONST')
        
        while True:
            if not self.check('ID'):
                self.error("常量声明中期望标识符")
            
            const_name = self.current_token[1]
            self.advance()
            
            if not self.check('SYMBOL', '='):
                self.error("常量声明中期望 '='")
            self.advance()
            
            if not self.check('NUMBER'):
                self.error("常量声明中期望数字")
            
            const_value = int(self.current_token[1])
            self.advance()
            
            # 在符号表中定义常量
            self.symbol_table.define_const(const_name, const_value)
            
            # 检查是否有更多常量定义
            if self.check('SYMBOL', ','):
                self.advance()
            else:
                break
        
        self.expect('SYMBOL', ';')
    
    def var_declaration(self):
        """var_decl -> 'var' ID {',' ID} ';'"""
        self.expect('VAR')
        
        while True:
            if not self.check('ID'):
                self.error("变量声明中期望标识符")
            
            var_name = self.current_token[1]
            self.advance()
            
            # 在符号表中定义变量
            self.symbol_table.define_var(var_name)
            
            # 检查是否有更多变量定义
            if self.check('SYMBOL', ','):
                self.advance()
            else:
                break
        
        self.expect('SYMBOL', ';')
    
    def procedure_declaration(self):
        """proc_decl -> 'procedure' ID ';' block ';'"""
        self.expect('PROCEDURE')
        
        if not self.check('ID'):
            self.error("过程声明中期望标识符")
        
        proc_name = self.current_token[1]
        self.advance()
        
        self.expect('SYMBOL', ';')
        
        # 记录过程入口
        proc_entry = len(self.quadruples)
        
        # 生成过程入口标记
        proc_label = self.new_label()
        self.emit("PROC", proc_name, "-", proc_label)
        
        # 进入新的作用域
        self.symbol_table.enter_scope()
        
        # 在外层符号表中定义过程
        saved_level = self.symbol_table.level
        self.symbol_table.level -= 1
        self.symbol_table.define_procedure(proc_name, proc_entry)
        self.symbol_table.level = saved_level
        
        # 解析过程体
        self.block()
        
        # 生成返回指令
        self.emit("RET", "-", "-", "-")
        
        # 退出作用域
        self.symbol_table.exit_scope()
        
        self.expect('SYMBOL', ';')
    
    def statement(self):
        """statement -> assignment | call | begin_end | if | while | read | write | empty"""
        
        if self.check('ID'):
            # 赋值语句
            self.assignment()
        
        elif self.check('CALL'):
            # 调用语句
            self.call_statement()
        
        elif self.check('BEGIN'):
            # 复合语句
            self.begin_end()
        
        elif self.check('IF'):
            # 条件语句
            self.if_statement()
        
        elif self.check('WHILE'):
            # 循环语句
            self.while_statement()
        
        elif self.check('READ'):
            # 读语句
            self.read_statement()
        
        elif self.check('WRITE'):
            # 写语句
            self.write_statement()
        
        # else: 空语句
    
    def assignment(self):
        """assignment -> ID ':=' expression"""
        
        if not self.check('ID'):
            self.error("赋值语句期望标识符")
        
        var_name = self.current_token[1]
        self.advance()
        
        # 查找变量
        symbol = self.symbol_table.lookup(var_name)
        if not symbol:
            self.error(f"未定义的标识符 '{var_name}'")
        
        if symbol.type != SymbolType.VAR:
            self.error(f"'{var_name}' 不是变量，不能赋值")
        
        self.expect('ASSIGN')
        
        # 计算表达式的值
        result = self.expression()
        
        # 生成赋值四元式: (=, result, -, var_name)
        self.emit("=", result, "-", var_name)
    
    def call_statement(self):
        """call_stmt -> 'call' ID"""
        self.expect('CALL')
        
        if not self.check('ID'):
            self.error("call 语句期望过程名")
        
        proc_name = self.current_token[1]
        self.advance()
        
        # 查找过程
        symbol = self.symbol_table.lookup(proc_name)
        if not symbol:
            self.error(f"未定义的过程 '{proc_name}'")
        
        if symbol.type != SymbolType.PROCEDURE:
            self.error(f"'{proc_name}' 不是过程")
        
        # 生成调用四元式: (CALL, proc_name, -, -)
        self.emit("CALL", proc_name, "-", "-")
    
    def begin_end(self):
        """begin_end -> 'begin' statement {';' statement} 'end'"""
        self.expect('BEGIN')
        
        self.statement()
        
        while self.check('SYMBOL', ';'):
            self.advance()
            self.statement()
        
        self.expect('END')
    
    def if_statement(self):
        """if_stmt -> 'if' condition 'then' statement"""
        self.expect('IF')
        
        # 计算条件
        cond_result = self.condition()
        
        self.expect('THEN')
        
        # 生成条件跳转: (JZ, cond_result, -, ?)
        jz_index = self.emit("JZ", cond_result, "-", "?")
        
        # 解析then部分的语句
        self.statement()
        
        # 回填跳转地址
        next_label = str(len(self.quadruples))
        self.backpatch(jz_index, next_label)
    
    def while_statement(self):
        """while_stmt -> 'while' condition 'do' statement"""
        self.expect('WHILE')
        
        # 记录循环开始位置
        loop_start = len(self.quadruples)
        
        # 计算条件
        cond_result = self.condition()
        
        self.expect('DO')
        
        # 生成条件跳转: (JZ, cond_result, -, ?)
        jz_index = self.emit("JZ", cond_result, "-", "?")
        
        # 解析循环体
        self.statement()
        
        # 生成无条件跳转回循环开始: (JMP, -, -, loop_start)
        self.emit("JMP", "-", "-", str(loop_start))
        
        # 回填跳转地址
        next_label = str(len(self.quadruples))
        self.backpatch(jz_index, next_label)
    
    def read_statement(self):
        """read_stmt -> 'read' '(' ID ')'"""
        self.expect('READ')
        self.expect('SYMBOL', '(')
        
        if not self.check('ID'):
            self.error("read 语句期望变量名")
        
        var_name = self.current_token[1]
        self.advance()
        
        # 查找变量
        symbol = self.symbol_table.lookup(var_name)
        if not symbol:
            self.error(f"未定义的变量 '{var_name}'")
        
        if symbol.type != SymbolType.VAR:
            self.error(f"'{var_name}' 不是变量")
        
        self.expect('SYMBOL', ')')
        
        # 生成读四元式: (READ, -, -, var_name)
        self.emit("READ", "-", "-", var_name)
    
    def write_statement(self):
        """write_stmt -> 'write' '(' expression ')'"""
        self.expect('WRITE')
        self.expect('SYMBOL', '(')
        
        # 计算表达式
        result = self.expression()
        
        self.expect('SYMBOL', ')')
        
        # 生成写四元式: (WRITE, result, -, -)
        self.emit("WRITE", result, "-", "-")
    
    def condition(self) -> str:
        """condition -> 'odd' expression | expression relop expression"""
        
        if self.check('ODD'):
            self.advance()
            expr_result = self.expression()
            
            # 生成 ODD 运算: (ODD, expr_result, -, temp)
            temp = self.new_temp()
            self.emit("ODD", expr_result, "-", temp)
            return temp
        else:
            left = self.expression()
            
            # 关系运算符
            if not self.current_token:
                self.error("条件表达式期望关系运算符")
            
            token_type, token_value = self.current_token[0], self.current_token[1]
            
            relop = None
            if token_type == 'SYMBOL':
                if token_value in ['=', '#', '<', '>', '<=', '>=']:
                    relop = token_value
            
            if not relop:
                self.error(f"期望关系运算符，但得到 {token_value}")
            
            self.advance()
            
            right = self.expression()
            
            # 生成关系运算四元式: (relop, left, right, temp)
            temp = self.new_temp()
            self.emit(relop, left, right, temp)
            return temp
    
    def expression(self) -> str:
        """expression -> ['+' | '-'] term {('+' | '-') term}"""
        
        # 处理正负号
        sign = None
        if self.check('SYMBOL', '+'):
            sign = '+'
            self.advance()
        elif self.check('SYMBOL', '-'):
            sign = '-'
            self.advance()
        
        result = self.term()
        
        # 如果有负号，生成取负运算
        if sign == '-':
            temp = self.new_temp()
            self.emit("NEG", result, "-", temp)
            result = temp
        
        # 处理加减运算
        while self.current_token and self.check('SYMBOL'):
            token_value = self.current_token[1]
            if token_value == '+':
                self.advance()
                right = self.term()
                temp = self.new_temp()
                self.emit("+", result, right, temp)
                result = temp
            elif token_value == '-':
                self.advance()
                right = self.term()
                temp = self.new_temp()
                self.emit("-", result, right, temp)
                result = temp
            else:
                break
        
        return result
    
    def term(self) -> str:
        """term -> factor {('*' | '/') factor}"""
        
        result = self.factor()
        
        # 处理乘除运算
        while self.current_token and self.check('SYMBOL'):
            token_value = self.current_token[1]
            if token_value == '*':
                self.advance()
                right = self.factor()
                temp = self.new_temp()
                self.emit("*", result, right, temp)
                result = temp
            elif token_value == '/':
                self.advance()
                right = self.factor()
                temp = self.new_temp()
                self.emit("/", result, right, temp)
                result = temp
            else:
                break
        
        return result
    
    def factor(self) -> str:
        """factor -> ID | NUMBER | '(' expression ')'"""
        
        if self.check('ID'):
            # 标识符
            name = self.current_token[1]
            self.advance()
            
            symbol = self.symbol_table.lookup(name)
            if not symbol:
                self.error(f"未定义的标识符 '{name}'")
            
            if symbol.type == SymbolType.CONST:
                # 常量：返回常量值
                return str(symbol.value)
            elif symbol.type == SymbolType.VAR:
                # 变量：返回变量名
                return name
            else:
                self.error(f"'{name}' 不能用于表达式中")
        
        elif self.check('NUMBER'):
            # 数字常量
            value = self.current_token[1]
            self.advance()
            return value
        
        elif self.check('SYMBOL', '('):
            # 括号表达式
            self.advance()
            result = self.expression()
            self.expect('SYMBOL', ')')
            return result
        
        else:
            self.error("表达式中期望标识符、数字或 '('")
    
    def print_quadruples(self):
        """打印四元式"""
        print("\n四元式序列:")
        print(f"{'序号':<6} {'操作符':<10} {'参数1':<10} {'参数2':<10} {'结果'}")
        print("-" * 50)
        for i, quad in enumerate(self.quadruples):
            print(quad.to_string(i))

# ==========================================
# 5. 测试代码
# ==========================================

if __name__ == '__main__':
    from pl0_lexer import Lexer
    
    # 测试代码1：简单的变量赋值和输出
    test_code1 = """
    var x, y;
    begin
        x := 10;
        y := 20;
        write(x + y)
    end.
    """
    
    print("=" * 60)
    print("测试1: 简单赋值和输出")
    print("=" * 60)
    lexer = Lexer(test_code1)
    tokens = lexer.get_tokens()
    
    analyzer = SemanticAnalyzer(tokens)
    quadruples = analyzer.analyze()
    
    analyzer.symbol_table.print_table()
    analyzer.print_quadruples()
    
    # 测试代码2：带常量和条件语句
    test_code2 = """
    const max = 100;
    var x, y;
    begin
        x := 50;
        y := 30;
        if x < max then
            write(x + y)
    end.
    """
    
    print("\n\n" + "=" * 60)
    print("测试2: 常量和条件语句")
    print("=" * 60)
    lexer2 = Lexer(test_code2)
    tokens2 = lexer2.get_tokens()
    
    analyzer2 = SemanticAnalyzer(tokens2)
    quadruples2 = analyzer2.analyze()
    
    analyzer2.symbol_table.print_table()
    analyzer2.print_quadruples()
    
    # 测试代码3：循环语句
    test_code3 = """
    var n, sum;
    begin
        n := 5;
        sum := 0;
        while n > 0 do
        begin
            sum := sum + n;
            n := n - 1
        end;
        write(sum)
    end.
    """
    
    print("\n\n" + "=" * 60)
    print("测试3: 循环语句")
    print("=" * 60)
    lexer3 = Lexer(test_code3)
    tokens3 = lexer3.get_tokens()
    
    analyzer3 = SemanticAnalyzer(tokens3)
    quadruples3 = analyzer3.analyze()
    
    analyzer3.symbol_table.print_table()
    analyzer3.print_quadruples()
