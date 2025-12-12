from enum import Enum, auto

# P-Code 指令类型
class OpCode(Enum):
    LIT = "LIT" # Load Constant: 将常量放入栈顶
    OPR = "OPR" # Operation: 执行算术或逻辑运算
    LOD = "LOD" # Load Variable: 将变量值放入栈顶
    STO = "STO" # Store Variable: 将栈顶值存入变量
    CAL = "CAL" # Call Procedure: 调用过程
    INT = "INT" # Increment: 在栈中分配空间
    JMP = "JMP" # Jump: 无条件跳转
    JPC = "JPC" # Jump Conditional: 条件跳转 (栈顶为0跳转)
    RED = "RED" # Read: 读入输入
    WRT = "WRT" # Write: 输出栈顶

# 运算符映射
OPR_MAP = {
    '+': 2, '-': 3, '*': 4, '/': 5,
    'odd': 6, '=': 8, '#': 9, '<': 10, '>': 12, '<=': 13, '>=': 11
}

class Instruction:
    def __init__(self, f, l, a):
        self.f = f  # Function code (OpCode)
        self.l = l  # Level difference (层差)
        self.a = a  # Address/Value (位移或数值)

    def __repr__(self):
        return f"{self.f.value}\t{self.l}\t{self.a}"