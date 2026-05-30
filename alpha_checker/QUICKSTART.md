# Alpha表达式检查器 - 快速开始

## 5分钟上手指南

### 1. 安装和设置

无需额外安装，检查器已包含在项目中。确保你的Python环境可以访问项目目录。

### 2. 基本使用

#### 方法一：Python代码

```python
from alpha_checker.alpha_checker import check_alpha_expression

# 检查你的Alpha表达式
expression = "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01))"

result = check_alpha_expression(expression)

if result.is_valid:
    print("✅ 表达式有效！")
else:
    print("❌ 发现错误:")
    for error in result.errors:
        print(f"  {error}")
```

#### 方法二：命令行

```bash
# 检查单个表达式
python ai/check_alpha.py "rank(field1)"

# 查看详细结果
python ai/check_alpha.py "rank(field1)" --verbose
```

#### 方法三：交互模式

```bash
python ai/check_alpha.py --interactive
```

然后输入表达式进行检查。

### 3. 常见场景

#### 场景1: 验证新生成的Alpha

```python
from alpha_checker.alpha_checker import check_alpha_expression

alpha = "ts_mean(close, 20) / ts_std_dev(close, 20)"
result = check_alpha_expression(alpha)

if result.is_valid:
    # 提交到平台
    submit_to_platform(alpha)
else:
    # 修复错误
    print(result.errors)
```

#### 场景2: 批量验证多个Alpha

创建文件 `my_alphas.txt`:
```
rank(field1)
ts_mean(close, 20)
if_else(greater(volume, 1000), 1, 0)
```

运行:
```bash
python ai/check_alpha.py --file my_alphas.txt
```

#### 场景3: 查找表达式中的错误

```bash
# 使用JSON格式便于程序处理
python ai/check_alpha.py "ts_delay(close)" --json
```

输出:
```json
{
  "is_valid": false,
  "errors": [
    {
      "position": 0,
      "message": "操作符 'ts_delay' 至少需要 2 个参数，但只提供了 1 个",
      "error_type": "INSUFFICIENT_PARAMETERS"
    }
  ]
}
```

### 4. 解读检查结果

#### 成功的结果
```
✅ 表达式有效

📊 使用的操作符 (3):
   • rank
   • vec_avg
   • ts_delay

📋 使用的字段 (1):
   • anl2_consensus_eps_est
```

#### 失败的结果
```
❌ 表达式无效，发现 2 个错误:
   - 位置 4: [UNMATCHED_BRACKET] 未闭合的左括号
   - 位置 0: [INSUFFICIENT_PARAMETERS] 操作符 'rank' 至少需要 1 个参数，但只提供了 0 个
```

### 5. 常见错误类型

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| `EMPTY_EXPRESSION` | 空表达式 | `""` |
| `UNMATCHED_BRACKET` | 括号不匹配 | `"rank(field1"` |
| `UNKNOWN_OPERATOR` | 未知操作符 | `"unknown_op(x)"` |
| `INSUFFICIENT_PARAMETERS` | 参数不足 | `"ts_delay(x)"` |
| `EXCESS_PARAMETERS` | 参数过多 | `"rank(x, y, z)"` |

### 6. 获取帮助

```bash
# 查看命令行帮助
python ai/check_alpha.py --help

# 在交互模式中
>>> help
```

### 7. 下一步

- 📖 阅读完整文档: `ai/ALPHA_CHECKER_README.md`
- 🧪 运行测试: `python tests/test_alpha_checker.py`
- 💡 查看示例: `tests/test_expressions.txt`

## 常见问题

**Q: 为什么我的表达式被标记为错误？**
A: 检查错误信息，常见原因包括：括号不匹配、使用了未知操作符、参数数量不正确。

**Q: 如何知道某个操作符需要多少个参数？**
A: 在交互模式中使用 `info <操作符名>` 查看详细信息。

**Q: 检查器能验证字段是否存在吗？**
A: 当前版本只检查语法，不验证字段是否存在于平台中。

**Q: 可以在CI/CD流程中使用吗？**
A: 可以！使用 `--json` 标志可以获得机器可读的输出。

## 需要帮助？

- 查看完整文档: `ai/ALPHA_CHECKER_README.md`
- 查看项目总结: `ALPHA_CHECKER_SUMMARY.md`
- 运行测试验证功能: `python tests/test_alpha_checker.py`
