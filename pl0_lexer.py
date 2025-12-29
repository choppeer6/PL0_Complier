import re
from typing import List, NamedTuple

# ==========================================
# 1. 配置与常量定义
# ==========================================

# PL/0 虚拟机通常基于栈，限制整数为 32 位有符号整数
MAX_INT = 2147483647 

class Token(NamedTuple):
    type: str       # Token 类型 (如 BEGIN, ID, NUMBER)
    value: str      # Token 的实际文本值
    line: int       # 行号
    column: int     # 列号

# 关键字集合 (全部大写，用于忽略大小写匹配)
KEYWORDS = {
    'BEGIN', 'CALL', 'CONST', 'DO', 'END', 'IF', 'ODD',
    'PROCEDURE', 'READ', 'THEN', 'VAR', 'WHILE', 'WRITE'
}

# ==========================================
# 2. 词法分析器核心类
# ==========================================

class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.tokens: List[Token] = []
        self.errors: List[str] = []  # 存储词法错误信息
        self.regex = self._compile_regex()
        
    def _compile_regex(self):
        """编译正则表达式规则，注意顺序很重要"""
        token_spec = [
            ('COMMENT',  r'\(\*.*?\*\)'),   # 注释 (* ... *)，非贪婪匹配
            ('ASSIGN',   r':='),            # 赋值符号 := (必须在冒号前)
            ('LE',       r'<='),            # 小于等于 <= (必须在小于号前)
            ('GE',       r'>='),            # 大于等于 >= (必须在大于号前)
            ('NUMBER',   r'\d+'),           # 数字
            ('ID',       r'[A-Za-z][A-Za-z0-9]*'), # 标识符
            ('NEWLINE',  r'\n'),            # 换行符
            ('SKIP',     r'[ \t\r]+'),      # 空白符(空格、制表符)
            ('PLUS',     r'\+'),            # 加号
            ('MINUS',    r'-'),             # 减号
            ('TIMES',    r'\*'),            # 乘号
            ('SLASH',    r'/'),             # 除号
            ('LPAREN',   r'\('),            # 左括号
            ('RPAREN',   r'\)'),            # 右括号
            ('EQ',       r'='),             # 等号
            ('NE',       r'#'),             # 不等于
            ('LT',       r'<'),             # 小于
            ('GT',       r'>'),             # 大于
            ('COMMA',    r','),             # 逗号
            ('PERIOD',   r'\.'),            # 句号
            ('SEMICOLON', r';'),            # 分号
            ('MISMATCH', r'.'),             # 兜底匹配：任何未被识别的字符
        ]
        # 使用 DOTALL 模式以便 . 能匹配换行(主要用于多行注释)
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
        return re.compile(tok_regex, re.DOTALL)

    def tokenize(self):
        """执行词法分析，生成详细的 Token 对象列表"""
        self.tokens = []
        self.errors = [] 
        line_num = 1
        line_start = 0

        for mo in self.regex.finditer(self.source):
            kind = mo.lastgroup
            value = mo.group()
            # 计算列号：当前位置 - 当前行起始位置 + 1
            column = mo.start() - line_start + 1

            if kind == 'SKIP':
                continue
            elif kind == 'NEWLINE':
                line_num += 1
                line_start = mo.end()
                continue
            elif kind == 'COMMENT':
                # 处理跨行注释，需要更新行号
                newlines = value.count('\n')
                if newlines > 0:
                    line_num += newlines
                    line_start = mo.end() - (len(value) - value.rfind('\n') - 1)
                continue

            elif kind == 'NUMBER':
                # 数值溢出检查
                try:
                    num_val = int(value)
                    if num_val > MAX_INT:
                        self._record_error(f"数值溢出: '{value}' 超过最大值 {MAX_INT}", line_num, column)
                except ValueError:
                    self._record_error(f"无效数字: {value}", line_num, column)

            elif kind == 'ID':
                # 检查是否为关键字
                upper_value = value.upper()
                if upper_value in KEYWORDS:
                    kind = upper_value

            elif kind == 'MISMATCH':
                # 记录错误但不崩溃，跳过该字符
                self._record_error(f"非法字符: '{value}'", line_num, column)
                continue

            token = Token(kind, value, line_num, column)
            self.tokens.append(token)

        return self.tokens

    def _record_error(self, msg: str, line: int, col: int):
        self.errors.append(f"[词法错误] 第 {line} 行, 第 {col} 列: {msg}")

    def has_error(self) -> bool:
        return len(self.errors) > 0

    def get_tokens(self):
        """
        返回 Parser 需要的格式。
        格式: [(类型, 值, 行号), ...]
        这是为了让语法分析器在报错时能获取行号。
        """
        if not self.tokens:
            self.tokenize()

        mapped = []
        for t in self.tokens:
            # 1. 关键字、标识符、赋值号、数字保持原类型
            if t.type in ('ASSIGN', 'NUMBER', 'ID') or t.type in KEYWORDS:
                mapped.append((t.type, t.value, t.line))
            # 2. 运算符和界符，为了配合 Parser 逻辑，可以保留原值或转为 SYMBOL
            else:
                if t.type in ('LE', 'GE'):
                    symval = '<=' if t.type == 'LE' else '>='
                    mapped.append(('SYMBOL', symval, t.line))
                elif t.type in ('EQ', 'NE', 'LT', 'GT', 'PLUS', 'MINUS', 'TIMES', 'SLASH', 
                                'LPAREN', 'RPAREN', 'COMMA', 'PERIOD', 'SEMICOLON'):
                    mapped.append(('SYMBOL', t.value, t.line))
                else:
                    mapped.append((t.type, t.value, t.line))

        return mapped