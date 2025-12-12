import re

# Token 定义
KEYWORDS = {'begin', 'call', 'const', 'do', 'end', 'if', 'odd', 
            'procedure', 'read', 'then', 'var', 'while', 'write'}
SYMBOLS = {'+', '-', '*', '/', '(', ')', '=', ',', '.', '#', '<', '>', '<=', '>='}

class Lexer:
    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []
        self.pos = 0
        self.tokenize()

    def tokenize(self):
        # 简单的正则匹配
        token_spec = [
            ('NUMBER',   r'\d+'),           # Integer
            ('ASSIGN',   r':='),            # Assignment
            ('ID',       r'[A-Za-z]\w*'),   # Identifiers
            ('SKIP',     r'[ \t\n]+'),      # Skip over spaces
            ('SYMBOL',   r'[=<>#+\-*/(),.;]'), # Symbols
            ('MISMATCH', r'.'),             # Any other character
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
        
        for mo in re.finditer(tok_regex, self.source):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                continue
            elif kind == 'ID' and value in KEYWORDS:
                kind = value.upper()
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            self.tokens.append((kind, value))
    
    def get_tokens(self):
        return self.tokens