import random
from typing import List, Dict


class UnifiedAlphaGenerator:
    def __init__(self, alpha_data: List[Dict], fields: Dict[str, str]):
        self.alpha_data = alpha_data
        self.fields = fields
        self.categorized_ops = self._categorize_operators()
        self.all_templates = self._create_unified_templates()

    def _categorize_operators(self) -> Dict[str, List[str]]:
        """分类所有操作符"""
        return {
            "vector": ["vec_avg", "vec_sum", "vec_max", "vec_min", "vec_count"],
            "ts_trend": ["ts_returns", "ts_delta", "ts_moment", "ts_regression"],
            "ts_mean_reversion": ["ts_zscore", "ts_av_diff", "ts_scale", "ts_rank"],
            "ts_volatility": ["ts_std_dev", "ts_entropy"],
            "ts_extremes": ["ts_max", "ts_min", "ts_arg_max", "ts_arg_min"],
            "ts_backfill": ["ts_backfill"],  # 单独分类
            "cs_ranking": ["rank", "quantile", "scale"],
            "cs_normalization": ["zscore", "normalize", "winsorize"],
            "arithmetic": ["add", "subtract", "multiply", "divide"],
            "group_ops": ["group_neutralize", "group_rank", "group_zscore"]
        }

    def _create_unified_templates(self) -> Dict[str, Dict]:
        """创建统一的模板系统，包含所有类型"""

        # 基础模板（原有的）
        basic_templates = {
            # 动量策略
            "momentum": {
                "structure": "{ts_op}({field_expr}, {window})",
                "description": "动量因子",
                "category": "basic",
                "suitable_ts_ops": self.categorized_ops["ts_trend"],
                "suitable_windows": [5, 10, 20],
                "field_processing": self._process_field_by_type
            },

            # 均值回归策略
            "mean_reversion": {
                "structure": "{ts_op}({field_expr}, {window})",
                "description": "均值回归因子",
                "category": "basic",
                "suitable_ts_ops": ["ts_zscore", "ts_av_diff", "ts_rank"],
                "suitable_windows": [5, 10, 20],
                "field_processing": self._process_field_by_type
            },

            # 波动率调整因子
            "volatility_adjusted": {
                "structure": "divide({ts_op}({field_expr}, {window1}), ts_std_dev({field_expr}, {window2}))",
                "description": "波动率调整因子",
                "category": "basic",
                "suitable_ts_ops": ["ts_delta", "ts_returns", "ts_av_diff"],
                "suitable_windows_pairs": [(5, 10), (10, 20), (20, 20)],
                "field_processing": self._process_field_by_type
            },

            # 横截面因子
            "cross_sectional": {
                "structure": "{cs_op}({ts_op}({field_expr}, {window}))",
                "description": "横截面标准化因子",
                "category": "basic",
                "suitable_cs_ops": ["rank", "zscore", "scale"],
                "suitable_ts_ops": ["ts_returns", "ts_delta", "ts_zscore"],
                "suitable_windows": [5, 10, 20],
                "field_processing": self._process_field_by_type
            }
        }

        # 高级模板（原有的）
        advanced_templates = {
            # 残差动量因子
            "residual_momentum": {
                "structure": "ts_regression({field_y}, {field_x}, {window}, 0, 1)",
                "description": "残差动量因子",
                "category": "advanced",
                "suitable_windows": [10, 20, 60],
                "suitable_field_pairs": self._generate_field_pairs(),
                "field_processing": self._process_field_by_type
            },

            # 行业中性化因子
            "sector_neutral": {
                "structure": "group_neutralize({cs_op}({ts_op}({field_expr}, {window})), sector)",
                "description": "行业中性化因子",
                "category": "advanced",
                "suitable_cs_ops": ["rank", "zscore"],
                "suitable_ts_ops": ["ts_returns", "ts_delta"],
                "suitable_windows": [10, 20],
                "requires_group": True,
                "field_processing": self._process_field_by_type
            },

            # 质量因子 (多维度)
            "quality_factor": {
                "structure": "add({factor1}, {factor2}, {factor3})",
                "description": "多维度质量因子",
                "category": "advanced",
                "factor_types": ["profitability", "growth", "safety"],
                "field_processing": self._process_field_by_type
            }
        }

        # 新增的固定回填模板
        fixed_backfill_templates = {
            # 核心模板 - 固定 ts_backfill + winsorize，灵活的外层函数
            "fixed_backfill_core": {
                "structure": "{outer_ts_func}(winsorize(ts_backfill({field_expr}, {backfill_window}), std={std}), {outer_window})",
                "description": "固定回填+去极值+灵活外层函数",
                "category": "fixed_backfill",
                "fixed_components": ["ts_backfill", "winsorize"],
                "flexible_components": {
                    "outer_ts_func": ["ts_delta", "ts_returns", "ts_zscore", "ts_rank", "ts_scale",
                                      "ts_mean", "ts_std_dev", "ts_sum", "ts_min", "ts_max"]
                },
                "parameters": {
                    "std": [4, 3, 5],
                    "backfill_windows": [60, 120, 250],
                    "outer_windows": {
                        "common": [5, 10, 20, 60, 120, 240],
                        "function_specific": self._get_function_specific_windows()
                    }
                },
                "field_processing": self._process_field_by_type
            },

            # 变体：添加额外的中间处理层
            "fixed_backfill_with_middle": {
                "structure": "{outer_ts_func}({middle_func}(winsorize(ts_backfill({field_expr}, {backfill_window}), std={std})), {outer_window})",
                "description": "固定回填+去极值+中间处理+灵活外层函数",
                "category": "fixed_backfill",
                "fixed_components": ["ts_backfill", "winsorize"],
                "middle_functions": ["normalize", "purify", "pasteurize"],
                "flexible_components": {
                    "outer_ts_func": ["ts_delta", "ts_returns", "ts_zscore", "ts_rank"]
                },
                "parameters": {
                    "std": [4],
                    "backfill_windows": [120, 250],
                    "outer_windows": {
                        "common": [10, 20, 60, 120]
                    }
                },
                "field_processing": self._process_field_by_type
            },

            # 变体：横截面版本
            "fixed_backfill_cross_section": {
                "structure": "{cs_func}({outer_ts_func}(winsorize(ts_backfill({field_expr}, {backfill_window}), std={std}), {outer_window}))",
                "description": "固定回填+去极值+灵活外层函数+横截面处理",
                "category": "fixed_backfill",
                "fixed_components": ["ts_backfill", "winsorize"],
                "cross_section_funcs": ["rank", "zscore", "scale"],
                "flexible_components": {
                    "outer_ts_func": ["ts_delta", "ts_returns", "ts_zscore", "ts_rank"]
                },
                "parameters": {
                    "std": [4],
                    "backfill_windows": [120, 250],
                    "outer_windows": {
                        "common": [10, 20, 60, 120]
                    }
                },
                "field_processing": self._process_field_by_type
            }
        }

        # 合并所有模板
        return {**basic_templates, **advanced_templates, **fixed_backfill_templates}

    def _generate_field_pairs(self) -> List[tuple]:
        """生成有意义的字段对"""
        fields = list(self.fields.keys())
        pairs = []
        for f1 in fields:
            for f2 in fields:
                if f1 != f2:
                    pairs.append((f1, f2))
        return pairs[:10]

    def _get_function_specific_windows(self) -> Dict[str, List[int]]:
        """获取函数特定的窗口参数"""
        function_windows = {
            "ts_delta": [1, 5, 10, 20, 60, 120, 240],
            "ts_returns": [1, 5, 10, 20, 60],
            "ts_zscore": [20, 60, 120, 250],
            "ts_rank": [10, 20, 60, 120],
            "ts_scale": [20, 60, 120],
            "ts_mean": [5, 10, 20, 60, 120],
            "ts_std_dev": [20, 60, 120, 250],
            "ts_sum": [5, 10, 20, 60],
            "ts_min": [5, 10, 20, 60],
            "ts_max": [5, 10, 20, 60]
        }
        return function_windows

    def _process_field_by_type(self, field: str, field_type: str) -> str:
        """根据字段类型处理字段表达式"""
        if field_type == "VECTOR":
            vector_ops = ["vec_avg", "vec_sum", "vec_max"]
            return f"{random.choice(vector_ops)}({field})"
        else:
            return field

    def generate_by_template(self, template_name: str, max_expressions: int = 20) -> List[str]:
        """根据模板名称生成表达式"""
        if template_name not in self.all_templates:
            raise ValueError(f"未知模板: {template_name}")

        template = self.all_templates[template_name]
        expressions = []

        try:
            if template["category"] == "fixed_backfill":
                expressions = self._generate_fixed_backfill_template(template, max_expressions)
            elif template_name == "residual_momentum":
                expressions = self._generate_residual_template(template, max_expressions)
            elif template_name == "quality_factor":
                expressions = self._generate_quality_template(template, max_expressions)
            elif "volatility_adjusted" in template_name:
                expressions = self._generate_volatility_adjusted_template(template, max_expressions)
            elif "cross_sectional" in template_name:
                expressions = self._generate_cross_sectional_template(template, max_expressions)
            else:
                expressions = self._generate_basic_template(template, max_expressions)

        except Exception as e:
            print(f"生成模板 {template_name} 时出错: {e}")

        return expressions[:max_expressions]

    def _generate_fixed_backfill_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成固定回填模板表达式"""
        expressions = []
        fields = list(self.fields.keys())
        parameters = template["parameters"]
        outer_funcs = template["flexible_components"]["outer_ts_func"]

        for field in fields:
            field_type = self.fields[field]
            field_expr = template["field_processing"](field, field_type)

            for outer_func in outer_funcs[:5]:  # 限制函数数量
                # 获取适合该函数的窗口
                outer_windows = self._get_outer_windows(outer_func, parameters)

                for backfill_window in parameters["backfill_windows"]:
                    for outer_window in outer_windows[:2]:  # 每个函数使用前2个窗口
                        for std in parameters["std"]:
                            if len(expressions) >= max_expr:
                                return expressions

                            # 处理中间函数（如果存在）
                            middle_part = ""
                            if "middle_functions" in template:
                                middle_func = random.choice(template["middle_functions"][:2])
                                middle_part = f"{middle_func}("
                                closing_parens = "))"
                            else:
                                closing_parens = ")"

                            # 处理横截面函数（如果存在）
                            cs_part = ""
                            if "cross_section_funcs" in template:
                                cs_func = random.choice(template["cross_section_funcs"][:2])
                                cs_part = f"{cs_func}("
                                closing_parens = "))"

                            expr = template["structure"].format(
                                outer_ts_func=outer_func,
                                middle_func=middle_part if "middle_functions" in template else "",
                                cs_func=cs_part if "cross_section_funcs" in template else "",
                                field_expr=field_expr,
                                backfill_window=backfill_window,
                                std=std,
                                outer_window=outer_window
                            ) + closing_parens

                            expressions.append(expr)

        return expressions

    def _generate_basic_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成基础模板表达式"""
        expressions = []
        fields = list(self.fields.keys())

        for field in fields:
            field_type = self.fields[field]
            field_expr = template["field_processing"](field, field_type)

            for ts_op in template["suitable_ts_ops"][:3]:
                for window in template["suitable_windows"][:2]:
                    if len(expressions) >= max_expr:
                        return expressions

                    expr = template["structure"].format(
                        ts_op=ts_op,
                        field_expr=field_expr,
                        window=window
                    )
                    expressions.append(expr)

        return expressions

    def _generate_volatility_adjusted_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成波动率调整模板表达式"""
        expressions = []
        fields = list(self.fields.keys())

        for field in fields:
            field_type = self.fields[field]
            field_expr = template["field_processing"](field, field_type)

            for ts_op in template["suitable_ts_ops"][:2]:
                for window1, window2 in template["suitable_windows_pairs"][:2]:
                    if len(expressions) >= max_expr:
                        return expressions

                    expr = template["structure"].format(
                        ts_op=ts_op,
                        field_expr=field_expr,
                        window1=window1,
                        window2=window2
                    )
                    expressions.append(expr)

        return expressions

    def _generate_cross_sectional_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成横截面模板表达式"""
        expressions = []
        fields = list(self.fields.keys())

        for field in fields:
            field_type = self.fields[field]
            field_expr = template["field_processing"](field, field_type)

            for cs_op in template["suitable_cs_ops"][:2]:
                for ts_op in template["suitable_ts_ops"][:2]:
                    for window in template["suitable_windows"][:2]:
                        if len(expressions) >= max_expr:
                            return expressions

                        expr = template["structure"].format(
                            cs_op=cs_op,
                            ts_op=ts_op,
                            field_expr=field_expr,
                            window=window
                        )
                        expressions.append(expr)

        return expressions

    def _generate_residual_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成残差模板表达式"""
        expressions = []

        for field1, field2 in template["suitable_field_pairs"][:max_expr]:
            for window in template["suitable_windows"]:
                expr = template["structure"].format(
                    field_y=field1, field_x=field2, window=window
                )
                expressions.append(expr)

        return expressions

    def _generate_quality_template(self, template: Dict, max_expr: int) -> List[str]:
        """生成质量因子模板表达式"""
        expressions = []
        fields = list(self.fields.keys())

        # 简化版本：使用3个不同的字段组合
        for i in range(min(max_expr, len(fields) // 3)):
            if i * 3 + 2 < len(fields):
                factor1 = fields[i * 3]
                factor2 = fields[i * 3 + 1]
                factor3 = fields[i * 3 + 2]

                expr = template["structure"].format(
                    factor1=factor1, factor2=factor2, factor3=factor3
                )
                expressions.append(expr)

        return expressions

    def _get_outer_windows(self, outer_func: str, parameters: Dict) -> List[int]:
        """获取外层函数的合适窗口"""
        if "function_specific" in parameters["outer_windows"]:
            func_specific = parameters["outer_windows"]["function_specific"]
            if outer_func in func_specific:
                return func_specific[outer_func]

        return parameters["outer_windows"]["common"]

    def generate_diverse_expressions(self, count: int = 30,
                                     include_categories: List[str] = None) -> List[str]:
        """生成多样化的表达式集合"""
        if include_categories is None:
            include_categories = ["basic", "advanced", "fixed_backfill"]

        expressions = []

        # 按类别分组模板
        templates_by_category = {}
        for name, template in self.all_templates.items():
            category = template["category"]
            if category in include_categories:
                if category not in templates_by_category:
                    templates_by_category[category] = []
                templates_by_category[category].append(name)

        # 为每个类别分配大致相等的数量
        for category, template_names in templates_by_category.items():
            per_template = max(2, count // (len(templates_by_category) * len(template_names)))

            for template_name in template_names:
                try:
                    template_exprs = self.generate_by_template(template_name, per_template)
                    expressions.extend(template_exprs)
                    print(f"模板 '{template_name}' 生成 {len(template_exprs)} 个表达式")
                except Exception as e:
                    print(f"模板 '{template_name}' 生成失败: {e}")
                    continue

        # 如果数量不够，补充简单表达式
        if len(expressions) < count:
            additional = self._generate_simple_expressions(count - len(expressions))
            expressions.extend(additional)

        return expressions[:count]

    def _generate_simple_expressions(self, count: int) -> List[str]:
        """生成简单的备用表达式"""
        expressions = []
        fields = list(self.fields.keys())
        templates = [
            "ts_returns({field}, {window})",
            "ts_delta({field}, {window})",
            "ts_zscore({field}, {window})",
            "rank({field})"
        ]
        windows = [5, 10, 20]

        for _ in range(count):
            template = random.choice(templates)
            field = random.choice(fields)
            if "{window}" in template:
                window = random.choice(windows)
                expr = template.format(field=field, window=window)
            else:
                expr = template.format(field=field)
            expressions.append(expr)

        return expressions

    def get_template_categories(self) -> List[str]:
        """获取所有模板类别"""
        categories = set()
        for template in self.all_templates.values():
            categories.add(template["category"])
        return list(categories)

    def get_templates_by_category(self, category: str) -> List[str]:
        """按类别获取模板名称"""
        return [name for name, template in self.all_templates.items()
                if template["category"] == category]


# 使用示例
def main():
    fields = {
        'anl11_1e': 'MATRIX',
        'anl11_1g': 'MATRIX',
        'anl11_1pme': 'VECTOR',
        'anl11_1tic': 'MATRIX',
        'anl11_2e': 'MATRIX',
        'anl11_2g': 'VECTOR',
        'anl11_2pme': 'MATRIX',
        'snt22dts_sop': 'MATRIX',
        'snt22_2dts_sop_7': 'MATRIX'
    }

    generator = UnifiedAlphaGenerator([], fields)

    print("=== 统一模板系统 ===")
    print(f"模板类别: {', '.join(generator.get_template_categories())}")

    # 显示每个类别的模板
    for category in generator.get_template_categories():
        templates = generator.get_templates_by_category(category)
        print(f"\n{category} 类别模板:")
        for template in templates:
            desc = generator.all_templates[template]["description"]
            print(f"  - {template}: {desc}")

    # 测试各类别模板
    print(f"\n=== 各类别模板测试 ===")

    # 基础模板测试
    basic_templates = generator.get_templates_by_category("basic")[:2]
    for template_name in basic_templates:
        print(f"\n{template_name} 表达式:")
        exprs = generator.generate_by_template(template_name, 3)
        for i, expr in enumerate(exprs, 1):
            print(f"  {i}. {expr}")

    # 高级模板测试
    advanced_templates = generator.get_templates_by_category("advanced")[:1]
    for template_name in advanced_templates:
        print(f"\n{template_name} 表达式:")
        exprs = generator.generate_by_template(template_name, 3)
        for i, expr in enumerate(exprs, 1):
            print(f"  {i}. {expr}")

    # 固定回填模板测试
    fixed_templates = generator.get_templates_by_category("fixed_backfill")[:2]
    for template_name in fixed_templates:
        print(f"\n{template_name} 表达式:")
        exprs = generator.generate_by_template(template_name, 3)
        for i, expr in enumerate(exprs, 1):
            print(f"  {i}. {expr}")

    print(f"\n=== 多样化表达式生成 ===")
    diverse_exprs = generator.generate_diverse_expressions(25)
    print(f"生成 {len(diverse_exprs)} 个多样化表达式")

    # 按模板类别显示示例
    print("\n各类别表达式示例:")
    category_examples = {}
    for expr in diverse_exprs:
        for template_name, template in generator.all_templates.items():
            if template["category"] not in category_examples:
                category_examples[template["category"]] = []
            if len(category_examples[template["category"]]) < 2:
                # 简单匹配：检查是否包含该模板的特征
                if "ts_backfill" in expr and template["category"] == "fixed_backfill":
                    category_examples[template["category"]].append(expr)
                    break
                elif "ts_regression" in expr and template_name == "residual_momentum":
                    category_examples[template["category"]].append(expr)
                    break
                elif "group_neutralize" in expr and template_name == "sector_neutral":
                    category_examples[template["category"]].append(expr)
                    break

    for category, examples in category_examples.items():
        print(f"\n{category} 示例:")
        for expr in examples:
            print(f"  - {expr}")


if __name__ == "__main__":
    # 按模板名称生成
    # exprs = generator.generate_by_template("momentum", 10)

    # 按类别生成多样化表达式
    # exprs = generator.generate_diverse_expressions(30, ["basic", "fixed_backfill"])
    main()