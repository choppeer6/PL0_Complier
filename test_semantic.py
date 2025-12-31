"""
测试 PL/0 语义分析和四元式生成模块
"""

from pl0_lexer import Lexer
from pl0_semantic import SemanticAnalyzer

def test_program(name, code):
    """测试一个 PL/0 程序"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    print("源代码:")
    print(code)
    print(f"\n{'-'*60}")
    
    try:
        # 1. 词法分析
        print("1. 词法分析...")
        lexer = Lexer(code)
        tokens = lexer.get_tokens()
        print(f"   生成 {len(tokens)} 个 tokens")
        
        if lexer.has_error():
            print("   词法错误:")
            lexer.print_errors()
            return
        
        # 2. 语义分析和四元式生成
        print("2. 语义分析和四元式生成...")
        analyzer = SemanticAnalyzer(tokens)
        quadruples = analyzer.analyze()
        print(f"   生成 {len(quadruples)} 条四元式")
        
        # 显示符号表
        analyzer.symbol_table.print_table()
        
        # 显示四元式
        analyzer.print_quadruples()
        
        print(f"\n[成功] 测试通过: {name}")
        
    except Exception as e:
        print(f"\n[失败] 测试失败: {e}")
        import traceback
        traceback.print_exc()

# ==========================================
# 测试用例
# ==========================================

if __name__ == '__main__':
    
    # 测试1: 简单的算术运算
    test_program(
        "简单算术运算",
        """
        var x, y, z;
        begin
            x := 10;
            y := 20;
            z := x + y;
            write(z)
        end.
        """
    )
    
    # 测试2: 常量定义
    test_program(
        "常量定义",
        """
        const max = 100, min = 0;
        var x;
        begin
            x := max - min;
            write(x)
        end.
        """
    )
    
    # 测试3: 条件语句
    test_program(
        "条件语句",
        """
        var x, y;
        begin
            x := 15;
            y := 10;
            if x > y then
                write(x)
        end.
        """
    )
    
    # 测试4: 循环语句 - 计算1到5的和
    test_program(
        "循环语句 - 求和",
        """
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
        """
    )
    
    # 测试5: ODD 函数
    test_program(
        "ODD 函数测试",
        """
        var x;
        begin
            x := 7;
            if odd x then
                write(1)
        end.
        """
    )
    
    # 测试6: 复杂表达式
    test_program(
        "复杂表达式",
        """
        var a, b, c, result;
        begin
            a := 5;
            b := 3;
            c := 2;
            result := a * b + c;
            write(result)
        end.
        """
    )
    
    # 测试7: 嵌套的 BEGIN-END
    test_program(
        "嵌套的复合语句",
        """
        var x;
        begin
            x := 1;
            begin
                x := x + 1;
                x := x + 1
            end;
            write(x)
        end.
        """
    )
    
    # 测试8: 过程调用
    test_program(
        "过程调用",
        """
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
        """
    )
    
    # 测试9: READ 语句
    test_program(
        "READ 语句",
        """
        var x, y;
        begin
            read(x);
            read(y);
            write(x + y)
        end.
        """
    )
    
    # 测试10: 所有关系运算符
    test_program(
        "关系运算符测试",
        """
        var a, b;
        begin
            a := 10;
            b := 20;
            if a < b then write(1);
            if a # b then write(4)
        end.
        """
    )
    
    # 测试11: 负数
    test_program(
        "负数测试",
        """
        var x, y;
        begin
            x := 10;
            y := -x;
            write(y)
        end.
        """
    )
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)
