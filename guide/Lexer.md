# PL/0 词法分析器设计文档

## 1. 项目概述

本项目实现了一个健壮的 PL/0 语言词法分析器（Lexical Analyzer）。其主要职责是读取 PL/0 源代码字符流，过滤空白符与注释，识别并生成 Token 序列，同时进行初步的词法错误检测。

该分析器基于 Python 的 `re` 模块实现，采用 **DFA（确定有限自动机）** 思想进行正则匹配，并具备**错误恢复**与**精确定位**功能。

## 2. Token 定义规范

分析器将源代码划分为以下几类 Token，所有关键字均不区分大小写（内部统一转换为大写）。

### 2.1 关键字 (Keywords)

| **关键字**      | **说明** | **Token 类型**  |
| --------------- | -------- | --------------- |
| `begin`, `end`  | 块定义   | `BEGIN`, `END`  |
| `if`, `then`    | 条件分支 | `IF`, `THEN`    |
| `while`, `do`   | 循环控制 | `WHILE`, `DO`   |
| `const`, `var`  | 声明     | `CONST`, `VAR`  |
| `procedure`     | 过程声明 | `PROCEDURE`     |
| `call`          | 过程调用 | `CALL`          |
| `read`, `write` | 输入输出 | `READ`, `WRITE` |
| `odd`           | 奇偶判断 | `ODD`           |

### 2.2 运算符与界符 (Operators & Delimiters)

| **符号** | **Token 类型** | **符号** | **Token 类型**  |
| -------- | -------------- | -------- | --------------- |
| `+`      | `PLUS`         | `(`      | `LPAREN`        |
| `-`      | `MINUS`        | `)`      | `RPAREN`        |
| `*`      | `TIMES`        | `,`      | `COMMA`         |
| `/`      | `SLASH`        | `.`      | `PERIOD`        |
| `=`      | `EQ`           | `;`      | `SEMICOLON`     |
| `#`      | `NE` (不等于)  | `:=`     | `ASSIGN` (赋值) |
| `<`      | `LT`           | `<=`     | `LE` (小于等于) |
| `>`      | `GT`           | `>=`     | `GE` (大于等于) |

### 2.3 字面量 (Literals)

- **标识符 (`ID`)**: 以字母开头，后跟任意字母或数字。
- **数字 (`NUMBER`)**: 无符号整数序列。

## 3. 核心功能特性

### 3.1 精确的位置追踪 (Location Tracking)

每个生成的 Token 都包含以下元数据，便于后续语法分析器进行精确报错：

- **Line**: Token 所在的行号。
- **Column**: Token 所在的列号（处理了行首偏移）。

### 3.2 错误恢复机制 (Error Recovery)

采用 "Panic Mode" 的简化策略：

- 当遇到无法识别的字符（如 `&`, `$` 等）时，分析器**不会崩溃**。
- 系统会记录一个 `Unexpected character` 错误，并自动**跳过**该非法字符，继续尝试解析下一个字符。
- 这允许分析器一次运行即可报告源文件中的所有词法错误。

### 3.3 数值安全检查 (Value Safety)

- 内置数值范围检查，默认限制为 32 位有符号整数最大值 ($2^{31} - 1 = 2147483647$)。
- 当数字字面量超过此范围时，会生成溢出错误（Overflow Error），但在 Token 流中仍保留该数字（标记为 `NUMBER`），以防止语法分析阶段因 Token 缺失而产生级联错误。

### 3.4 注释处理

支持 PL/0 标准注释格式 `(* ... *)`。分析器会自动忽略注释内容，并正确处理**跨行注释**对行号计数的影响。

## 4. 接口说明

### 4.1 Token 结构

Python

```
class Token(NamedTuple):
    type: str       # Token 类型 (如 'ID', 'ASSIGN')
    value: str      # 原始文本值
    line: int       # 行号 (从1开始)
    column: int     # 列号 (从1开始)
```

### 4.2 API 使用示例

Python

```
from lexer import Lexer

source = "var x; begin x := 10; end."
lexer = Lexer(source)

# 执行分析
tokens = lexer.tokenize()

# 检查错误
if lexer.has_error():
    lexer.print_errors()
else:
    # 遍历结果
    for t in tokens:
        print(t)
```

## 5. 错误报告示例

假设输入代码如下（包含非法字符和数值溢出）：

Delphi

```
var n;
begin
    n := 99999999999; (* 溢出 *)
    n := n % 2;       (* 非法字符 % *)
end.
```

词法分析器将输出以下错误报告，明确指出错误发生的坐标：

Plaintext

```
[Error] Line 3, Column 10: Number overflow: '99999999999' exceeds 2147483647
[Error] Line 4, Column 12: Unexpected character: '%'
```