# PL/0 语义分析与中间代码生成

## 📚 概述

本模块实现了 PL/0 编译器的语义分析和中间代码生成功能，包括：

1. **符号表管理** - 管理常量、变量、过程的定义和作用域
2. **语义检查** - 类型检查、作用域检查、声明检查
3. **中间代码生成** - 生成基于栈的 P-Code 指令

## 🏗️ 架构设计

### 1. 符号表设计

#### 符号类型 (SymbolType)

```python
class SymbolType(Enum):
    CONST = "CONST"      # 常量
    VAR = "VAR"          # 变量
    PROCEDURE = "PROC"   # 过程
```

#### 符号表项 (Symbol)

每个符号包含以下信息：

- `name`: 符号名称
- `type`: 符号类型（常量/变量/过程）
- `level`: 所在层次（嵌套深度）
- `value`: 常量值（仅对常量有效）
- `address`: 地址/偏移量
- `size`: 过程需要的数据空间大小

#### 符号表管理器 (SymbolTable)

**主要功能：**

- `enter_scope()` - 进入新的作用域
- `exit_scope()` - 退出当前作用域
- `define_const(name, value)` - 定义常量
- `define_var(name)` - 定义变量
- `define_procedure(name, entry)` - 定义过程
- `lookup(name)` - 查找符号（从内向外）

**作用域管理：**

- 使用层次号 (level) 表示嵌套深度
- 主程序层次为 0，每进入一个过程层次 +1
- 退出作用域时删除当前层次的所有符号

**地址分配：**

- 每个层次维护独立的地址计数器
- 地址从 3 开始（预留 SL、DL、RA）
- 变量按声明顺序依次分配地址

### 2. 递归下降语法分析器

采用递归下降分析法，每个非终结符对应一个解析函数：

```
program          -> block '.'
block            -> [const_decl] [var_decl] [proc_decl] statement
const_decl       -> 'const' const_def {',' const_def} ';'
var_decl         -> 'var' ID {',' ID} ';'
proc_decl        -> 'procedure' ID ';' block ';'
statement        -> assignment | call | begin_end | if | while | read | write | empty
assignment       -> ID ':=' expression
call             -> 'call' ID
begin_end        -> 'begin' statement {';' statement} 'end'
if               -> 'if' condition 'then' statement
while            -> 'while' condition 'do' statement
read             -> 'read' '(' ID ')'
write            -> 'write' '(' expression ')'
condition        -> 'odd' expression | expression relop expression
expression       -> ['+' | '-'] term {('+' | '-') term}
term             -> factor {('*' | '/') factor}
factor           -> ID | NUMBER | '(' expression ')'
```

### 3. P-Code 指令集

| 指令 | 格式 | 说明 |
|------|------|------|
| LIT | LIT 0 a | 将常量 a 压入栈顶 |
| LOD | LOD l a | 将层差为 l、地址为 a 的变量值压入栈顶 |
| STO | STO l a | 将栈顶值存入层差为 l、地址为 a 的变量 |
| CAL | CAL l a | 调用层差为 l、入口地址为 a 的过程 |
| INT | INT 0 a | 在栈中分配 a 个单元的空间 |
| JMP | JMP 0 a | 无条件跳转到地址 a |
| JPC | JPC 0 a | 条件跳转：栈顶为 0 时跳转到地址 a |
| RED | RED 0 0 | 读取输入并压入栈顶 |
| WRT | WRT 0 0 | 输出栈顶值 |
| OPR | OPR 0 a | 执行运算，a 为运算码 |

**OPR 运算码：**

| a | 运算 | 说明 |
|---|------|------|
| 0 | RET | 过程返回 |
| 1 | NEG | 取负 |
| 2 | ADD | 加法 |
| 3 | SUB | 减法 |
| 4 | MUL | 乘法 |
| 5 | DIV | 除法 |
| 6 | ODD | 奇偶判断 |
| 8 | EQ | 等于 |
| 9 | NE | 不等于 |
| 10 | LT | 小于 |
| 11 | GE | 大于等于 |
| 12 | GT | 大于 |
| 13 | LE | 小于等于 |

## 🔍 语义检查

### 1. 声明检查

- 变量/常量/过程使用前必须先声明
- 同一作用域内不能重复声明

```python
symbol = self.symbol_table.lookup(name)
if not symbol:
    self.error(f"未定义的标识符 '{name}'")
```

### 2. 类型检查

- 常量不能被赋值
- 过程不能用于表达式
- 赋值语句左边必须是变量

```python
if symbol.type != SymbolType.VAR:
    self.error(f"'{name}' 不是变量，不能赋值")
```

### 3. 作用域检查

- 使用层差 (level difference) 访问不同层次的变量
- 内层可以访问外层的变量和常量
- 外层不能访问内层的变量

```python
level_diff = self.symbol_table.level - symbol.level
self.emit(OpCode.LOD, level_diff, symbol.address)
```

## 💻 代码生成示例

### 示例 1: 简单赋值

**源代码：**
```
var x;
begin
    x := 10;
    write(x)
end.
```

**生成的 P-Code：**
```
0   JMP  0  1      # 跳过变量声明区
1   INT  0  4      # 分配空间（3个基本单元 + 1个变量）
2   LIT  0  10     # 将常量 10 压栈
3   STO  0  3      # 存入变量 x（地址 3）
4   LOD  0  3      # 加载变量 x
5   WRT  0  0      # 输出
6   OPR  0  0      # 返回
```

### 示例 2: 条件语句

**源代码：**
```
var x, y;
begin
    x := 15;
    y := 10;
    if x > y then
        write(x)
end.
```

**生成的 P-Code：**
```
0   JMP  0  1      # 跳过变量声明区
1   INT  0  5      # 分配空间（3 + 2个变量）
2   LIT  0  15     # x := 15
3   STO  0  3
4   LIT  0  10     # y := 10
5   STO  0  4
6   LOD  0  3      # 加载 x
7   LOD  0  4      # 加载 y
8   OPR  0  12     # 比较 x > y
9   JPC  0  12     # 如果为假，跳转到 12
10  LOD  0  3      # 加载 x
11  WRT  0  0      # 输出 x
12  OPR  0  0      # 返回
```

### 示例 3: 循环语句

**源代码：**
```
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
```

**生成的 P-Code：**
```
0   JMP  0  1      # 跳过变量声明区
1   INT  0  5      # 分配空间
2   LIT  0  5      # n := 5
3   STO  0  3
4   LIT  0  0      # sum := 0
5   STO  0  4
6   LOD  0  3      # 循环开始：加载 n
7   LIT  0  0      # 加载 0
8   OPR  0  12     # 比较 n > 0
9   JPC  0  19     # 如果为假，跳出循环
10  LOD  0  4      # sum := sum + n
11  LOD  0  3
12  OPR  0  2
13  STO  0  4
14  LOD  0  3      # n := n - 1
15  LIT  0  1
16  OPR  0  3
17  STO  0  3
18  JMP  0  6      # 跳回循环开始
19  LOD  0  4      # 加载 sum
20  WRT  0  0      # 输出
21  OPR  0  0      # 返回
```

### 示例 4: 过程调用

**源代码：**
```
var x;

procedure inc;
begin
    x := x + 1
end;

begin
    x := 10;
    call inc;
    call inc;
    write(x)
end.
```

**生成的 P-Code：**
```
0   JMP  0  8      # 跳过过程定义
1   JMP  0  2      # 过程 inc 的跳转
2   INT  0  3      # 过程体：分配空间
3   LOD  1  3      # 加载外层的 x（层差为1）
4   LIT  0  1
5   OPR  0  2
6   STO  1  3      # 存入外层的 x
7   OPR  0  0      # 返回
8   INT  0  4      # 主程序：分配空间
9   LIT  0  10     # x := 10
10  STO  0  3
11  CAL  0  1      # 调用 inc
12  CAL  0  1      # 再次调用 inc
13  LOD  0  3      # 加载 x
14  WRT  0  0      # 输出
15  OPR  0  0      # 返回
```

## 🎯 关键技术点

### 1. 回填技术

在生成跳转指令时，目标地址可能还未确定，需要先生成占位指令，后续回填：

```python
# 生成条件跳转指令（占位）
jpc_addr = len(self.code)
self.emit(OpCode.JPC, 0, 0)

# ... 生成 then 部分的代码 ...

# 回填跳转地址
self.code[jpc_addr].a = len(self.code)
```

### 2. 层次访问

使用层差 (level difference) 实现嵌套作用域的变量访问：

```python
level_diff = self.symbol_table.level - symbol.level
self.emit(OpCode.LOD, level_diff, symbol.address)
```

### 3. 栈帧结构

每个过程调用创建新的栈帧，包含：

- **SL (Static Link)**: 静态链，指向定义该过程的外层栈帧
- **DL (Dynamic Link)**: 动态链，指向调用者的栈帧
- **RA (Return Address)**: 返回地址

### 4. 表达式求值

采用后缀表达式的方式生成代码：

```python
# 对于表达式 a + b
self.factor()  # 生成 a 的代码（结果在栈顶）
self.factor()  # 生成 b 的代码（结果在栈顶）
self.emit(OpCode.OPR, 0, 2)  # 执行加法
```

## 🧪 测试用例

测试文件 `test_semantic.py` 包含 12 个测试用例：

1. ✅ 简单算术运算
2. ✅ 常量定义
3. ✅ 条件语句
4. ✅ 循环语句 - 求和
5. ✅ ODD 函数测试
6. ✅ 复杂表达式
7. ✅ 嵌套的复合语句
8. ✅ 过程调用
9. ✅ 嵌套过程
10. ✅ READ 语句
11. ✅ 关系运算符测试
12. ✅ 负数测试

运行测试：
```bash
python test_semantic.py
```

## 📖 使用方法

### 基本用法

```python
from pl0_lexer import Lexer
from pl0_semantic import Parser
from pl0_vm import VM

# 1. 词法分析
code = """
var x;
begin
    x := 10;
    write(x)
end.
"""

lexer = Lexer(code)
tokens = lexer.get_tokens()

# 2. 语义分析和代码生成
parser = Parser(tokens)
p_code = parser.parse()

# 3. 虚拟机执行
vm = VM(p_code)
result = vm.run()
print(result)
```

### 错误处理

```python
try:
    parser = Parser(tokens)
    p_code = parser.parse()
except SemanticError as e:
    print(f"语义错误: {e}")
```

## 🔧 扩展建议

### 1. 增强语义检查

- 添加常量表达式求值
- 检查除零错误
- 检查数值溢出

### 2. 优化代码生成

- 常量折叠
- 死代码消除
- 窥孔优化

### 3. 支持更多特性

- 数组类型
- 函数（带返回值）
- 更多数据类型（实数、字符串）

## 📚 参考资料

- 《编译原理》（龙书）- 第 2 版
- PL/0 语言规范
- 递归下降分析法
- 栈式虚拟机设计

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**: 2025-12-30

