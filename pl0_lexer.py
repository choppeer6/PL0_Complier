import re
from typing import List, NamedTuple, Optional

# ==========================================
# 1. 配置与定义
# ==========================================

# PL/0 虚拟机通常基于栈，限制整数为 32 位有符号整数
MAX_INT = 2147483647  # 2^31 - 1

class Token(NamedTuple):
    type: str       # Token 类型
    value: str      # Token 值
    line: int       # 行号
    column: int     # 列号

KEYWORDS = {
    'BEGIN', 'CALL', 'CONST', 'DO', 'END', 'IF', 'ODD',
    'PROCEDURE', 'READ', 'THEN', 'VAR', 'WHILE', 'WRITE'
}

# ==========================================
# 2. 增强版 Lexer 类
# ==========================================

class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.tokens: List[Token] = []
        self.errors: List[str] = []  # 【新功能】用于存储错误列表
        self.regex = self._compile_regex()
        
    def _compile_regex(self):
        token_spec = [
            ('COMMENT',  r'\(\*.*?\*\)'),   # 注释 (* ... *)
            ('ASSIGN',   r':='),            # :=
            ('LE',       r'<='),            # <=
            ('GE',       r'>='),            # >=
            ('NUMBER',   r'\d+'),           # 数字
            ('ID',       r'[A-Za-z][A-Za-z0-9]*'), # 标识符
            ('NEWLINE',  r'\n'),            # 换行
            ('SKIP',     r'[ \t\r]+'),      # 空白
            ('PLUS',     r'\+'),
            ('MINUS',    r'-'),
            ('TIMES',    r'\*'),
            ('SLASH',    r'/'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('EQ',       r'='),
            ('NE',       r'#'), 
            ('LT',       r'<'),
            ('GT',       r'>'),
            ('COMMA',    r','),
            ('PERIOD',   r'\.'),
            ('SEMICOLON', r';'),
            ('MISMATCH', r'.'),             # 非法字符
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
        return re.compile(tok_regex, re.DOTALL)

    def tokenize(self):
        """执行词法分析"""
        self.tokens = []
        self.errors = [] # 每次重新分析时清空错误
        line_num = 1
        line_start = 0

        for mo in self.regex.finditer(self.source):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start + 1

            # --- 处理跳过和换行 ---
            if kind == 'SKIP':
                continue
            elif kind == 'NEWLINE':
                line_num += 1
                line_start = mo.end()
                continue
            elif kind == 'COMMENT':
                newlines = value.count('\n')
                if newlines > 0:
                    line_num += newlines
                    line_start = mo.end() - (len(value) - value.rfind('\n') - 1)
                continue

            # --- 【新功能 #4】数值检查 ---
            elif kind == 'NUMBER':
                # 虽然是数字，但需要检查是否溢出
                try:
                    num_val = int(value)
                    if num_val > MAX_INT:
                        self._record_error(f"Number overflow: '{value}' exceeds {MAX_INT}", line_num, column)
                        # 即使溢出，我们通常还是生成 Token，
                        # 这样语法分析器(Parser)不会因为缺 Token 而报错，后续语义分析再拦截即可。
                except ValueError:
                    self._record_error(f"Invalid number format: {value}", line_num, column)

            # --- 关键字处理 ---
            elif kind == 'ID':
                upper_value = value.upper()
                if upper_value in KEYWORDS:
                    kind = upper_value

            # --- 【新功能 #2】错误恢复 ---
            elif kind == 'MISMATCH':
                # 记录错误，但不抛出异常，也不中断循环
                self._record_error(f"Unexpected character: '{value}'", line_num, column)
                # 直接 continue，跳过这个字符，不生成 Token
                continue

            # 生成并添加 Token
            token = Token(kind, value, line_num, column)
            self.tokens.append(token)

        return self.tokens

    def _record_error(self, msg: str, line: int, col: int):
        """辅助方法：格式化错误信息"""
        error_msg = f"[Error] Line {line}, Column {col}: {msg}"
        self.errors.append(error_msg)

    def has_error(self) -> bool:
        return len(self.errors) > 0

    def print_errors(self):
        if not self.errors:
            print("No lexical errors found.")
        else:
            print(f"Found {len(self.errors)} errors:")
            for err in self.errors:
                print(err)

    def get_tokens(self):
        """返回 Parser 期望的 (sym, val) 对。
        Parser 旧实现期望大多数标点/运算符使用通用的 'SYMBOL' 类型，
        并用 value 保存实际字符（例如 ',' ';' '(' ')' '<=' '>=' 等）。
        这个方法会在需要时调用 tokenize() 生成 tokens，然后做一次映射。
        """
        if not self.tokens:
            self.tokenize()

        mapped = []
        for t in self.tokens:
            # 关键字已经被转换为大写类型（如 'VAR', 'BEGIN' 等）
            if t.type in ('ASSIGN', 'NUMBER'):
                # ASSIGN 和 NUMBER 在 Parser 中有专门类型
                mapped.append((t.type, t.value))
            elif t.type == 'ID' or t.type in KEYWORDS:
                mapped.append((t.type, t.value))
            else:
                # 将所有运算符/界符统一为 SYMBOL，保留原始字符作为 value
                if t.type in ('LE', 'GE'):
                    # <=, >=
                    symval = '<=' if t.type == 'LE' else '>='
                    mapped.append(('SYMBOL', symval))
                elif t.type in ('EQ', 'NE', 'LT', 'GT', 'PLUS', 'MINUS', 'TIMES', 'SLASH', 'LPAREN', 'RPAREN', 'COMMA', 'PERIOD', 'SEMICOLON'):
                    mapped.append(('SYMBOL', t.value))
                else:
                    # 保留原样作为后备（便于调试和向后兼容）
                    mapped.append((t.type, t.value))

        return mapped

# ==========================================
# 3. 验证与测试
# ==========================================

if __name__ == '__main__':
    # 构造一个包含错误的测试用例：
    # 1. 正常的赋值
    # 2. 一个溢出的大整数 (99999999999)
    # 3. 几个非法字符 (&, @)
    # 4. 正常的结束符
    bad_code = """
    var x, y;
    begin
        x := 99999999999;  (* 错误1：数值溢出 *)
        y := x + & @ 5;    (* 错误2：非法字符 & 和 @ *)
    end.
    """

    print("=== 开始词法分析 ===")
    lexer = Lexer(bad_code)
    tokens = lexer.tokenize()

    # 1. 输出生成的 Token (证明即使有错，分析器也跑完了)
    print("\n[Generated Tokens]")
    print(f"{'LINE':<5} {'TYPE':<15} {'VALUE'}")
    print("-" * 30)
    for token in tokens:
        print(f"{token.line:<5} {token.type:<15} {token.value}")

    # 2. 输出错误报告
    print("\n[Error Report]")
    lexer.print_errors()
    
    if lexer.has_error():
        print("\nResult: Compilation failed due to lexical errors.")
    else:
        print("\nResult: Success.")