import streamlit as st
from pl0_lexer import Lexer
from pl0_parser import Parser
from pl0_vm import VM

# 设置页面标题和布局
st.set_page_config(
    layout="wide", 
    page_title="PL/0 编译器演示", 
    page_icon="🛠️"
)

# --- 侧边栏：项目介绍 ---
with st.sidebar:
    st.header("关于本项目")
    st.info(
        """
        这是一个基于 **Python** 实现的教学用 **PL/0 编译器**。
        
        它包含了编译器的完整四个阶段：
        1. **词法分析** (Lexer)
        2. **语法分析** (Parser)
        3. **中间/目标代码生成** (Code Gen)
        4. **虚拟机执行** (Stack VM)
        """
    )
    st.markdown("---")
    st.markdown("### 💡 语法小贴士")
    st.markdown("""
    - **变量声明**: `var x, y;`
    - **常量声明**: `const a = 10;`
    - **赋值**: `x := 10;` (注意是 `:=`)
    - **判断**: `if x < y then ...`
    - **循环**: `while x > 0 do ...`
    - **输入输出**: `read(x);`, `write(x);`
    - **程序结束**: 必须以 `.` 结尾
    """)

# --- 主页面 ---
st.title("🛠️ PL/0 编译器在线演示系统")
st.markdown("### 从源码到运行结果的完整可视化")

# 默认的测试代码
default_code = """var x, y;
begin
  x := 10;
  y := 20;
  if x < y then
    write(x + y)
end."""

# 创建两列布局
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 源代码输入 (Source Code)")
    code_input = st.text_area(
        "在此输入 PL/0 代码：", 
        value=default_code, 
        height=350,
        help="请确保代码符合 PL/0 语法规范，并以 '.' 结尾"
    )
    
    # 编译按钮
    run_button = st.button("🚀 编译并运行 (Compile & Run)", use_container_width=True, type="primary")

    if run_button:
        try:
            # 1. 词法分析
            lexer = Lexer(code_input)
            tokens = lexer.get_tokens()
            st.session_state['tokens'] = tokens
            
            # 2. 语法分析与代码生成
            parser = Parser(tokens)
            p_code = parser.parse()
            st.session_state['p_code'] = p_code
            
            # 3. 虚拟机执行
            vm = VM(p_code)
            result = vm.run()
            st.session_state['result'] = result
            
            st.success("✅ 编译成功！代码已执行。")
            
        except Exception as e:
            st.error(f"❌ 编译或运行出错: {e}")
            # 清除之前的错误状态，避免混淆
            if 'result' in st.session_state:
                del st.session_state['result']

with col2:
    st.subheader("📊 编译器输出 (Compiler Output)")
    
    # 创建三个标签页
    tab1, tab2, tab3 = st.tabs(["🔤 词法分析 (Tokens)", "⚙️ 目标代码 (P-Code)", "🖥️ 运行结果 (Output)"])
    
    with tab1:
        st.caption("将源代码分解为 Token 流：")
        if 'tokens' in st.session_state:
            st.dataframe(st.session_state['tokens'], use_container_width=True, column_config={
                0: "Token 类型",
                1: "Token 值"
            })
        else:
            st.info("请点击左侧按钮开始编译...")
    
    with tab2:
        st.caption("生成的栈式计算机指令 (P-Code)：")
        if 'p_code' in st.session_state:
            # 格式化 P-Code 以便阅读
            # 格式：行号 指令 层差 参数
            code_text = ""
            for i, inst in enumerate(st.session_state['p_code']):
                code_text += f"{i}\t{inst.f.name}\t{inst.l}\t{inst.a}\n"
            
            st.text_area("汇编指令预览", code_text, height=250)
            
            # 提供下载功能
            st.download_button(
                label="📥 下载目标代码 (.asm)",
                data=code_text,
                file_name="output.asm",
                mime="text/plain"
            )
        else:
            st.info("编译成功后将在此处显示目标代码...")
            
    with tab3:
        st.caption("虚拟机的控制台输出结果：")
        if 'result' in st.session_state:
            st.code(st.session_state['result'], language="text")
            if not st.session_state['result']:
                st.warning("程序运行完毕，但没有产生输出 (是否忘记使用 write 指令?)")
        else:
            st.info("等待运行...")

# --- 页脚 ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>"
    "这是一个用于《编译原理》 PL/0 实现。<br>"
    "支持基础的整数运算、条件判断、循环与过程调用。"
    "</div>", 
    unsafe_allow_html=True
)