# 🛠️ PL/0 Compiler Online Visualization

这是一个基于 **Python** 实现的教学用 **PL/0 语言编译器**，配备了基于 **Streamlit** 的现代化 Web 前端界面。

本项目旨在通过可视化方式展示编译器工作的完整流程：从源代码词法分析，到语法分析生成 P-Code，最后在栈式虚拟机（Stack VM）上执行并输出结果。

## ✨ 功能特性

* **完整的编译管线**：
  * **词法分析 (Lexer)**：使用正则将源码转换为 Token 流。
  * **语法分析 (Parser)**：采用递归下降分析法，支持变量/常量声明、过程嵌套、控制流语句。
  * **代码生成 (Code Gen)**：生成基于栈式计算机的 P-Code (伪汇编指令)。
  * **虚拟机执行 (VM)**：模拟栈式计算机运行目标代码。
* **可视化 Web 界面**：
  * 基于 Streamlit 构建，无需繁琐配置。
  * **多视图展示**：Token 列表、汇编代码预览、控制台输出分栏显示。
  * **交互式调试**：提供目标代码 (.asm) 下载功能。
* **支持的 PL/0 语法**：
  * 数据类型：整型。
  * 控制流：`if...then`, `while...do`, `call` (过程调用)。
  * IO 操作：`read`, `write`。
  * 运算：四则运算及逻辑判断 (`odd`, `=`, `#`, `<`, `>`, `<=`, `>=`).

## 📂 项目结构

```text
.
├── app.py           # Streamlit 前端入口，处理 UI 布局和交互逻辑
├── pl0_lexer.py     # 词法分析器，负责 Token 提取
├── pl0_parser.py    # 语法分析器，负责语法检查与 P-Code 生成
├── pl0_vm.py        # 虚拟机，负责执行 P-Code 指令
└── pl0_types.py     # 类型定义 (OpCode 枚举, Instruction 类等)
```

## 🚀 快速开始

### 1. 环境准备

确保你的环境中已安装 Python 3.8+。

### 2. 安装依赖

本项目仅依赖 `streamlit`。

Bash

```
pip install streamlit
```

### 3. 运行系统

在项目根目录下运行以下命令：

Bash

```
PS D:\Program Files\github\PL0_Complier> .\.venv\Scripts\activate    //进入虚拟环境

streamlit run app.py

or

python -m streamlit run app.py
```

启动后，浏览器将自动打开 `http://localhost:8501`，你即可看到编译器界面。

## 📝 语法示例 (PL/0)

以下是一段标准的 PL/0 代码示例，计算两个数的和：

```
var x, y;
begin
  x := 10;
  y := 20;

  if x < y then
    write(x + y)
end.
```

### 更多语法规则

- **程序结束**：所有程序必须以 `.` 结尾。
- **声明**：
  - `const a = 10;`
  - `var x, y, z;`
  - `procedure p; begin ... end;`
- **赋值**：使用 `:=` (例如 `x := x + 1`)。
- **输入输出**：`read(x)` 读取输入到变量，`write(x)` 打印栈顶值。

## ⚙️ 虚拟机指令集 (P-Code)

本编译器生成的目标代码基于以下指令集：

| **指令** | **说明**                           | **示例**  |
| -------------- | ---------------------------------------- | --------------- |
| **LIT**  | Load Constant (将常量压入栈顶)           | `LIT 0 10`    |
| **LOD**  | Load Variable (将变量值压入栈顶)         | `LOD 0 3`     |
| **STO**  | Store Variable (将栈顶值存入变量)        | `STO 1 3`     |
| **CAL**  | Call Procedure (调用过程)                | `CAL 0 5`     |
| **INT**  | Increment (在栈中分配空间)               | `INT 0 5`     |
| **JMP**  | Jump (无条件跳转)                        | `JMP 0 10`    |
| **JPC**  | Jump Conditional (条件跳转，栈顶为0时跳) | `JPC 0 15`    |
| **OPR**  | Operation (执行算术/逻辑运算或返回)      | `OPR 0 2` (+) |
| **RED**  | Read (读取输入)                          | `RED 0 0`     |
| **WRT**  | Write (输出栈顶)                         | `WRT 0 0`     |
