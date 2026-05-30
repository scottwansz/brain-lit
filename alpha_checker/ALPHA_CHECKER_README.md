# Alpha表达式检查器使用说明

## 概述

Alpha表达式检查器 (`alpha_checker.py`) 是一个用于验证WorldQuant Brain平台Alpha表达式语法正确性的工具。它可以检查：

1. **括号匹配** - 确保所有括号正确配对
2. **操作符合法性** - 验证使用的操作符是否在平台定义中
3. **参数数量** - 检查每个操作符的参数数量是否符合要求
4. **基本语法结构** - 检测常见的语法错误

## 快速开始

### 基本用法

```python
from alpha_checker.alpha_checker import check_alpha_expression

# 检查Alpha表达式
expression = "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01))"

result = check_alpha_expression(expression)

# 检查结果
if result.is_valid:
    print("✅ 表达式有效")
else:
    print(f"❌ 表达式无效，发现 {len(result.errors)} 个错误:")
    for error in result.errors:
        print(f"  - {error}")

# 查看使用的操作符和字段
print(f"操作符: {result.operators_used}")
print(f"字段: {result.fields_used}")
```

### 高级用法

```python
from alpha_checker.alpha_checker import AlphaExpressionChecker

# 创建检查器实例
checker = AlphaExpressionChecker()

# 检查表达式
result = checker.check(expression)

# 获取操作符信息
op_info = checker.get_operator_info('ts_delay')
print(f"ts_delay 定义: {op_info['definition']}")
print(f"ts_delay 描述: {op_info['description']}")

# 列出所有操作符
all_operators = checker.list_all_operators()
print(f"可用操作符数量: {len(all_operators)}")

# 按类别获取操作符
time_series_ops = checker.get_operators_by_category('Time Series')
print(f"时间序列操作符: {time_series_ops}")
```

## 检查结果说明

`check_alpha_expression` 函数返回一个 `ParseResult` 对象，包含以下属性：

- **is_valid** (bool): 表达式是否有效
- **errors** (List[CheckError]): 错误列表，如果表达式有效则为空
- **operators_used** (List[str]): 表达式中使用的所有操作符
- **fields_used** (List[str]): 表达式中使用的所有数据字段
- **structure_info** (Dict): 表达式的结构信息

### CheckError 对象

每个错误都是一个 `CheckError` 对象，包含：

- **position** (int): 错误在表达式中的位置
- **message** (str): 错误描述信息
- **error_type** (str): 错误类型，如：
  - `EMPTY_EXPRESSION`: 空表达式
  - `UNMATCHED_BRACKET`: 括号不匹配
  - `UNKNOWN_OPERATOR`: 未知操作符
  - `INSUFFICIENT_PARAMETERS`: 参数不足
  - `EXCESS_PARAMETERS`: 参数过多
  - `INVALID_START`: 无效的表达式开头
  - `MISSING_OPERATOR`: 可能缺少运算符

## 测试

运行测试套件验证检查器功能：

```bash
python tests/test_alpha_checker.py
```

## 示例

### 示例1: 检查复杂表达式

```python
expression = """
rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / 
     (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01)) + 
rank((vec_avg(anl2_consensus_revenue_estimate) - ts_delay(vec_avg(anl2_consensus_revenue_estimate), 20)) / 
     (abs(ts_delay(vec_avg(anl2_consensus_revenue_estimate), 20)) + 0.01)) + 
rank(if_else(is_nan(etz_eps_tsrank), 0, etz_eps_tsrank))
"""

result = check_alpha_expression(expression)

if result.is_valid:
    print("✅ 表达式语法正确")
    print(f"使用了 {len(result.operators_used)} 个不同的操作符")
    print(f"使用了 {len(result.fields_used)} 个数据字段")
else:
    for error in result.errors:
        print(f"错误: {error}")
```

### 示例2: 批量检查多个表达式

```python
expressions = [
    "rank(field1)",
    "ts_mean(close, 20)",
    "invalid_op(field1)",  # 未知操作符
    "ts_delay(field1)",    # 参数不足
]

checker = AlphaExpressionChecker()

for expr in expressions:
    result = checker.check(expr)
    status = "✅" if result.is_valid else "❌"
    print(f"{status} {expr[:50]}")
    if not result.is_valid:
        for error in result.errors:
            print(f"   {error}")
```

### 示例3: 获取操作符详细信息

```python
checker = AlphaExpressionChecker()

# 获取ts_delay的详细信息
op_info = checker.get_operator_info('ts_delay')
if op_info:
    print(f"名称: {op_info['name']}")
    print(f"类别: {op_info['category']}")
    print(f"定义: {op_info['definition']}")
    print(f"描述: {op_info['description']}")
    print(f"适用范围: {op_info['scope']}")
```

## 注意事项

1. **操作符定义**: 检查器基于 `alpha_operators.json` 文件中的操作符定义进行验证。确保该文件是最新的。

2. **字段验证**: 当前版本只提取字段名，不验证字段是否存在于平台中。如需验证字段，需要额外的API调用。

3. **参数默认值**: 检查器能够识别带有默认值的可选参数，并正确计算必需参数的最小数量。

4. **嵌套表达式**: 检查器支持任意深度的嵌套表达式和复杂的参数结构。

5. **性能**: 对于非常长的表达式，检查可能需要一些时间。建议在提交到平台之前先进行本地检查。

## 集成到工作流

可以将检查器集成到Alpha生成或提交流程中：

```python
def validate_and_submit_alpha(expression: str):
    """验证并提交Alpha表达式"""
    from alpha_checker.alpha_checker import check_alpha_expression
    from svc.submit import submit_alpha

    # 先进行语法检查
    result = check_alpha_expression(expression)

    if not result.is_valid:
        print("Alpha表达式存在语法错误:")
        for error in result.errors:
            print(f"  - {error}")
        return False

    # 语法正确，提交到平台
    try:
        response = submit_alpha(expression)
        print(f"Alpha提交成功: {response}")
        return True
    except Exception as e:
        print(f"提交失败: {e}")
        return False
```

## 故障排除

### 问题1: 报告参数数量错误，但实际是正确的

**原因**: 可能是操作符定义文件过时或不准确。

**解决**: 检查 `alpha_operators.json` 文件中该操作符的定义是否正确。

### 问题2: 某些合法表达式被标记为错误

**原因**: 检查器可能不支持某些特殊的语法结构。

**解决**: 查看错误类型，如果是误报，可以暂时忽略该类型的错误，或者更新检查器逻辑。

### 问题3: 字段提取不完整

**原因**: 某些字段可能被识别为操作符或关键字。

**解决**: 检查字段名是否与操作符名称冲突，或者是否是保留关键字。

## 扩展功能

未来可以考虑添加的功能：

1. **字段验证**: 通过API验证字段是否存在
2. **语义检查**: 检查操作符的参数类型是否匹配
3. **性能分析**: 评估表达式的计算复杂度
4. **自动修复**: 提供常见错误的自动修复建议
5. **表达式优化**: 提供表达式简化和优化建议

## 相关文件

- `ai/alpha_checker.py`: 检查器主文件
- `ai/alpha_operators.json`: 操作符定义文件
- `ai/alpha_operators.py`: Python格式的操作符列表
- `tests/test_alpha_checker.py`: 测试套件
