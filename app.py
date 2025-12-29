import streamlit as st
from pl0_lexer import Lexer
from pl0_parser import SLRParser

# ==========================================
# 1. 页面配置与侧边栏 (保持原样)
# ==========================================

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
        这是一个基于 **Python** 实现的 **PL/0 编译器**。
        
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

# ==========================================
# 2. 主页面布局
# ==========================================

st.title("🛠️ PL/0 编译器在线演示系统")
st.markdown("### 从源码到运行结果的完整可视化")

# 默认的测试代码 (修正了原代码中 call factorial 缺分号的问题)
default_code = """var x, fact;
begin
  x := 5;
  fact := 1;
  while x > 0 do
  begin
    fact := fact * x;
    x := x - 1
  end;
  write(fact)
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
        # 清除之前的状态
        if 'result' in st.session_state: del st.session_state['result']
        if 'p_code' in st.session_state: del st.session_state['p_code']

        try:
            # 1. 词法分析
            lexer = Lexer(code_input)
            
            # 先检查词法错误
            lexer.tokenize() 
            if lexer.has_error():
                st.error("❌ 词法分析失败 (Lexical Error)")
                for err in lexer.errors:
                    st.error(err)
            else:
                # 获取格式化后的 Tokens (带行号)
                tokens = lexer.get_tokens()
                st.session_state['tokens'] = tokens
                
                # 2. 语法分析
                # 注意：当前的 SLRParser 仅做语法校验，暂不生成 P-Code
                parser = SLRParser(tokens)
                parser.parse()
                
                st.success("✅ 编译成功！(语法分析通过)")
                
                # 由于我们目前只实现了 SLR 校验器，没有提供 CodeGen/VM 模块，
                # 这里做一个友好的提示，保持界面不崩溃。
                st.session_state['p_code'] = ["(当前版本仅支持语法检查，无目标代码生成)"]
                st.session_state['result'] = "Syntax Check Passed."
            
        except SyntaxError as se:
            st.error(f"❌ {se}") # 这里会直接显示带行号的错误信息
        except Exception as e:
            st.error(f"❌ 系统错误: {e}")

with col2:
    st.subheader("📊 编译器输出 (Compiler Output)")
    
    # 创建三个标签页 (保持原来的样式)
    tab1, tab2, tab3 = st.tabs(["🔤 词法分析 (Tokens)", "⚙️ 目标代码 (P-Code)", "🖥️ 运行结果 (Output)"])
    
    with tab1:
        st.caption("将源代码分解为 Token 流：")
        if 'tokens' in st.session_state:
            tokens = st.session_state['tokens']
            rows = []
            # 解析 tokens (Type, Value, Line)
            for t in tokens:
                # 兼容 Lexer 返回的三元组
                if isinstance(t, tuple) and len(t) >= 3:
                    t_type, t_val, t_line = t[0], t[1], t[2]
                    rows.append({"行": t_line, "Token 类型": t_type, "Token 值": t_val})
            
            st.dataframe(rows, use_container_width=True)

            # 把“语法解析（Parse Only）”按钮放在词法展示之后
            if st.button("🔍 语法解析 (Parse Only)", key="parse_in_tab"):
                try:
                    tokens = st.session_state['tokens']
                    parser = SLRParser(tokens)
                    parser.parse()
                    st.success("✅ 语法检查通过（符合文法）")
                except SyntaxError as se:
                    st.error(f"❌ {se}")
                except Exception as e:
                    st.error(f"❌ 解析失败: {e}")

        else:
            st.info("请点击左侧按钮开始编译...")
    
    with tab2:
        st.caption("生成的栈式计算机指令 (P-Code)：")
        if 'p_code' in st.session_state:
            # 简单展示
            st.code("\n".join(str(x) for x in st.session_state['p_code']))
        else:
            st.info("编译成功后将在此处显示目标代码...")
            
    with tab3:
        st.caption("虚拟机的控制台输出结果：")
        if 'result' in st.session_state:
            st.code(st.session_state['result'], language="text")
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