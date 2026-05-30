"""
Alpha表达式语法检查器
用于验证Alpha表达式的语法正确性，包括：
1. 括号匹配
2. 操作符合法性
3. 参数数量检查
4. 基本语法结构
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class CheckError:
    """检查错误信息"""
    position: int
    message: str
    error_type: str = "SYNTAX_ERROR"
    
    def __str__(self):
        return f"位置 {self.position}: [{self.error_type}] {self.message}"


@dataclass
class ParseResult:
    """解析结果"""
    is_valid: bool
    errors: List[CheckError] = field(default_factory=list)
    operators_used: List[str] = field(default_factory=list)
    fields_used: List[str] = field(default_factory=list)
    structure_info: Dict = field(default_factory=dict)


class AlphaExpressionChecker:
    """Alpha表达式检查器"""
    
    def __init__(self, operators_file: str = None):
        """
        初始化检查器
        
        Args:
            operators_file: 操作符定义文件路径，如果为None则使用默认路径
        """
        import json
        import os
        
        if operators_file is None:
            # 默认使用alpha_operators.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            operators_file = os.path.join(current_dir, 'alpha_operators.json')
        
        with open(operators_file, 'r', encoding='utf-8') as f:
            operators_list = json.load(f)
        
        # 构建操作符字典
        self.operators = {}
        for op in operators_list:
            self.operators[op['name']] = op
    
    def check(self, expression: str) -> ParseResult:
        """
        检查Alpha表达式
        
        Args:
            expression: Alpha表达式字符串
            
        Returns:
            ParseResult: 检查结果
        """
        errors = []
        
        # 1. 基本空值检查
        if not expression or not expression.strip():
            return ParseResult(
                is_valid=False,
                errors=[CheckError(0, "表达式为空", "EMPTY_EXPRESSION")]
            )
        
        expression = expression.strip()
        
        # 2. 括号匹配检查
        bracket_errors = self._check_brackets(expression)
        errors.extend(bracket_errors)
        
        # 3. 词法分析
        tokens = self._tokenize(expression)
        
        # 4. 提取使用的操作符和字段
        operators_used = self._extract_operators(tokens)
        fields_used = self._extract_fields(tokens, operators_used)
        
        # 5. 验证操作符合法性
        operator_errors = self._validate_operators(operators_used)
        errors.extend(operator_errors)
        
        # 6. 验证操作符参数数量
        param_errors = self._validate_operator_parameters(expression, tokens)
        errors.extend(param_errors)
        
        # 7. 检查基本语法结构
        syntax_errors = self._check_syntax_structure(tokens)
        errors.extend(syntax_errors)
        
        is_valid = len(errors) == 0
        
        return ParseResult(
            is_valid=is_valid,
            errors=errors,
            operators_used=operators_used,
            fields_used=fields_used,
            structure_info={
                'total_tokens': len(tokens),
                'expression_length': len(expression)
            }
        )
    
    def _check_brackets(self, expression: str) -> List[CheckError]:
        """检查括号匹配"""
        errors = []
        stack = []
        
        for i, char in enumerate(expression):
            if char == '(':
                stack.append((i, '('))
            elif char == ')':
                if not stack:
                    errors.append(CheckError(i, "多余的右括号", "UNMATCHED_BRACKET"))
                else:
                    stack.pop()
        
        # 检查是否有未闭合的左括号
        for pos, bracket in stack:
            errors.append(CheckError(pos, "未闭合的左括号", "UNMATCHED_BRACKET"))
        
        return errors
    
    def _tokenize(self, expression: str) -> List[Dict]:
        """
        词法分析，将表达式分解为token
        
        Returns:
            List[Dict]: token列表，每个token包含type和value
        """
        tokens = []
        i = 0
        n = len(expression)
        
        while i < n:
            char = expression[i]
            
            # 跳过空白字符
            if char.isspace():
                i += 1
                continue
            
            # 括号
            if char in '(),':
                tokens.append({'type': 'PUNCTUATION', 'value': char, 'pos': i})
                i += 1
                continue
            
            # 数字（包括小数和负数）
            if char.isdigit() or (char == '-' and i + 1 < n and expression[i + 1].isdigit()):
                j = i
                if char == '-':
                    i += 1
                while i < n and (expression[i].isdigit() or expression[i] == '.'):
                    i += 1
                tokens.append({'type': 'NUMBER', 'value': expression[j:i], 'pos': j})
                continue
            
            # 字符串常量（引号内的内容）
            if char in '"\'':
                quote_char = char
                j = i + 1
                while j < n and expression[j] != quote_char:
                    if expression[j] == '\\':
                        j += 1  # 跳过转义字符
                    j += 1
                if j < n:
                    j += 1  # 包含结束引号
                tokens.append({'type': 'STRING', 'value': expression[i:j], 'pos': i})
                i = j
                continue
            
            # 标识符（操作符名称、字段名等）
            if char.isalpha() or char == '_':
                j = i
                while i < n and (expression[i].isalnum() or expression[i] == '_'):
                    i += 1
                tokens.append({'type': 'IDENTIFIER', 'value': expression[j:i], 'pos': j})
                continue
            
            # 运算符
            if char in '+-*/=' or expression[i:i+2] in ['==', '!=', '<=', '>=']:
                op = expression[i:i+2] if expression[i:i+2] in ['==', '!=', '<=', '>='] else char
                tokens.append({'type': 'OPERATOR', 'value': op, 'pos': i})
                i += len(op)
                continue
            
            # 未知字符
            tokens.append({'type': 'UNKNOWN', 'value': char, 'pos': i})
            i += 1
        
        return tokens
    
    def _extract_operators(self, tokens: List[Dict]) -> List[str]:
        """从token中提取操作符"""
        operators = []
        i = 0
        while i < len(tokens):
            # 如果标识符后面跟着左括号，则是函数调用（操作符）
            if (tokens[i]['type'] == 'IDENTIFIER' and 
                i + 1 < len(tokens) and 
                tokens[i + 1]['value'] == '('):
                operators.append(tokens[i]['value'])
            i += 1
        return operators
    
    def _extract_fields(self, tokens: List[Dict], operators: List[str]) -> List[str]:
        """从token中提取字段名"""
        fields = []
        operator_set = set(operators)
        
        for token in tokens:
            if token['type'] == 'IDENTIFIER':
                # 不是操作符且不是常见关键字的标识符视为字段
                if (token['value'] not in operator_set and 
                    token['value'] not in ['true', 'false', 'True', 'False', 'NaN', 'nan', 'INF', 'inf']):
                    fields.append(token['value'])
        
        # 去重并保持顺序
        seen = set()
        unique_fields = []
        for f in fields:
            if f not in seen:
                seen.add(f)
                unique_fields.append(f)
        
        return unique_fields
    
    def _validate_operators(self, operators: List[str]) -> List[CheckError]:
        """验证操作符是否合法"""
        errors = []
        
        for op in operators:
            if op not in self.operators:
                errors.append(CheckError(
                    position=-1,
                    message=f"未知的操作符: '{op}'",
                    error_type="UNKNOWN_OPERATOR"
                ))
        
        return errors
    
    def _validate_operator_parameters(self, expression: str, tokens: List[Dict]) -> List[CheckError]:
        """验证操作符的参数数量"""
        errors = []
        
        # 查找所有函数调用并检查参数
        i = 0
        while i < len(tokens):
            if (tokens[i]['type'] == 'IDENTIFIER' and 
                i + 1 < len(tokens) and 
                tokens[i + 1]['value'] == '('):
                
                operator_name = tokens[i]['value']
                
                # 获取该操作符的定义
                if operator_name in self.operators:
                    op_def = self.operators[operator_name]
                    definition = op_def.get('definition', '')
                    
                    # 解析参数数量要求
                    min_params, max_params = self._parse_parameter_requirements(definition)
                    
                    # 计算实际参数数量（传递左括号的位置）
                    actual_params = self._count_parameters(tokens, i + 1)
                    
                    # 检查参数数量
                    if actual_params < min_params:
                        errors.append(CheckError(
                            position=tokens[i]['pos'],
                            message=f"操作符 '{operator_name}' 至少需要 {min_params} 个参数，但只提供了 {actual_params} 个",
                            error_type="INSUFFICIENT_PARAMETERS"
                        ))
                    elif max_params is not None and actual_params > max_params:
                        errors.append(CheckError(
                            position=tokens[i]['pos'],
                            message=f"操作符 '{operator_name}' 最多需要 {max_params} 个参数，但提供了 {actual_params} 个",
                            error_type="EXCESS_PARAMETERS"
                        ))
            
            i += 1
        
        return errors
    
    def _parse_parameter_requirements(self, definition: str) -> Tuple[int, Optional[int]]:
        """
        从定义中解析参数数量要求
        
        Returns:
            (min_params, max_params): 最小和最大参数数量，max_params为None表示无限制
        """
        # 提取括号内的参数部分
        match = re.search(r'\((.*?)\)', definition)
        if not match:
            return 0, None
        
        params_str = match.group(1)
        
        # 处理特殊情况
        if '...' in params_str:
            # 可变参数，如 multiply(x, y, ...)
            # 计算必需参数（在...之前）
            before_ellipsis = params_str.split('...')[0]
            required_params = [p.strip() for p in before_ellipsis.split(',') if p.strip()]
            return len(required_params), None
        
        # 计算参数数量
        # 简单方法：统计逗号数量 + 1，但要考虑可选参数
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        
        # 统计必需参数（没有默认值的参数）
        required_count = 0
        total_count = len(params)
        
        for param in params:
            # 跳过注释和说明
            if '=' in param:
                # 有默认值的参数是可选的
                continue
            else:
                required_count += 1
        
        # 对于大多数情况，返回必需参数数量和总参数数量
        if required_count > 0:
            return required_count, total_count
        
        return total_count, total_count
    
    def _count_parameters(self, tokens: List[Dict], start_pos: int) -> int:
        """
        从给定位置开始计算函数调用的参数数量
        
        Args:
            tokens: token列表
            start_pos: 开始位置（应该是左括号的位置）
            
        Returns:
            参数数量
        """
        if start_pos >= len(tokens) or tokens[start_pos]['value'] != '(':
            return 0
        
        param_count = 0
        bracket_depth = 0
        i = start_pos + 1  # 跳过左括号
        
        # 检查是否为空参数
        if i < len(tokens) and tokens[i]['value'] == ')':
            return 0
        
        # 第一个参数
        has_content = False
        
        while i < len(tokens):
            token = tokens[i]
            
            if token['value'] == '(':
                bracket_depth += 1
                has_content = True
            elif token['value'] == ')':
                if bracket_depth == 0:
                    # 函数调用结束
                    if has_content:
                        param_count += 1
                    break
                bracket_depth -= 1
            elif token['value'] == ',' and bracket_depth == 0:
                # 遇到顶层逗号，当前参数结束
                if has_content:
                    param_count += 1
                has_content = False
            else:
                # 非空白、非标点的内容
                if token['type'] not in ['PUNCTUATION'] or token['value'] not in [',', '(', ')']:
                    has_content = True
            
            i += 1
        
        return param_count
    
    def _check_syntax_structure(self, tokens: List[Dict]) -> List[CheckError]:
        """检查基本语法结构"""
        errors = []
        
        if not tokens:
            return errors
        
        # 检查是否以操作符或字段开头
        first_token = tokens[0]
        if first_token['type'] not in ['IDENTIFIER', 'NUMBER', '(']:
            errors.append(CheckError(
                position=first_token['pos'],
                message=f"表达式不能以 '{first_token['value']}' 开头",
                error_type="INVALID_START"
            ))
        
        # 检查连续的标识符（可能是缺少运算符）
        for i in range(len(tokens) - 1):
            if (tokens[i]['type'] == 'IDENTIFIER' and 
                tokens[i + 1]['type'] == 'IDENTIFIER' and
                tokens[i]['value'] not in ['true', 'false', 'True', 'False']):
                # 检查是否是函数调用后的参数
                if i + 2 < len(tokens) and tokens[i + 1]['value'] != '(':
                    errors.append(CheckError(
                        position=tokens[i + 1]['pos'],
                        message=f"标识符 '{tokens[i]['value']}' 后直接跟 '{tokens[i + 1]['value']}'，可能缺少运算符",
                        error_type="MISSING_OPERATOR"
                    ))
        
        return errors
    
    def get_operator_info(self, operator_name: str) -> Optional[Dict]:
        """获取操作符的详细信息"""
        return self.operators.get(operator_name)
    
    def list_all_operators(self) -> List[str]:
        """列出所有可用的操作符"""
        return list(self.operators.keys())
    
    def get_operators_by_category(self, category: str) -> List[str]:
        """获取指定类别的所有操作符"""
        return [
            name for name, op in self.operators.items()
            if op.get('category') == category
        ]


def check_alpha_expression(expression: str, operators_file: str = None) -> ParseResult:
    """
    便捷函数：检查Alpha表达式
    
    Args:
        expression: Alpha表达式
        operators_file: 操作符定义文件路径
        
    Returns:
        ParseResult: 检查结果
    """
    checker = AlphaExpressionChecker(operators_file)
    return checker.check(expression)


if __name__ == '__main__':
    # 测试示例
    test_expressions = [
        # 正确的表达式
        "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)) / (abs(ts_delay(vec_avg(anl2_consensus_eps_est), 20)) + 0.01))",
        
        # 错误的表达式 - 括号不匹配
        "rank((vec_avg(anl2_consensus_eps_est) - ts_delay(vec_avg(anl2_consensus_eps_est), 20)",
        
        # 错误的表达式 - 未知操作符
        "unknown_op(field1, field2)",
        
        # 错误的表达式 - 参数不足
        "ts_delay(field1)",
    ]
    
    checker = AlphaExpressionChecker()
    
    for i, expr in enumerate(test_expressions, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}:")
        print(f"表达式: {expr[:80]}{'...' if len(expr) > 80 else ''}")
        print('-' * 60)
        
        result = checker.check(expr)
        
        if result.is_valid:
            print("✅ 表达式有效")
        else:
            print(f"❌ 表达式无效，发现 {len(result.errors)} 个错误:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.operators_used:
            print(f"使用的操作符: {', '.join(result.operators_used)}")
        
        if result.fields_used:
            print(f"使用的字段: {', '.join(result.fields_used)}")
