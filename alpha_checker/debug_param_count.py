"""调试参数计数问题"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alpha_checker.alpha_checker import AlphaExpressionChecker

checker = AlphaExpressionChecker()

# 测试简单表达式
expr = "rank(field1)"
print(f"表达式: {expr}")

tokens = checker._tokenize(expr)
print(f"\nTokens:")
for i, token in enumerate(tokens):
    print(f"  {i}: {token}")

operators = checker._extract_operators(tokens)
print(f"\n操作符: {operators}")

# 手动检查参数计数
if operators:
    op_name = operators[0]
    # 找到操作符的位置
    for i, token in enumerate(tokens):
        if token['value'] == op_name and i + 1 < len(tokens) and tokens[i + 1]['value'] == '(':
            print(f"\n在位置 {i} 找到操作符 '{op_name}'")
            print(f"左括号在位置 {i + 1}")
            
            param_count = checker._count_parameters(tokens, i + 1)
            print(f"参数计数结果: {param_count}")
            break
