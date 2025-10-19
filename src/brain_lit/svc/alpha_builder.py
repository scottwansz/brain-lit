import random
from typing import List, Dict
from itertools import combinations


class AlphaGenerator:
    def __init__(self, fields: Dict[str, Dict]):
        """
        Args:
            alpha_data: Alpha操作符数据
            fields: 字段信息字典，格式为 {'field_name': {'type': 'MATRIX', 'coverage': 0.58}, ...}
        """
        self.fields = fields
        self.processed_fields = self._process_all_fields()
        self.categorized_ops = self._categorize_operators()
        self.all_templates = self._create_optimized_templates()

        # 固定的回填窗口选项
        self.backfill_windows = [5, 10, 20, 60, 120, 250]

    def _categorize_operators(self) -> Dict[str, List[str]]:
        """分类操作符"""
        return {
            "vector": ["vec_avg", "vec_sum", "vec_max", "vec_min"],
            "ts_trend": ["ts_returns", "ts_delta", "ts_moment", "ts_regression"],
            "ts_mean_reversion": ["ts_zscore", "ts_av_diff", "ts_scale", "ts_rank"],
            "ts_volatility": ["ts_std_dev", "ts_entropy"],
            "ts_backfill": ["ts_backfill", "kth_element", "group_backfill"],
            "coverage_handling": ["ts_backfill", "kth_element", "group_backfill", "is_nan", "days_from_last_change"],
            "outlier_handling": ["winsorize", "truncate", "rank", "zscore", "normalize", "scale"],
            "group_ops": ["group_neutralize", "group_rank", "group_zscore"]
        }

    def _create_optimized_templates(self) -> Dict[str, Dict]:
        """创建优化后的模板系统"""

        # 基础模板
        basic_templates = {
            "momentum": {
                "structure": "{ts_op}({field_expr}, {window})",
                "description": "动量因子",
                "category": "basic",
                "suitable_ts_ops": self.categorized_ops["ts_trend"],
                "suitable_windows": [5, 10, 20]
            },

            "mean_reversion": {
                "structure": "{ts_op}({field_expr}, {window})",
                "description": "均值回归因子",
                "category": "basic",
                "suitable_ts_ops": ["ts_zscore", "ts_av_diff", "ts_rank"],
                "suitable_windows": [5, 10, 20]
            },

            "volatility_adjusted": {
                "structure": "divide({ts_op}({field_expr}, {window1}), ts_std_dev({field_expr}, {window2}))",
                "description": "波动率调整因子",
                "category": "basic",
                "suitable_ts_ops": ["ts_delta", "ts_returns", "ts_av_diff"],
                "suitable_windows_pairs": [(5, 10), (10, 20), (20, 20)]
            },

            "cross_sectional": {
                "structure": "{cs_op}({ts_op}({field_expr}, {window}))",
                "description": "横截面标准化因子",
                "category": "basic",
                "suitable_cs_ops": ["rank", "zscore", "scale"],
                "suitable_ts_ops": ["ts_returns", "ts_delta", "ts_zscore"],
                "suitable_windows": [5, 10, 20]
            }
        }

        # 高级模板
        advanced_templates = {
            "residual_momentum": {
                "structure": "ts_regression({field_y}, {field_x}, {window}, 0, 1)",
                "description": "残差动量因子",
                "category": "advanced",
                "suitable_windows": [10, 20, 60]
            },

            "coverage_conditional": {
                "structure": "group_count(is_nan({field_expr}), market) > 40 ? {field_expr} : nan",
                "description": "覆盖率条件因子（检测异常下降）",
                "category": "advanced"
            },

            "sector_neutral_robust": {
                "structure": "group_neutralize(rank(winsorize({ts_op}({field_expr}, {window}), std=4)), sector)",
                "description": "稳健行业中性因子",
                "category": "advanced",
                "suitable_ts_ops": ["ts_returns", "ts_delta", "ts_zscore"],
                "suitable_windows": [10, 20]
            },

            "distribution_normalized": {
                "structure": "scale(rank({ts_op}({field_expr}, {window})), longscale=0.8, shortscale=0.8)",
                "description": "分布标准化因子（控制多头空头权重）",
                "category": "advanced",
                "suitable_ts_ops": ["ts_returns", "ts_delta", "ts_zscore"],
                "suitable_windows": [5, 10, 20]
            },

            "robust_momentum": {
                "structure": "winsorize(rank({ts_op}({field_expr}, {window})), std=4)",
                "description": "稳健动量因子（异常值处理+排名）",
                "category": "advanced",
                "suitable_ts_ops": ["ts_returns", "ts_delta", "ts_zscore"],
                "suitable_windows": [5, 10, 20]
            }
        }

        return {**basic_templates, **advanced_templates}

    def _process_all_fields(self) -> Dict[str, str]:
        """
        在构造函数中预处理所有字段，避免在模板中重复处理
        """
        processed = {}
        for field, field_info in self.fields.items():
            processed[field] = self._process_field_by_coverage(field, field_info)
        return processed

    def _process_field_by_coverage(self, field: str, field_info: Dict) -> str:
        """
        根据字段覆盖率和类型处理字段表达式
        使用固定的回填窗口选项 [5, 10, 20, 60, 120, 250]
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
        available_windows = [5, 10, 20, 60, 120, 250]
        backfill_window = next((w for w in available_windows if w > missing_days), 250)

        field_expr = f"ts_backfill({field_expr}, {backfill_window})"

        return field_expr

    def get_fields_by_coverage(self, min_coverage: float = None, max_coverage: float = None) -> List[str]:
        """根据覆盖率获取字段"""
        fields = []
        for field, info in self.fields.items():
            coverage = info.get('coverage', 1.0)
            if min_coverage is not None and coverage < min_coverage:
                continue
            if max_coverage is not None and coverage > max_coverage:
                continue
            fields.append(field)
        return fields

    def generate_by_template(self, template_name: str, max_expressions: int = 20) -> Dict[str, List[str]]:
        """根据模板名称生成表达式"""
        if template_name not in self.all_templates:
            raise ValueError(f"未知模板: {template_name}")

        template = self.all_templates[template_name]
        expressions = {}
        
        # 根据模板的覆盖率要求筛选字段
        min_coverage = template.get('min_coverage')
        max_coverage = template.get('max_coverage')
        suitable_fields = self.get_fields_by_coverage(min_coverage, max_coverage)

        if not suitable_fields:
            print(f"模板 {template_name} 没有找到合适的字段（覆盖率要求: min={min_coverage}, max={max_coverage}）")
            return expressions

        try:
            if template_name == "residual_momentum":
                expressions = self._generate_residual_template_with_fields(template, suitable_fields, max_expressions)
            elif template_name == "robust_momentum":
                expressions = self._generate_robust_momentum_template_with_fields(template, suitable_fields, max_expressions)
            elif template_name == "coverage_conditional":
                expressions = self._generate_coverage_conditional_template_with_fields(template, suitable_fields, max_expressions)
            elif "volatility_adjusted" in template_name:
                expressions = self._generate_volatility_adjusted_template_with_fields(template, suitable_fields, max_expressions)
            elif "cross_sectional" in template_name:
                expressions = self._generate_cross_sectional_template_with_fields(template, suitable_fields, max_expressions)
            else:
                expressions = self._generate_basic_template_with_fields(template, suitable_fields, max_expressions)

        except Exception as e:
            print(f"生成模板 {template_name} 时出错: {e}")

        return expressions

    def _generate_basic_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成基础模板表达式，返回带字段信息的结构"""
        expressions = {}

        for field in fields:
            field_info = self.fields[field]
            field_expr = self.processed_fields[field]
            expressions[field] = []

            for ts_op in template["suitable_ts_ops"]:
                if "suitable_windows" in template:
                    for window in template["suitable_windows"]:
                        if len(expressions[field]) >= max_expr:
                            break
                        expr = template["structure"].format(
                            ts_op=ts_op, field_expr=field_expr, window=window
                        )
                        expressions[field].append(expr)
                elif "suitable_windows_pairs" in template:
                    for window1, window2 in template["suitable_windows_pairs"]:
                        if len(expressions[field]) >= max_expr:
                            break
                        expr = template["structure"].format(
                            ts_op=ts_op, field_expr=field_expr, window1=window1, window2=window2
                        )
                        expressions[field].append(expr)

        return expressions

    def _generate_cross_sectional_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成横截面模板表达式，返回带字段信息的结构"""
        expressions = {}

        for field in fields:
            field_info = self.fields[field]
            field_expr = self.processed_fields[field]
            expressions[field] = []

            for cs_op in template["suitable_cs_ops"]:
                for ts_op in template["suitable_ts_ops"]:
                    for window in template["suitable_windows"]:
                        if len(expressions[field]) >= max_expr:
                            break

                        expr = template["structure"].format(
                            cs_op=cs_op,
                            ts_op=ts_op,
                            field_expr=field_expr,
                            window=window
                        )
                        expressions[field].append(expr)

        return expressions

    def _generate_volatility_adjusted_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成波动率调整模板表达式，返回带字段信息的结构"""
        expressions = {}

        for field in fields:
            field_info = self.fields[field]
            field_expr = self.processed_fields[field]
            expressions[field] = []

            for ts_op in template["suitable_ts_ops"]:
                for window1, window2 in template["suitable_windows_pairs"]:
                    if len(expressions[field]) >= max_expr:
                        break

                    expr = template["structure"].format(
                        ts_op=ts_op, field_expr=field_expr, window1=window1, window2=window2
                    )
                    expressions[field].append(expr)

        return expressions

    def _generate_residual_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成残差模板表达式，返回带字段信息的结构"""
        expressions = {}

        # 直接生成字段对
        field_pairs = list(combinations(self.fields.keys(), 2))

        for field_pair in field_pairs:
            if len(field_pair) >= 2:
                field1, field2 = field_pair[0], field_pair[1]
            else:
                continue
                
            # 处理两个字段
            field1_info = self.fields.get(field1, {})
            field2_info = self.fields.get(field2, {})
            
            # 如果字段不存在，跳过
            if not field1_info or not field2_info:
                continue
                
            field1_expr = self.processed_fields[field1]
            field2_expr = self.processed_fields[field2]
            
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

    def _generate_robust_momentum_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成稳健动量模板表达式，返回带字段信息的结构"""
        expressions = {}

        for field in fields:
            field_info = self.fields[field]
            field_expr = self.processed_fields[field]
            expressions[field] = []

            # 处理适合的时间序列操作和窗口
            suitable_ts_ops = template.get("suitable_ts_ops", ["ts_returns"])
            suitable_windows = template.get("suitable_windows", [5, 10, 20])
            
            for ts_op in suitable_ts_ops:
                for window in suitable_windows:
                    if len(expressions[field]) >= max_expr:
                        break
                        
                    expr = template["structure"].format(
                        ts_op=ts_op, field_expr=field_expr, window=window
                    )
                    expressions[field].append(expr)

        return expressions

    def _generate_coverage_conditional_template_with_fields(self, template: Dict, fields: List[str], max_expr: int) -> Dict[str, List[str]]:
        """生成覆盖率条件模板表达式，返回带字段信息的结构"""
        expressions = {}

        for field in fields:
            field_info = self.fields[field]
            field_expr = self.processed_fields[field]
            
            if field not in expressions:
                expressions[field] = []

            expr = template["structure"].format(field_expr=field_expr)
            expressions[field].append(expr)

        return expressions

    def generate_diverse_expressions(self, count: int = 30) -> List[str]:
        """生成多样化的表达式集合"""
        expressions = []

        # 按模板类别分配数量
        basic_templates = [name for name, template in self.all_templates.items()
                           if template["category"] == "basic"]
        advanced_templates = [name for name, template in self.all_templates.items()
                              if template["category"] == "advanced"]

        templates_count = len(basic_templates) + len(advanced_templates)
        per_template = max(5, count // templates_count)  # 增加每个模板的表达式数量

        # 生成基础模板表达式
        for template_name in basic_templates:
            if len(expressions) >= count:
                break
            template_exprs = self.generate_by_template(template_name, per_template)
            print(f"基础模板 '{template_name}' 生成 {len(template_exprs)} 个表达式")
            # 修复：从返回的字典中提取表达式
            for field_exprs in template_exprs.values():
                expressions.extend(field_exprs)

        # 生成高级模板表达式
        for template_name in advanced_templates:
            if len(expressions) >= count:
                break
            template_exprs = self.generate_by_template(template_name, per_template)
            print(f"高级模板 '{template_name}' 生成 {len(template_exprs)} 个表达式")
            # 修复：从返回的字典中提取表达式
            for field_exprs in template_exprs.values():
                expressions.extend(field_exprs)

        # 如果数量不够，补充简单表达式
        if len(expressions) < count:
            additional = self._generate_simple_expressions(count - len(expressions))
            expressions.extend(additional)

        return expressions[:count]

    def generate_diverse_expressions_by_field(self, count: int = 30) -> Dict[str, Dict[str, List[str]]]:
        """生成多样化的表达式集合，按字段和模板组织"""
        all_expressions = {}

        # 按模板类别分配数量
        basic_templates = [name for name, template in self.all_templates.items()
                           if template["category"] == "basic"]
        advanced_templates = [name for name, template in self.all_templates.items()
                              if template["category"] == "advanced"]

        templates_count = len(basic_templates) + len(advanced_templates)
        per_template = max(5, count // templates_count)  # 增加每个模板的表达式数量

        # 生成基础模板表达式
        for template_name in basic_templates:
            template_exprs = self.generate_by_template(template_name, per_template)
            # 合并到all_expressions中
            for field, exprs in template_exprs.items():
                if field not in all_expressions:
                    all_expressions[field] = {}
                all_expressions[field][template_name] = exprs

        # 生成高级模板表达式
        for template_name in advanced_templates:
            template_exprs = self.generate_by_template(template_name, per_template)
            # 合并到all_expressions中
            for field, exprs in template_exprs.items():
                if field not in all_expressions:
                    all_expressions[field] = {}
                all_expressions[field][template_name] = exprs

        return all_expressions

    def _generate_simple_expressions(self, count: int) -> List[str]:
        """生成简单的备用表达式"""
        expressions = []
        fields = list(self.fields.keys())

        for field in fields:
            if len(expressions) >= count:
                break

            field_info = self.fields[field]
            coverage = field_info.get('coverage', 1.0)
            # 使用新的计算方式选择回填窗口
            update_frequency = 250 * (1 - coverage)
            available_windows = [5, 10, 20, 60, 120, 250]
            backfill_window = next((w for w in available_windows if w > update_frequency), 250)

            if field_info['type'] == "VECTOR":
                expr = f"ts_returns(ts_backfill(vec_avg({field}), {backfill_window}), 10)"
            else:
                expr = f"ts_returns(ts_backfill({field}, {backfill_window}), 10)"
            expressions.append(expr)

        return expressions

    def analyze_field_coverage(self) -> Dict:
        """分析字段覆盖率"""
        coverage_stats = {
            "total_fields": len(self.fields),
            "field_details": {},
            "window_options": self.backfill_windows
        }

        for field, info in self.fields.items():
            coverage = info.get('coverage', 1.0)
            # 使用新的计算方式选择回填窗口
            # 计算数据缺失天数：250*(1-覆盖率)
            missing_days = 250 * (1 - coverage)
            available_windows = [5, 10, 20, 60, 120, 250]
            backfill_window = next((w for w in available_windows if w > missing_days), 250)
            
            coverage_stats["field_details"][field] = {
                "type": info['type'],
                "coverage": coverage,
                "backfill_window": backfill_window
            }

        return coverage_stats

    def get_coverage_advice(self) -> str:
        """获取覆盖率处理建议"""
        stats = self.analyze_field_coverage()
        advice = []

        advice.append("=== 覆盖率处理建议 ===")
        advice.append(f"字段总数: {stats['total_fields']}")

        advice.append(f"\n可用回填窗口: {self.backfill_windows}")
        advice.append("\n回填策略:")
        advice.append("  - 根据公式 250*(1-覆盖率) 计算数据缺失天数")
        advice.append("  - 从 [5, 10, 20, 60, 120, 250] 中选择大于数据缺失天数的最小窗口")
        advice.append("  - 覆盖率越高，(1-覆盖率)越小，数据缺失天数越少，所选窗口越短")
        advice.append("  - 覆盖率越低，(1-覆盖率)越大，数据缺失天数越多，所选窗口越长")

        return "\n".join(advice)

    def get_window_usage_stats(self, expressions: List[str]) -> Dict:
        """统计回填窗口使用情况"""
        import re
        window_stats = {str(window): 0 for window in self.backfill_windows}

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

    generator = AlphaGenerator(fields)

    print("=== 固定窗口覆盖率感知Alpha表达式生成器 ===")

    # 显示覆盖率建议
    advice = generator.get_coverage_advice()
    print(advice)

    # 分析字段覆盖率
    coverage_stats = generator.analyze_field_coverage()
    print(f"\n=== 字段详情 ===")
    for field, info in coverage_stats["field_details"].items():
        print(f"  {field}: {info['type']}, 覆盖率={info['coverage']:.2f}, "
              f"回填窗口={info['backfill_window']}")

    # 测试不同模板
    print(f"\n=== 模板测试 ===")

    # 基础模板测试
    basic_templates = ["momentum", "mean_reversion", "volatility_adjusted", "cross_sectional"]
    for template_name in basic_templates[:2]:
        print(f"\n{template_name} 表达式:")
        exprs = generator.generate_by_template(template_name, 3)
        for field, field_exprs in exprs.items():
            print(f"  {field}")
            for i, expr in enumerate(field_exprs[:3], 1):
                print(f"    {i}. {expr}")

    # 高级模板测试
    advanced_templates = ["residual_momentum", "robust_momentum"]
    for template_name in advanced_templates[:2]:
        print(f"\n{template_name} 表达式:")
        exprs = generator.generate_by_template(template_name, 3)
        for field, field_exprs in exprs.items():
            print(f"  {field}")
            for i, expr in enumerate(field_exprs[:3], 1):
                print(f"    {i}. {expr}")

    print(f"\n=== 多样化表达式生成 ===")
    diverse_exprs = generator.generate_diverse_expressions(20)
    diverse_exprs_by_field = generator.generate_diverse_expressions_by_field(20)
    print(f"生成 {len(diverse_exprs)} 个多样化表达式")
    
    # 显示按字段和模板组织的表达式
    print("\n=== 按字段和模板组织的表达式 ===")
    for field, templates in diverse_exprs_by_field.items():
        print(f"\n字段: {field}")
        for template, exprs in templates.items():
            print(f"  模板 '{template}': {len(exprs)} 个表达式")
            for i, expr in enumerate(exprs[:3], 1):  # 只显示前3个
                print(f"    {i}. {expr}")

    # 统计窗口使用情况
    window_stats = generator.get_window_usage_stats(diverse_exprs)
    print(f"\n回填窗口使用统计:")
    for window, count in window_stats.items():
        if count > 0:
            print(f"  窗口 {window}天: {count} 次")

    # 显示一些示例
    print("\n示例表达式:")
    sample_expressions = diverse_exprs[:6] if isinstance(diverse_exprs, list) else list(diverse_exprs.keys())[:6]
    for i, expr in enumerate(sample_expressions, 1):
        print(f"  {i}. {expr}")


if __name__ == "__main__":
    main()