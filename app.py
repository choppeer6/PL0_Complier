import streamlit as st
from pl0_lexer import Lexer
from pl0_parser import SLRParser
from pl0_semantic import SemanticAnalyzer  # 语义分析和四元式生成器

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
        这是一个基于 **Python** 实现的 **PL/0 编译器**。
        
        它包含了编译器的完整阶段：
        1. **词法分析** (Lexer)
        2. **语法分析** (Parser)
        3. **语义分析** (Semantic Analyzer)
        4. **中间代码生成** (四元式)
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
st.markdown("### 语义分析与四元式生成")

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
    run_button = st.button("🚀 编译 (Compile)", use_container_width=True, type="primary")

    if run_button:
        try:
            # 1. 词法分析
            lexer = Lexer(code_input)
            tokens = lexer.get_tokens()
            st.session_state['tokens'] = tokens
            
            # 2. 语义分析与四元式生成
            analyzer = SemanticAnalyzer(tokens)
            quadruples = analyzer.analyze()
            st.session_state['quadruples'] = quadruples
            st.session_state['analyzer'] = analyzer
            
            st.success("✅ 编译成功！")
            
        except Exception as e:
            st.error(f"❌ 编译出错: {e}")
            # 清除之前的错误状态
            if 'quadruples' in st.session_state:
                del st.session_state['quadruples']
            if 'analyzer' in st.session_state:
                del st.session_state['analyzer']

with col2:
    st.subheader("📊 编译器输出 (Compiler Output)")
    
    # 创建三个标签页
    tab1, tab2, tab3 = st.tabs(["🔤 词法分析 (Tokens)", "📋 符号表 (Symbol Table)", "⚙️ 四元式 (Quadruples)"])
    
    with tab1:
        st.caption("将源代码分解为 Token 流：")
        if 'tokens' in st.session_state:
            tokens = st.session_state['tokens']
            src_text = code_input
            rows = []
            cur_pos = 0
            
            for t in tokens:
                line_no = 0
                t_type = ""
                t_val = ""
                
                if isinstance(t, (tuple, list)):
                    if len(t) >= 2:
                        t_type = t[0]
                        t_val = t[1]
                    if len(t) >= 3 and isinstance(t[2], int):
                        line_no = t[2]
                    elif len(t) >= 4 and isinstance(t[3], int):
                        line_no = t[3]
                
                if not line_no and isinstance(t_val, str) and src_text:
                    try:
                        idx = src_text.find(t_val, cur_pos)
                        if idx != -1:
                            line_no = src_text.count('\n', 0, idx) + 1
                            cur_pos = idx + max(1, len(t_val))
                    except Exception:
                        line_no = 0

                rows.append({"行": line_no, "Token 类型": t_type, "Token 值": t_val})
            
            st.dataframe(rows, use_container_width=True)

            # 语法解析按钮
            if st.button("🔍 语法解析 (Parse Only)", key="parse_in_tab"):
                try:
                    tokens = st.session_state['tokens']
                    parser = SLRParser(tokens)
                    parser.parse()
                    st.success("✅ 语法检查通过（符合文法）")
                except SyntaxError as se:
                    st.error(f"❌ 语法错误: {se}")
                except Exception as e:
                    st.error(f"❌ 解析失败: {e}")

        else:
            st.info("请点击左侧按钮开始编译...")
    
    with tab2:
        st.caption("符号表（变量、常量、过程）：")
        if 'analyzer' in st.session_state:
            analyzer = st.session_state['analyzer']
            symbols = analyzer.symbol_table.symbols
            
            if symbols:
                rows = []
                for symbol in symbols:
                    row = {
                        "名字": symbol.name,
                        "类型": symbol.type.value,
                        "层次": symbol.level,
                        "值": symbol.value if symbol.type.value == "常量" else "-",
                        "地址": symbol.address if symbol.type.value != "常量" else "-"
                    }
                    rows.append(row)
                
                st.dataframe(rows, use_container_width=True)
            else:
                st.info("符号表为空")
        else:
            st.info("编译成功后将在此处显示符号表...")
            
    with tab3:
        st.caption("生成的四元式中间代码：")
        if 'quadruples' in st.session_state:
            quadruples = st.session_state['quadruples']
            
            # 使用表格显示四元式
            rows = []
            for i, quad in enumerate(quadruples):
                row = {
                    "序号": i,
                    "操作符": quad.op,
                    "参数1": quad.arg1,
                    "参数2": quad.arg2,
                    "结果": quad.result
                }
                rows.append(row)
            
            st.dataframe(rows, use_container_width=True)
            
            # 生成下载用的文本格式
            download_text = f"{'序号':<6} {'操作符':<10} {'参数1':<10} {'参数2':<10} {'结果':<10}\n"
            download_text += "-" * 60 + "\n"
            for i, quad in enumerate(quadruples):
                download_text += f"{i:<6} {quad.op:<10} {quad.arg1:<10} {quad.arg2:<10} {quad.result:<10}\n"
            
            # 提供下载功能
            st.download_button(
                label="📥 下载四元式 (.txt)",
                data=download_text,
                file_name="quadruples.txt",
                mime="text/plain"
            )
        else:
            st.info("编译成功后将在此处显示四元式...")

# --- 页脚 ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>"
    "PL/0 编译器 - 语义分析与四元式生成<br>"
    "支持基础的整数运算、条件判断、循环与过程调用。"
    "</div>", 
    unsafe_allow_html=True
)
