import json
from datetime import datetime
from typing import Dict, Tuple, List, Union


class SentimentAlphaGeneratorV5:
    """
    第五代情感数据Alpha表达式生成器
    完整生成所有可能的Alpha表达式，支持行业中性化
    """

    def __init__(self, field_metadata: Dict = None):
        """
        初始化生成器

        Args:
            field_metadata: 字段元数据
        """
        self.field_metadata = field_metadata or {}
        self.grouped_data, self.group_stats = self._group_fields()
        self._initialize_operators()
        self._initialize_strategy_templates()
        self._initialize_group_fields()

        print(f"字段分组完成: {self.group_stats['groups_created']} 个组, "
              f"{self.group_stats['groups_complete']} 个完整组")

    def _parse_field_name(self, field_name: str) -> Tuple[str, str, str, str]:
        """解析字段名"""
        parts = field_name.split('_')

        if len(parts) < 3:
            return None, None, None, None

        prefix = parts[0]
        window = None
        sentiment = None
        stat_type = None

        second_part = parts[1]

        # 带窗口数字
        if second_part and second_part[0].isdigit():
            window_digits = ''
            for char in second_part:
                if char.isdigit():
                    window_digits += char
                else:
                    break

            if window_digits:
                window = window_digits
                remaining = second_part[len(window_digits):]
                if remaining in ['neg', 'neut', 'pos']:
                    sentiment = remaining

                if len(parts) >= 3:
                    if len(parts) == 4 and parts[2] == 'conf':
                        stat_type = f"{parts[2]}_{parts[3]}"
                    else:
                        stat_type = '_'.join(parts[2:])

        # 基础窗口
        elif second_part in ['neg', 'neut', 'pos']:
            window = 'base'
            sentiment = second_part
            stat_type = '_'.join(parts[2:]) if len(parts) > 2 else None

        return prefix, window, sentiment, stat_type

    def _group_fields(self) -> Tuple[Dict, Dict]:
        """将字段分组"""
        grouped_data = {}
        stats = {
            "total_fields": len(self.field_metadata),
            "grouped_fields": 0,
            "groups_created": 0,
            "groups_complete": 0,
            "groups_partial": 0,
            "unmatched_fields": 0,
        }

        field_info = {}
        for field_id in self.field_metadata.keys():
            try:
                prefix, window, sentiment, stat_type = self._parse_field_name(field_id)

                if not (prefix and window and sentiment and stat_type):
                    continue

                field_info[field_id] = {
                    "prefix": prefix,
                    "window": window,
                    "sentiment": sentiment,
                    "stat_type": stat_type
                }

            except Exception:
                continue

        # 按组分类
        temp_groups = {}
        for field_id, info in field_info.items():
            prefix = info["prefix"]
            window = info["window"]
            sentiment = info["sentiment"]
            stat_type = info["stat_type"]

            if window == 'base':
                group_key = f"{prefix}_sentiment_{stat_type}"
            else:
                group_key = f"{prefix}_{window}sentiment_{stat_type}"

            if group_key not in temp_groups:
                temp_groups[group_key] = {}

            temp_groups[group_key][sentiment] = field_id
            stats["grouped_fields"] += 1

        # 整理分组数据
        for group_key, sentiment_dict in temp_groups.items():
            grouped_data[group_key] = {
                "fields": sentiment_dict,
                "info": self._analyze_group(group_key, sentiment_dict)
            }
            stats["groups_created"] += 1

            if len(sentiment_dict) == 3:
                stats["groups_complete"] += 1
            else:
                stats["groups_partial"] += 1

        stats["unmatched_fields"] = stats["total_fields"] - stats["grouped_fields"]

        return grouped_data, stats

    def _analyze_group(self, group_key: str, fields_dict: Dict) -> Dict:
        """分析组的信息"""
        parts = group_key.split('_')

        info = {
            "prefix": parts[0],
            "has_window": False,
            "window": None,
            "stat_type": None,
            "is_complete": len(fields_dict) == 3,
            "available_sentiments": list(fields_dict.keys()),
            "missing_sentiments": []
        }

        if len(parts) >= 2:
            second_part = parts[1]
            if second_part.endswith('sentiment'):
                window_part = second_part.replace('sentiment', '')
                if window_part.isdigit():
                    info["has_window"] = True
                    info["window"] = window_part

        if len(parts) >= 3:
            info["stat_type"] = '_'.join(parts[2:])

        all_sentiments = ['neg', 'neut', 'pos']
        info["missing_sentiments"] = [s for s in all_sentiments if s not in fields_dict]

        return info

    def _initialize_operators(self):
        """初始化算子库"""
        self.operators = {
            "arithmetic": {
                "add": "加法",
                "subtract": "减法",
                "multiply": "乘法",
                "divide": "除法",
                "power": "幂运算",
                "sqrt": "平方根",
                "abs": "绝对值",
                "log": "对数",
                "signed_power": "带符号幂",
                "inverse": "倒数",
                "reverse": "取反"
            },
            "timeseries": {
                "ts_mean": "时间序列均值",
                "ts_std_dev": "时间序列标准差",
                "ts_zscore": "时间序列Z-score",
                "ts_rank": "时间序列排名",
                "ts_delay": "时间序列延迟",
                "ts_delta": "时间序列差分",
                "ts_returns": "时间序列收益率",
                "ts_sum": "时间序列求和",
                "ts_max": "时间序列最大值",
                "ts_min": "时间序列最小值",
                "ts_corr": "时间序列相关性",
                "ts_covariance": "时间序列协方差",
                "ts_decay_linear": "线性衰减",
                "ts_decay_exp_window": "指数衰减",
                "ts_weighted_decay": "加权衰减"
            },
            "cross_sectional": {
                "zscore": "截面Z-score",
                "rank": "截面排名",
                "winsorize": "缩尾处理",
                "scale": "缩放",
                "normalize": "标准化",
                "quantile": "分位数"
            },
            "group": {
                "group_neutralize": "分组中性化",
                "group_zscore": "分组Z-score",
                "group_rank": "分组排名",
                "group_mean": "分组均值",
                "group_std_dev": "分组标准差"
            },
            "transformational": {
                "hump_decay": "驼峰衰减",
                "jump_decay": "跳跃衰减",
                "trade_when": "条件交易",
                "tail": "尾部处理",
                "right_tail": "右尾处理",
                "left_tail": "左尾处理",
                "hump": "驼峰",
                "nan_out": "NaN替换"
            }
        }

    def _initialize_strategy_templates(self):
        """初始化策略模板"""
        self.strategy_templates = {
            # 基础策略
            "net_sentiment": {
                "description": "净情绪策略：正面情绪 - 负面情绪",
                "template": "subtract({pos}, {neg})",
                "required_sentiments": ["pos", "neg"],
                "category": "basic"
            },
            "sentiment_ratio": {
                "description": "情绪比率策略：正面情绪 / (正面情绪 + 负面情绪)",
                "template": "divide({pos}, add({pos}, {neg}))",
                "required_sentiments": ["pos", "neg"],
                "category": "basic"
            },
            "sentiment_difference": {
                "description": "情绪差异策略：(正面情绪 - 负面情绪) / (正面情绪 + 负面情绪)",
                "template": "divide(subtract({pos}, {neg}), add({pos}, {neg}))",
                "required_sentiments": ["pos", "neg"],
                "category": "basic"
            },

            # 复合策略
            "composite_sentiment": {
                "description": "复合情绪策略：加权组合三种情绪",
                "template": "add(multiply({pos}, 1.5), add(multiply({neg}, -1.2), multiply({neut}, -0.3)))",
                "required_sentiments": ["pos", "neg", "neut"],
                "category": "composite"
            },
            "weighted_composite": {
                "description": "加权复合策略：自定义权重的情绪组合",
                "template": "add(multiply({pos}, {pos_weight}), add(multiply({neg}, {neg_weight}), multiply({neut}, {neut_weight})))",
                "required_sentiments": ["pos", "neg", "neut"],
                "parameters": {"pos_weight": 1.5, "neg_weight": -1.2, "neut_weight": -0.3},
                "category": "composite"
            },

            # 偏差策略
            "pos_neut_deviation": {
                "description": "正面-中性偏差策略：正面情绪 - 中性情绪",
                "template": "subtract({pos}, {neut})",
                "required_sentiments": ["pos", "neut"],
                "category": "deviation"
            },
            "neg_neut_deviation": {
                "description": "负面-中性偏差策略：负面情绪 - 中性情绪",
                "template": "subtract({neg}, {neut})",
                "required_sentiments": ["neg", "neut"],
                "category": "deviation"
            },

            # 波动率调整策略
            "volatility_adjusted_pos": {
                "description": "波动率调整正面情绪：正面情绪 / 正面情绪标准差",
                "template": "divide({pos_mean}, {pos_std})",
                "required_sentiments": ["pos_mean", "pos_std"],
                "category": "volatility"
            },
            "volatility_adjusted_net": {
                "description": "波动率调整净情绪：净情绪 / 情绪波动率",
                "template": "divide(subtract({pos_mean}, {neg_mean}), add({pos_std}, {neg_std}))",
                "required_sentiments": ["pos_mean", "neg_mean", "pos_std", "neg_std"],
                "category": "volatility"
            },

            # 时间序列策略
            "ts_momentum_net": {
                "description": "时间序列动量策略：净情绪的时间序列变化",
                "template": "ts_returns(subtract({pos}, {neg}), d={lookback}, mode=1)",
                "required_sentiments": ["pos", "neg"],
                "parameters": {"lookback": 3},
                "category": "momentum"
            },
            "ts_zscore_sentiment": {
                "description": "时间序列Z-score策略：情绪的Z-score",
                "template": "ts_zscore({sentiment}, d={lookback})",
                "required_sentiments": ["sentiment"],
                "parameters": {"sentiment": "pos", "lookback": 10},
                "category": "momentum"
            },

            # 反转策略
            "extreme_reversal": {
                "description": "极端反转策略：置信区间判断极端情绪",
                "template": "if_else(greater({pos_conf_low}, {pos_threshold}), -1, if_else(less({neg_conf_up}, {neg_threshold}), 1, 0))",
                "required_sentiments": ["pos_conf_low", "neg_conf_up"],
                "parameters": {"pos_threshold": 0.85, "neg_threshold": 0.15},
                "category": "reversal"
            },
            "confidence_reversal": {
                "description": "置信区间反转策略：窄置信区间更可靠",
                "template": "multiply(subtract({pos}, {neg}), reverse(subtract({pos_conf_up}, {pos_conf_low})))",
                "required_sentiments": ["pos", "neg", "pos_conf_up", "pos_conf_low"],
                "category": "reversal"
            },

            # 范围策略
            "range_strategy": {
                "description": "情绪范围策略：情绪最大值 - 最小值",
                "template": "subtract({max}, {min})",
                "required_sentiments": ["max", "min"],
                "category": "range"
            },
            "normalized_range": {
                "description": "标准化范围策略：情绪范围 / 均值",
                "template": "divide(subtract({max}, {min}), {mean})",
                "required_sentiments": ["max", "min", "mean"],
                "category": "range"
            }
        }

        # 按类别组织
        self.strategy_categories = {
            "basic": ["net_sentiment", "sentiment_ratio", "sentiment_difference"],
            "composite": ["composite_sentiment", "weighted_composite"],
            "deviation": ["pos_neut_deviation", "neg_neut_deviation"],
            "volatility": ["volatility_adjusted_pos", "volatility_adjusted_net"],
            "momentum": ["ts_momentum_net", "ts_zscore_sentiment"],
            "reversal": ["extreme_reversal", "confidence_reversal"],
            "range": ["range_strategy", "normalized_range"]
        }

    def _initialize_group_fields(self):
        """初始化分组字段（用于中性化）"""
        self.group_fields = {
            "industry": "industry",  # 行业代码
            "subindustry": "subindustry",  # 子行业代码
            "sector": "sector",  # 板块代码
            "country": "country",  # 国家代码
            "market_cap": "market_cap_group",  # 市值分组
            "style": "style_group",  # 风格分组（价值/成长）
        }

    def get_group_fields(self, stat_type: str = None,
                         window: str = None,
                         require_complete: bool = True) -> List[str]:
        """获取符合条件的组"""
        matching_groups = []

        for group_key, group_data in self.grouped_data.items():
            info = group_data["info"]

            if require_complete and not info["is_complete"]:
                continue

            if stat_type and info["stat_type"] != stat_type:
                continue

            if window:
                if window == 'base' and info["window"] is not None:
                    continue
                elif window != 'base' and info["window"] != window:
                    continue

            matching_groups.append(group_key)

        return sorted(matching_groups)

    def generate_strategy(self,
                          group_key: str,
                          strategy_name: str,
                          parameters: Dict = None) -> str:
        """从组生成策略"""
        if strategy_name not in self.strategy_templates:
            raise ValueError(f"未知策略: {strategy_name}")

        if group_key not in self.grouped_data:
            raise ValueError(f"未知组: {group_key}")

        template = self.strategy_templates[strategy_name]
        required_sentiments = template["required_sentiments"]
        default_params = template.get("parameters", {})

        if parameters:
            default_params.update(parameters)
        params = default_params

        group_fields = self.grouped_data[group_key]["fields"]

        # 检查所需情绪类型
        for sentiment in required_sentiments:
            if sentiment.startswith('{') and sentiment.endswith('}'):
                param_name = sentiment[1:-1]
                if param_name in params:
                    actual_sentiment = params[param_name]
                    if actual_sentiment not in group_fields:
                        raise ValueError(f"组缺少情绪类型: {actual_sentiment}")
            elif sentiment not in group_fields:
                # 检查是否是组合字段（如pos_mean需要pos的mean统计类型）
                if '_' in sentiment:
                    sentiment_type, stat = sentiment.split('_')
                    # 需要从其他组获取
                    pass
                else:
                    raise ValueError(f"组缺少情绪类型: {sentiment}")

        # 应用模板
        expression = template["template"]

        # 替换字段占位符
        for sentiment in required_sentiments:
            actual_sentiment = sentiment
            if sentiment.startswith('{') and sentiment.endswith('}'):
                param_name = sentiment[1:-1]
                if param_name in params:
                    actual_sentiment = params[param_name]

            if actual_sentiment in group_fields:
                expression = expression.replace(f"{{{sentiment}}}", group_fields[actual_sentiment])
            elif '_' in actual_sentiment:
                # 处理组合字段（如pos_mean）
                sent_type, stat = actual_sentiment.split('_')
                # 需要从其他组查找
                found = False
                for gk, gdata in self.grouped_data.items():
                    ginfo = gdata["info"]
                    if ginfo["stat_type"] == stat and sent_type in gdata["fields"]:
                        expression = expression.replace(f"{{{sentiment}}}", gdata["fields"][sent_type])
                        found = True
                        break
                if not found:
                    raise ValueError(f"未找到字段: {actual_sentiment}")

        # 替换参数占位符
        for param_key, param_value in params.items():
            expression = expression.replace(f"{{{param_key}}}", str(param_value))

        return expression

    def generate_neutralized_strategy(self,
                                      base_strategy: str,
                                      group_type: str = "industry") -> str:
        """
        生成中性化策略

        Args:
            base_strategy: 基础策略表达式
            group_type: 中性化类型，可选值: industry, subindustry, sector, country

        Returns:
            中性化的Alpha表达式
        """
        if group_type not in self.group_fields:
            raise ValueError(f"未知分组类型: {group_type}")

        group_field = self.group_fields[group_type]
        return f"group_neutralize({base_strategy}, {group_field})"

    def generate_all_strategies_for_group(self,
                                          group_key: str,
                                          include_neutralized: bool = True) -> Dict[str, str]:
        """
        为指定组生成所有可能的策略

        Returns:
            策略名称 -> 表达式 的字典
        """
        strategies = {}
        group_info = self.grouped_data[group_key]["info"]
        stat_type = group_info["stat_type"]

        # 生成基础策略
        for strategy_name, template in self.strategy_templates.items():
            try:
                # 检查策略是否适用于此组
                required_sentiments = template["required_sentiments"]

                # 简单的兼容性检查
                group_fields = self.grouped_data[group_key]["fields"]
                can_generate = True
                for sentiment in required_sentiments:
                    if sentiment.startswith('{') and sentiment.endswith('}'):
                        # 参数化情绪类型，需要进一步检查
                        pass
                    elif sentiment not in group_fields:
                        # 检查是否是组合字段
                        if '_' in sentiment:
                            sent_type, stat = sentiment.split('_')
                            if stat != stat_type:
                                can_generate = False
                                break
                        else:
                            can_generate = False
                            break

                if can_generate:
                    # 尝试生成策略
                    expr = self.generate_strategy(group_key, strategy_name)
                    strategies[strategy_name] = expr

                    # 如果需要，生成中性化版本
                    if include_neutralized:
                        for group_type in ["industry", "subindustry", "sector"]:
                            neutralized_expr = self.generate_neutralized_strategy(expr, group_type)
                            strategies[f"{strategy_name}_{group_type}_neutralized"] = neutralized_expr

            except Exception as e:
                # 策略生成失败，跳过
                pass

        return strategies

    def generate_all_strategies(self,
                                include_neutralized: bool = True,
                                include_multi_window: bool = True) -> Dict[str, Dict[str, str]]:
        """
        生成所有可能的Alpha表达式

        Returns:
            字典结构: {
                "group_key": {
                    "strategy_name": "expression",
                    ...
                },
                ...
            }
        """
        all_strategies = {}

        print("开始生成所有Alpha表达式...")

        # 为每个完整组生成策略
        complete_groups = self.get_group_fields(require_complete=True)

        for i, group_key in enumerate(complete_groups):
            print(f"处理组 {i + 1}/{len(complete_groups)}: {group_key}")

            group_strategies = self.generate_all_strategies_for_group(
                group_key, include_neutralized=include_neutralized
            )

            if group_strategies:
                all_strategies[group_key] = group_strategies

        # 生成多窗口策略
        if include_multi_window:
            multi_window_strategies = self._generate_multi_window_strategies()
            all_strategies.update(multi_window_strategies)

        return all_strategies

    def _generate_multi_window_strategies(self) -> Dict[str, Dict[str, str]]:
        """生成多窗口策略"""
        multi_window_strategies = {}

        # 获取所有统计类型
        stat_types = set()
        for group_data in self.grouped_data.values():
            info = group_data["info"]
            if info["stat_type"]:
                stat_types.add(info["stat_type"])

        for stat_type in stat_types:
            # 获取此统计类型的所有窗口
            windows = []
            for group_key in self.grouped_data:
                info = self.grouped_data[group_key]["info"]
                if info["stat_type"] == stat_type and info["is_complete"] and info["window"]:
                    if info["window"] not in windows:
                        windows.append(info["window"])

            if len(windows) >= 2:
                # 按数字排序
                windows = sorted(windows, key=lambda x: int(x))

                # 生成多窗口组合策略
                for strategy_name in ["net_sentiment", "composite_sentiment"]:
                    try:
                        # 为每个窗口生成表达式
                        window_exprs = []
                        for window in windows:
                            # 查找对应的组
                            group_key = None
                            for gk in self.grouped_data:
                                ginfo = self.grouped_data[gk]["info"]
                                if (ginfo["stat_type"] == stat_type and
                                        ginfo["window"] == window and
                                        ginfo["is_complete"]):
                                    group_key = gk
                                    break

                            if group_key:
                                expr = self.generate_strategy(group_key, strategy_name)
                                window_exprs.append(expr)

                        if len(window_exprs) >= 2:
                            # 等权重组合
                            if len(window_exprs) == 2:
                                multi_expr = f"add(multiply({window_exprs[0]}, 0.5), multiply({window_exprs[1]}, 0.5))"
                            elif len(window_exprs) == 3:
                                multi_expr = f"add(multiply({window_exprs[0]}, 0.4), multiply({window_exprs[1]}, 0.3), multiply({window_exprs[2]}, 0.3))"
                            elif len(window_exprs) == 4:
                                multi_expr = f"add(multiply({window_exprs[0]}, 0.4), multiply({window_exprs[1]}, 0.3), multiply({window_exprs[2]}, 0.2), multiply({window_exprs[3]}, 0.1))"
                            else:
                                multi_expr = f"add({', '.join(window_exprs)})"

                            group_key = f"multi_window_{stat_type}_{strategy_name}"
                            multi_window_strategies[group_key] = {
                                f"multi_window_{strategy_name}": multi_expr
                            }

                            # 生成中性化版本
                            for group_type in ["industry", "subindustry", "sector"]:
                                neutralized_expr = self.generate_neutralized_strategy(multi_expr, group_type)
                                multi_window_strategies[group_key][
                                    f"multi_window_{strategy_name}_{group_type}_neutralized"] = neutralized_expr

                    except Exception as e:
                        # 跳过生成失败的多窗口策略
                        pass

        return multi_window_strategies

    def generate_full_pipeline_strategies(self) -> Dict[str, Dict[str, str]]:
        """
        生成完整处理流程的策略

        Returns:
            完整策略字典
        """
        full_strategies = {}

        # 获取基础策略
        base_strategies = self.generate_all_strategies(include_neutralized=False, include_multi_window=False)

        for group_key, strategies in base_strategies.items():
            group_full_strategies = {}

            for strategy_name, base_expr in strategies.items():
                # 跳过已经是完整流程的策略
                if any(x in strategy_name for x in ["neutralized", "full_pipeline"]):
                    continue

                # 定义不同的处理管道
                pipelines = {
                    "basic": {
                        "description": "基本处理: 衰减 + 风险控制 + 标准化",
                        "preprocessing": ["hump_decay"],
                        "risk_control": True,
                        "normalization": True,
                        "postprocessing": []
                    },
                    "advanced": {
                        "description": "高级处理: 多步预处理 + 行业中性化",
                        "preprocessing": ["ts_decay_linear", "winsorize"],
                        "risk_control": True,
                        "normalization": True,
                        "postprocessing": ["industry_neutralized", "scale"]
                    },
                    "conservative": {
                        "description": "保守处理: 严格风险控制 + 多行业中性化",
                        "preprocessing": ["hump_decay", "nan_out"],
                        "risk_control": True,
                        "normalization": True,
                        "postprocessing": ["industry_neutralized", "subindustry_neutralized", "trade_when"]
                    }
                }

                # 为每个管道生成完整策略
                for pipe_name, pipe_config in pipelines.items():
                    try:
                        full_expr = base_expr

                        # 预处理
                        if pipe_config["preprocessing"]:
                            for step in pipe_config["preprocessing"]:
                                if step == "hump_decay":
                                    full_expr = f"hump_decay({full_expr}, p=0.05)"
                                elif step == "ts_decay_linear":
                                    full_expr = f"ts_decay_linear({full_expr}, d=5, dense=false)"
                                elif step == "winsorize":
                                    full_expr = f"winsorize({full_expr}, std=3)"
                                elif step == "nan_out":
                                    full_expr = f"nan_out({full_expr}, lower=-3, upper=3)"

                        # 风险控制
                        if pipe_config["risk_control"]:
                            full_expr = f"hump({full_expr}, hump=0.01)"

                        # 标准化
                        if pipe_config["normalization"]:
                            full_expr = f"zscore({full_expr})"

                        # 后处理
                        if pipe_config["postprocessing"]:
                            for step in pipe_config["postprocessing"]:
                                if step == "industry_neutralized":
                                    full_expr = self.generate_neutralized_strategy(full_expr, "industry")
                                elif step == "subindustry_neutralized":
                                    full_expr = self.generate_neutralized_strategy(full_expr, "subindustry")
                                elif step == "scale":
                                    full_expr = f"scale({full_expr}, scale=1, longscale=1.2, shortscale=0.8)"
                                elif step == "trade_when":
                                    condition = f"greater({list(self.grouped_data[group_key]['fields'].values())[0]}, 0)"  # 示例条件
                                    full_expr = f"trade_when({condition}, {full_expr}, NaN)"

                        full_strategy_name = f"{strategy_name}_{pipe_name}_pipeline"
                        group_full_strategies[full_strategy_name] = {
                            "expression": full_expr,
                            "description": pipe_config["description"],
                            "base_strategy": strategy_name
                        }

                    except Exception as e:
                        # 跳过生成失败的管道
                        pass

            if group_full_strategies:
                full_strategies[group_key] = group_full_strategies

        return full_strategies

    def export_all_strategies(self,
                              output_format: str = "json",
                              include_full_pipeline: bool = True) -> Union[str, Dict]:
        """
        导出所有Alpha表达式

        Args:
            output_format: 输出格式，'json' 或 'python'
            include_full_pipeline: 是否包含完整处理管道

        Returns:
            所有策略的字典或字符串
        """
        print("导出所有Alpha表达式...")

        # 收集所有策略
        all_data = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "total_fields": self.group_stats["total_fields"],
                "complete_groups": self.group_stats["groups_complete"],
                "available_stat_types": list(self._get_available_stat_types()),
                "available_windows": list(self._get_available_windows()),
                "strategy_count": 0
            },
            "strategies": {},
            "categories": self.strategy_categories,
            "group_fields": self.group_fields,
            "operators": self.operators
        }

        # 基础策略
        print("生成基础策略...")
        base_strategies = self.generate_all_strategies()

        # 完整管道策略
        if include_full_pipeline:
            print("生成完整管道策略...")
            full_strategies = self.generate_full_pipeline_strategies()

            # 合并策略
            for group_key, strategies in base_strategies.items():
                if group_key not in all_data["strategies"]:
                    all_data["strategies"][group_key] = {}

                for strategy_name, expr in strategies.items():
                    all_data["strategies"][group_key][strategy_name] = {
                        "expression": expr,
                        "type": "base"
                    }

            for group_key, strategies in full_strategies.items():
                if group_key not in all_data["strategies"]:
                    all_data["strategies"][group_key] = {}

                for strategy_name, strategy_data in strategies.items():
                    all_data["strategies"][group_key][strategy_name] = {
                        "expression": strategy_data["expression"],
                        "description": strategy_data.get("description", ""),
                        "base_strategy": strategy_data.get("base_strategy", ""),
                        "type": "full_pipeline"
                    }
        else:
            # 只包含基础策略
            for group_key, strategies in base_strategies.items():
                all_data["strategies"][group_key] = {}
                for strategy_name, expr in strategies.items():
                    all_data["strategies"][group_key][strategy_name] = {
                        "expression": expr,
                        "type": "base"
                    }

        # 计算策略总数
        strategy_count = 0
        for group_strategies in all_data["strategies"].values():
            strategy_count += len(group_strategies)

        all_data["meta"]["strategy_count"] = strategy_count

        # 按输出格式处理
        if output_format == "json":
            return json.dumps(all_data, indent=2, ensure_ascii=False)
        elif output_format == "python":
            return self._format_python(all_data)
        else:
            return all_data

    def _get_available_windows(self):
        """获取可用窗口"""
        windows = set()
        for group_data in self.grouped_data.values():
            info = group_data["info"]
            if info["window"]:
                windows.add(info["window"])
        return windows

    def _get_available_stat_types(self):
        """获取可用统计类型"""
        stat_types = set()
        for group_data in self.grouped_data.values():
            info = group_data["info"]
            if info["stat_type"]:
                stat_types.add(info["stat_type"])
        return stat_types

    def _format_python(self, data: Dict) -> str:
        """格式化为Python代码"""
        output = "# 情感数据Alpha表达式库\n\n"
        output += f"# 生成时间: {data['meta']['generated_at']}\n"
        output += f"# 总策略数: {data['meta']['strategy_count']}\n\n"

        output += "ALPHA_STRATEGIES = {\n"

        for group_key, strategies in data["strategies"].items():
            output += f'    "{group_key}": {{\n'

            for strategy_name, strategy_data in strategies.items():
                expr = strategy_data["expression"].replace('"', '\\"')
                output += f'        "{strategy_name}": {{\n'
                output += f'            "expression": "{expr}",\n'
                output += f'            "type": "{strategy_data["type"]}"\n'

                if "description" in strategy_data:
                    desc = strategy_data["description"].replace('"', '\\"')
                    output += f'            "description": "{desc}",\n'

                if "base_strategy" in strategy_data:
                    output += f'            "base_strategy": "{strategy_data["base_strategy"]}",\n'

                output = output.rstrip(",\n") + "\n        },\n"

            output = output.rstrip(",\n") + "\n    },\n"

        output = output.rstrip(",\n") + "\n}\n"

        return output
