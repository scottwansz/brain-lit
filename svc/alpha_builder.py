import random
import re
from typing import List, Dict
from itertools import combinations

# 定义回填窗口常量
BACKFILL_WINDOWS = [5, 10, 20, 60, 120, 250]


def get_alpha_templates() -> Dict[str, Dict]:
    """创建优化后的模板系统"""

    # 基础模板 - 根据参数模式分类的操作符模板
    simple_templates = {
        # 基本双参数模式 (字段, 窗口) - 包含可选额外参数的操作符
        "ts_basic": {
            "structure": "{ts_op}({field_expr}, {window})",
            "description": "基本时间序列操作符模板",
            "category": "simple",
            "suitable_ts_ops": ["ts_zscore", "ts_product", "ts_std_dev", "ts_av_diff", 
                               "ts_kurtosis", "ts_mean", "ts_sum", "ts_entropy",
                               "ts_arg_min", "ts_skewness", "ts_max_diff", "ts_median",
                               "ts_delta", "ts_arg_max", "ts_max", "ts_min", "ts_rank",
                               "ts_returns", "ts_scale", "ts_moment", "ts_decay_exp_window", "ts_quantile"],
            "suitable_windows": [5, 10, 20],
            "extra_params": {
                "ts_returns": ["mode=1"],
                "ts_scale": ["constant=0"],
                "ts_moment": ["k=0"],
                "ts_decay_exp_window": ["factor=1"],
                "ts_quantile": ['driver="gaussian"']
            }
        },
        
        # ts_regression模板 - 用于残差动量等场景
        "ts_regression": {
            "structure": "ts_regression({field_y}, {field_x}, {window}, lag=0, rettype=1)",
            "description": "回归分析时间序列操作符模板",
            "category": "simple",
            "suitable_ts_ops": ["ts_regression"],
            "suitable_windows": [10, 20, 60]
        }
    }

    # 高级模板 - 使用简单模板输出作为输入
    advanced_templates = {
        "sector_neutral_robust": {
            "structure": "group_neutralize({simple_expr}, sector)",
            "description": "稳健行业中性因子",
            "category": "advanced",
            "suitable_windows": [10, 20]
        },

        "volatility_adjusted": {
            "structure": "divide({simple_expr}, ts_std_dev({field_expr}, {window}))",
            "description": "波动率调整因子",
            "category": "advanced",
            "suitable_windows": [5, 10, 20, 60]
        },

        "cross_sectional_ops": {
            "structure": "{cs_op}({simple_expr})",
            "description": "横截面标准化因子",
            "category": "advanced",
            "suitable_cs_ops": ["zscore", "rank", "scale"]
        }
    }

    return {**simple_templates, **advanced_templates}


def process_field_by_coverage(field: str, field_info: Dict) -> str:
    """
    根据字段覆盖率和类型处理字段表达式
    """
    field_type = field_info['type']
    coverage = field_info.get('coverage', 1.0)

    # 处理字段类型
    if field_type == "VECTOR":
        vector_ops = ["vec_avg", "vec_sum", "vec_max"]
        field_expr = f"{random.choice(vector_ops)}({field})"
    else:
        field_expr = field

    # 根据覆盖率选择回填窗口
    # 计算数据缺失天数：250*(1-覆盖率)
    missing_days = 250 * (1 - coverage)
    backfill_window = next((w for w in BACKFILL_WINDOWS if w > missing_days), 250)

    field_expr = f"ts_backfill({field_expr}, {backfill_window})"

    return field_expr


def process_all_fields(fields: Dict[str, Dict]) -> Dict[str, str]:
    """
    预处理所有字段，避免在模板中重复处理
    """
    processed = {}
    for field, field_info in fields.items():
        processed[field] = process_field_by_coverage(field, field_info)
    return processed




def generate_simple_expressions(processed_fields: Dict[str, str], template_name: str = None, max_expressions: int = 20) -> Dict[str, List[str]]:
    """给定字段列表生成这些字段的简单表达式"""
    # 预处理字段
    all_templates = get_alpha_templates()
    
    if template_name:
        if template_name not in all_templates:
            raise ValueError(f"未知模板: {template_name}")
        template_names = [template_name]
    else:
        # 默认使用所有简单模板
        template_names = [name for name, template in all_templates.items() 
                        if template["category"] == "simple"]

    all_expressions = {}
    
    for tmpl_name in template_names:
        template = all_templates[tmpl_name]
        expressions = {}
        
        try:
            if tmpl_name == "ts_regression":
                expressions = _generate_residual_expressions(template, processed_fields, max_expressions)
            elif tmpl_name in ["ts_basic", "ts_complex"]:
                expressions = _generate_simple_expressions(template, processed_fields, max_expressions, tmpl_name)
            
            # 合并到总表达式中，去重
            for field, exprs in expressions.items():
                if field not in all_expressions:
                    all_expressions[field] = []
                # 先合并再整体去重，保持顺序
                all_expressions[field].extend(exprs)
                all_expressions[field] = list(dict.fromkeys(all_expressions[field]))
                
        except Exception as e:
            print(f"生成模板 {tmpl_name} 时出错: {e}")

    return all_expressions

def generate_complex_expressions(simple_expressions: Dict[str, List[str]], template_name: str = None, max_expressions: int = 20) -> Dict[str, List[str]]:
    """给定带字段ID信息的简单表达式列表生成复杂表达式"""
    all_templates = get_alpha_templates()
        
    if template_name:
        if template_name not in all_templates:
            raise ValueError(f"未知模板: {template_name}")
        template_names = [template_name]
    else:
        # 默认使用所有高级模板
        template_names = [name for name, template in all_templates.items() 
                        if template["category"] == "advanced"]

    all_expressions = {}
    
    for tmpl_name in template_names:
        template = all_templates[tmpl_name]
        expressions = {}
        
        try:
            if tmpl_name in ["sector_neutral_robust", "volatility_adjusted", "cross_sectional_ops"]:
                expressions = _generate_advanced_expressions(template, simple_expressions, max_expressions, tmpl_name)
            
            # 合并到总表达式中，去重
            for field, exprs in expressions.items():
                if field not in all_expressions:
                    all_expressions[field] = []
                # 先合并再整体去重，保持顺序
                all_expressions[field].extend(exprs)
                all_expressions[field] = list(dict.fromkeys(all_expressions[field]))
                
        except Exception as e:
            print(f"生成模板 {tmpl_name} 时出错: {e}")

    return all_expressions

def _generate_unary_ops_expressions(template: Dict, processed_fields: Dict[str, str], max_expr: int) -> Dict[str, List[str]]:
    """生成一元操作符模板表达式，返回带字段信息的结构"""
    expressions = {}

    for field in processed_fields:
        field_expr = processed_fields[field]
        expressions[field] = []

        for op in template["suitable_ops"]:
            if len(expressions[field]) >= max_expr:
                break
                
            expr = template["structure"].format(
                op=op, field_expr=field_expr
            )
            expressions[field].append(expr)

    return expressions



def _generate_simple_expressions(template: Dict, processed_fields: Dict[str, str], max_expr: int, template_name: str) -> Dict[str, List[str]]:
    """生成简单模板表达式，返回带字段信息的结构"""
    expressions = {}

    # 特殊处理ts_regression模板，需要两个字段
    if template_name == "ts_regression":
        return _generate_residual_expressions(template, processed_fields, max_expr)

    for field in processed_fields:
        field_expr = processed_fields[field]
        expressions[field] = []

        # 如果没有适合的操作符，直接返回空表达式
        if not template.get("suitable_ts_ops"):
            continue

        for ts_op in template["suitable_ts_ops"]:
            for window in template["suitable_windows"]:
                if len(expressions[field]) >= max_expr:
                    break
                    
                # 根据模板类型生成表达式
                if template_name == "ts_basic":
                    # 复制额外参数（如果存在）
                    extra_params = template.get("extra_params", {}).get(ts_op, [])
                    if extra_params:
                        # 生成带额外参数的表达式
                        for extra_param in extra_params:
                            if len(expressions[field]) >= max_expr:
                                break
                            expr = f"{ts_op}({field_expr}, {window}, {extra_param})"
                            expressions[field].append(expr)
                    
                    # 生成不带额外参数的表达式（退化为双参数）
                    if len(expressions[field]) < max_expr:
                        expr = f"{ts_op}({field_expr}, {window})"
                        expressions[field].append(expr)
                elif template_name == "ts_triple":
                    # 获取额外参数
                    extra_params = template.get("extra_params", {}).get(ts_op, [])
                    if extra_params:
                        # 随机选择一个额外参数
                        extra_param = random.choice(extra_params)
                        expr = template["structure"].format(
                            ts_op=ts_op, field_expr=field_expr, window=window, extra_param=extra_param
                        )
                        expressions[field].append(expr)
                    else:
                        # 如果没有额外参数，使用基本结构
                        expr = f"{ts_op}({field_expr}, {window})"
                        expressions[field].append(expr)
                elif template_name in ["ts_complex"]:
                    # 获取额外参数
                    extra_params_list = template.get("extra_params", {}).get(ts_op, [])
                    if extra_params_list:
                        # 连接所有额外参数
                        extra_params_str = "".join(extra_params_list)
                        expr = template["structure"].format(
                            ts_op=ts_op, field_expr=field_expr, window=window, extra_params=extra_params_str
                        )
                        expressions[field].append(expr)
                    else:
                        # 如果没有额外参数，使用基本结构
                        expr = template["structure"].format(
                            ts_op=ts_op, field_expr=field_expr, window=window
                        )
                        expressions[field].append(expr)
        
    return expressions

def _extract_field_expr_from_simple_expr(simple_expr: str) -> str:
    """
    从简单表达式中提取字段表达式
    例如: 从 "ts_zscore(ts_backfill(anl11_1e, 120), 5)" 提取 "ts_backfill(anl11_1e, 120)"
    """
    # 尝试匹配 ts_backfill 模式
    backfill_match = re.search(r'\w+\((ts_backfill\([^)]+\))', simple_expr)
    if backfill_match:
        return backfill_match.group(1)
    
    # 尝试匹配普通字段模式
    field_match = re.search(r'\w+\(([^,]+),[^)]*\)', simple_expr)
    if field_match:
        return field_match.group(1)
    
    # 如果无法匹配，则返回空字符串
    return ""

def _generate_advanced_expressions(template: Dict, simple_expressions: Dict[str, List[str]], max_expr: int, template_name: str) -> Dict[str, List[str]]:
    """使用简单模板输出作为输入生成高级模板表达式"""
    expressions = {}
    
    for field in simple_expressions:
        expressions[field] = []
        
        # 获取该字段的简单表达式作为输入
        simple_exprs = simple_expressions.get(field, [])
        if not simple_exprs:
            continue
            
        if template_name == "sector_neutral_robust":
            # 对于sector_neutral_robust，使用基础模板的输出
            for simple_expr in simple_exprs[:max_expr]:  # 限制数量
                for window in template.get("suitable_windows", [10, 20]):
                    if len(expressions[field]) >= max_expr:
                        break
                    expr = template["structure"].format(simple_expr=simple_expr, window=window)
                    expressions[field].append(expr)
                    
        elif template_name == "volatility_adjusted":
            # 对于volatility_adjusted，使用基础模板的输出
            # 从simple_expr中提取field_expr
            sample_expr = simple_exprs[0] if simple_exprs else ""
            field_expr = _extract_field_expr_from_simple_expr(sample_expr)
            
            # 如果无法提取，则使用字段名作为默认值
            if not field_expr:
                field_expr = field
                
            for simple_expr in simple_exprs[:max_expr]:  # 限制数量
                for window in template.get("suitable_windows", [5, 10, 20]):
                    if len(expressions[field]) >= max_expr:
                        break
                    expr = template["structure"].format(simple_expr=simple_expr, field_expr=field_expr, window=window)
                    expressions[field].append(expr)
                    
        elif template_name == "cross_sectional_ops":
            # 对于cross_sectional_ops，使用基础模板的输出
            for simple_expr in simple_exprs[:max_expr]:  # 限制数量
                for cs_op in template.get("suitable_cs_ops", ["zscore", "rank", "scale"]):
                    if len(expressions[field]) >= max_expr:
                        break
                    expr = template["structure"].format(simple_expr=simple_expr, cs_op=cs_op)
                    expressions[field].append(expr)
                    
    return expressions

def _generate_residual_expressions(template: Dict, processed_fields: Dict[str, str], max_expr: int) -> Dict[str, List[str]]:
    """生成残差模板表达式，返回带字段信息的结构"""
    expressions = {}

    # 直接生成字段对
    field_pairs = list(combinations(processed_fields.keys(), 2))

    for field_pair in field_pairs:
        if len(field_pair) >= 2:
            field1, field2 = field_pair[0], field_pair[1]
        else:
            continue
            
        # 处理两个字段
        field1_expr = processed_fields[field1]
        field2_expr = processed_fields[field2]
        
        # 以第一个字段作为主字段
        if field1 not in expressions:
            expressions[field1] = []
        
        for window in template.get("suitable_windows", [10, 20, 60]):
            if len(expressions[field1]) >= max_expr:
                break

            expr = template["structure"].format(
                field_y=field1_expr, field_x=field2_expr, window=window
            )
            expressions[field1].append(expr)

    return expressions

def generate_all_expressions(processed_fields: Dict[str, str], template_name: str = None, max_expressions: int = 20) -> Dict[str, Dict[str, List[str]]]:
    """生成多样化的表达式集合，按字段和模板组织"""
        
    all_expressions = {}

    # 生成简单表达式
    simple_exprs = generate_simple_expressions(processed_fields, template_name, max_expressions)
    # 合并到all_expressions中，去重
    for field, exprs in simple_exprs.items():
        if field not in all_expressions:
            all_expressions[field] = {}
        # 对简单表达式进行去重
        unique_exprs = list(dict.fromkeys(exprs))  # 保持顺序的去重
        all_expressions[field]["simple"] = unique_exprs

    # 生成复杂表达式
    complex_exprs = generate_complex_expressions(simple_exprs, None, max_expressions)
    # 合并到all_expressions中，去重
    for field, exprs in complex_exprs.items():
        if field not in all_expressions:
            all_expressions[field] = {}
        # 对复杂表达式进行去重
        unique_exprs = list(dict.fromkeys(exprs))  # 保持顺序的去重
        all_expressions[field]["complex"] = unique_exprs

    return all_expressions

def analyze_field_coverage(fields: Dict[str, Dict]) -> Dict:
    """分析字段覆盖率"""
    coverage_stats = {
        "total_fields": len(fields),
        "field_details": {},
        "window_options": BACKFILL_WINDOWS
    }

    for field, info in fields.items():
        coverage = info.get('coverage', 1.0)
        # 使用新的计算方式选择回填窗口
        # 计算数据缺失天数：250*(1-覆盖率)
        missing_days = 250 * (1 - coverage)
        backfill_window = next((w for w in BACKFILL_WINDOWS if w > missing_days), 250)
        
        coverage_stats["field_details"][field] = {
            "type": info['type'],
            "coverage": coverage,
            "backfill_window": backfill_window
        }

    return coverage_stats

def get_coverage_advice(fields: Dict[str, Dict]) -> str:
    """获取覆盖率处理建议"""
    stats = analyze_field_coverage(fields)
    advice = []

    advice.append("=== 覆盖率处理建议 ===")
    advice.append(f"字段总数: {stats['total_fields']}")

    advice.append(f"\n可用回填窗口: {BACKFILL_WINDOWS}")
    advice.append("\n回填策略:")
    advice.append("  - 根据公式 250*(1-覆盖率) 计算数据缺失天数")
    advice.append(f"  - 从 {BACKFILL_WINDOWS} 中选择大于数据缺失天数的最小窗口")
    advice.append("  - 覆盖率越高，(1-覆盖率)越小，数据缺失天数越少，所选窗口越短")
    advice.append("  - 覆盖率越低，(1-覆盖率)越大，数据缺失天数越多，所选窗口越长")

    return "\n".join(advice)

def get_window_usage_stats(expressions: List[str]) -> Dict:
    """统计回填窗口使用情况"""
    import re
    window_stats = {str(window): 0 for window in BACKFILL_WINDOWS}

    for expr in expressions:
        # 提取所有回填窗口
        matches = re.findall(r'ts_backfill\([^,]+,\s*(\d+)\)', expr)
        for match in matches:
            window = int(match)
            if str(window) in window_stats:
                window_stats[str(window)] += 1

    return window_stats


# 使用示例
def main():
    # 示例字段数据（包含覆盖率信息）
    fields = {
        'anl11_1e': {'type': 'MATRIX', 'coverage': 0.5813},
        'anl11_1g': {'type': 'MATRIX', 'coverage': 0.5822},
        'anl11_1pme': {'type': 'MATRIX', 'coverage': 0.5823},
        'anl11_1tic': {'type': 'MATRIX', 'coverage': 0.7915},
        'anl11_2e': {'type': 'MATRIX', 'coverage': 0.7921},
        'anl11_2g': {'type': 'VECTOR', 'coverage': 0.4523},
        'anl11_2pme': {'type': 'MATRIX', 'coverage': 0.8234},
        'snt22dts_sop': {'type': 'MATRIX', 'coverage': 0.3812},
        'snt22_2dts_sop_7': {'type': 'MATRIX', 'coverage': 0.7123}
    }

    # 预处理字段
    processed_fields = process_all_fields(fields)

    # 测试简单表达式生成
    print(f"\n=== 简单表达式生成 ===")
    simple_exprs = generate_simple_expressions(processed_fields, "ts_basic", 10)
    for field, field_exprs in simple_exprs.items():
        print(f"  {field}")
        for i, expr in enumerate(field_exprs[:10], 1):
            print(f"    {i}. {expr}")
        break  # 只显示一个字段的表达式

    # 测试复杂表达式生成
    print(f"\n=== 复杂表达式生成 ===")
    complex_exprs = generate_complex_expressions(simple_exprs, "cross_sectional_ops", 3)
    for field, field_exprs in complex_exprs.items():
        print(f"  {field}")
        for i, expr in enumerate(field_exprs[:3], 1):
            print(f"    {i}. {expr}")
        break  # 只显示一个字段的表达式

    # 测试volatility_adjusted表达式生成
    print(f"\n=== Volatility Adjusted 表达式生成 ===")
    vol_exprs = generate_complex_expressions(simple_exprs, "volatility_adjusted", 7)
    for field, field_exprs in vol_exprs.items():
        print(f"  {field}")
        for i, expr in enumerate(field_exprs, 1):
            print(f"    {i}. {expr}")
        break  # 只显示一个字段的表达式

    print(f"\n=== 所有表达式生成 ===")
    all_exprs = generate_all_expressions(processed_fields, None, 20)

    for field, templates in all_exprs.items():
        print(f"\n字段: {field}")
        for template, exprs in templates.items():
            print(f"  类型 '{template}': {len(exprs)} 个表达式")
            for i, expr in enumerate(exprs[:3], 1):  # 只显示前3个
                print(f"    {i}. {expr}")
        break  # 只显示一个字段的表达式


if __name__ == "__main__":
    main()