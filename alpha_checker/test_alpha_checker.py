"""
Alpha表达式检查器测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alpha_checker.alpha_checker import AlphaExpressionChecker


def test_basic_syntax():
    """测试基本语法检查"""
    print("=" * 80)
    print("测试1: 基本语法检查")
    print("=" * 80)
    
    # 测试用例
    test_cases = [
        {
            "name": "正确的复杂表达式",
            "expression": "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01)) + rank((vec_avg(anl2_consensus_revenue_estimate) - ts_delay(vec_avg(anl2_consensus_revenue_estimate), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_revenue_estimate), 20)) + 0.01)) + rank(if_else(is_nan(etz_eps_tsrank), 0, etz_eps_tsrank))",
            "should_pass": True
        },
        {
            "name": "简单有效表达式",
            "expression": "rank(field1)",
            "should_pass": True
        },
        {
            "name": "括号不匹配 - 缺少右括号",
            "expression": "rank(field1",
            "should_pass": False
        },
        {
            "name": "括号不匹配 - 多余右括号",
            "expression": "rank(field1))",
            "should_pass": False
        },
        {
            "name": "空表达式",
            "expression": "",
            "should_pass": False
        },
    ]
    
    checker = AlphaExpressionChecker()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"表达式: {test_case['expression'][:100]}{'...' if len(test_case['expression']) > 100 else ''}")
        
        result = checker.check(test_case['expression'])
        
        if result.is_valid == test_case['should_pass']:
            status = "[PASS] PASS"
        else:
            status = "[FAIL] FAIL"
        
        print(f"期望: {'通过' if test_case['should_pass'] else '失败'} | 实际: {'通过' if result.is_valid else '失败'} | {status}")
        
        if not result.is_valid:
            print(f"错误数量: {len(result.errors)}")
            for error in result.errors[:3]:  # 只显示前3个错误
                print(f"  - {error}")
            if len(result.errors) > 3:
                print(f"  ... 还有 {len(result.errors) - 3} 个错误")
        
        if result.operators_used:
            print(f"操作符: {', '.join(result.operators_used[:5])}{'...' if len(result.operators_used) > 5 else ''}")
        
        if result.fields_used:
            print(f"字段: {', '.join(result.fields_used[:5])}{'...' if len(result.fields_used) > 5 else ''}")


def test_operator_validation():
    """测试操作符验证"""
    print("\n" + "=" * 80)
    print("测试2: 操作符验证")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "使用未知操作符",
            "expression": "unknown_operator(field1)",
            "expected_error_type": "UNKNOWN_OPERATOR"
        },
        {
            "name": "参数不足",
            "expression": "ts_delay(field1)",  # ts_delay需要2个参数
            "expected_error_type": "INSUFFICIENT_PARAMETERS"
        },
        {
            "name": "正确使用操作符",
            "expression": "ts_delay(field1, 10)",
            "expected_error_type": None
        },
        {
            "name": "嵌套操作符",
            "expression": "rank(ts_decay_linear(field1, 10))",
            "expected_error_type": None
        },
    ]
    
    checker = AlphaExpressionChecker()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"表达式: {test_case['expression']}")
        
        result = checker.check(test_case['expression'])
        
        if test_case['expected_error_type'] is None:
            # 期望没有错误
            if result.is_valid:
                print(f"[PASS] PASS - 表达式有效")
            else:
                print(f"[FAIL] FAIL - 期望有效但发现错误:")
                for error in result.errors:
                    print(f"  - {error}")
        else:
            # 期望特定类型的错误
            found_expected_error = any(error.error_type == test_case['expected_error_type'] 
                                      for error in result.errors)
            if found_expected_error:
                print(f"[PASS] PASS - 找到期望的错误类型: {test_case['expected_error_type']}")
            else:
                print(f"[FAIL] FAIL - 未找到期望的错误类型: {test_case['expected_error_type']}")
                if result.errors:
                    print(f"实际错误:")
                    for error in result.errors:
                        print(f"  - {error}")


def test_complex_expressions():
    """测试复杂表达式"""
    print("\n" + "=" * 80)
    print("测试3: 复杂表达式")
    print("=" * 80)
    
    complex_expressions = [
        "group_neutralize(rank(ts_mean(close, 20)), industry)",
        "if_else(greater(volume, ts_mean(volume, 20)), 1, -1)",
        "ts_corr(close, volume, 30) / ts_std_dev(close, 30)",
        "multiply(add(field1, field2), subtract(field3, field4))",
        "rank(zscore(ts_returns(close, 1)))",
    ]
    
    checker = AlphaExpressionChecker()
    
    for i, expr in enumerate(complex_expressions, 1):
        print(f"\n表达式 {i}:")
        print(f"{expr}")
        
        result = checker.check(expr)
        
        if result.is_valid:
            print(f"[PASS] 有效")
        else:
            print(f"[FAIL] 无效 ({len(result.errors)} 个错误)")
            for error in result.errors[:2]:
                print(f"  - {error}")
        
        if result.operators_used:
            print(f"操作符 ({len(result.operators_used)}): {', '.join(result.operators_used)}")


def test_parameter_counting():
    """测试参数计数"""
    print("\n" + "=" * 80)
    print("测试4: 参数计数验证")
    print("=" * 80)
    
    test_cases = [
        ("add(a, b)", "add", 2),
        ("max(a, b, c)", "max", 3),
        ("ts_delay(x, 10)", "ts_delay", 2),
        ("if_else(cond, true_val, false_val)", "if_else", 3),
        ("group_mean(x, weight, group)", "group_mean", 3),
    ]
    
    checker = AlphaExpressionChecker()
    
    for expr, expected_op, expected_params in test_cases:
        print(f"\n表达式: {expr}")
        
        result = checker.check(expr)
        
        if expected_op in result.operators_used:
            print(f"[PASS] 检测到操作符: {expected_op}")
            
            # 检查是否有参数相关的错误
            param_errors = [e for e in result.errors 
                          if '参数' in e.message or 'PARAMETER' in e.error_type]
            
            if not param_errors:
                print(f"[PASS] 参数数量正确 (期望: {expected_params})")
            else:
                print(f"[FAIL] 参数数量问题:")
                for error in param_errors:
                    print(f"  - {error}")
        else:
            print(f"[FAIL] 未检测到操作符: {expected_op}")


def test_field_extraction():
    """测试字段提取"""
    print("\n" + "=" * 80)
    print("测试5: 字段提取")
    print("=" * 80)
    
    expression = "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01))"
    
    checker = AlphaExpressionChecker()
    result = checker.check(expression)
    
    print(f"表达式: {expression[:80]}...")
    print(f"\n提取的字段 ({len(result.fields_used)}):")
    for field in result.fields_used:
        print(f"  - {field}")
    
    print(f"\n提取的操作符 ({len(result.operators_used)}):")
    for op in result.operators_used:
        print(f"  - {op}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("Alpha表达式检查器测试套件")
    print("=" * 80)
    
    try:
        test_basic_syntax()
        test_operator_validation()
        test_complex_expressions()
        test_parameter_counting()
        test_field_extraction()
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
