#!/usr/bin/env python3
"""
Alpha表达式检查器命令行工具

用法:
    python check_alpha.py "rank(field1)"
    python check_alpha.py --file expressions.txt
    python check_alpha.py --interactive
"""

import sys
import os
import argparse
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alpha_checker.alpha_checker import AlphaExpressionChecker, check_alpha_expression


def format_result(result, verbose=False):
    """格式化检查结果"""
    lines = []
    
    if result.is_valid:
        lines.append("✅ 表达式有效")
    else:
        lines.append(f"❌ 表达式无效，发现 {len(result.errors)} 个错误:")
        for error in result.errors:
            lines.append(f"   - {error}")
    
    if verbose or result.operators_used:
        unique_ops = list(dict.fromkeys(result.operators_used))  # 去重并保持顺序
        lines.append(f"\n📊 使用的操作符 ({len(unique_ops)}):")
        for op in unique_ops:
            lines.append(f"   • {op}")
    
    if verbose or result.fields_used:
        lines.append(f"\n📋 使用的字段 ({len(result.fields_used)}):")
        for field in result.fields_used:
            lines.append(f"   • {field}")
    
    if verbose and result.structure_info:
        lines.append(f"\n📈 结构信息:")
        for key, value in result.structure_info.items():
            lines.append(f"   • {key}: {value}")
    
    return '\n'.join(lines)


def check_single_expression(expression, verbose=False):
    """检查单个表达式"""
    print(f"\n{'='*80}")
    print(f"表达式: {expression[:100]}{'...' if len(expression) > 100 else ''}")
    print('='*80)
    
    result = check_alpha_expression(expression)
    print(format_result(result, verbose))
    
    return result.is_valid


def check_from_file(file_path, verbose=False):
    """从文件检查多个表达式"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        expressions = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"📄 从文件读取到 {len(expressions)} 个表达式\n")
    
    results = []
    for i, expr in enumerate(expressions, 1):
        print(f"[{i}/{len(expressions)}]", end=' ')
        is_valid = check_single_expression(expr, verbose)
        results.append((expr, is_valid))
    
    # 汇总统计
    valid_count = sum(1 for _, valid in results if valid)
    print(f"\n{'='*80}")
    print(f"📊 汇总统计:")
    print(f"   总表达式数: {len(results)}")
    print(f"   ✅ 有效: {valid_count}")
    print(f"   ❌ 无效: {len(results) - valid_count}")
    print(f"   通过率: {valid_count/len(results)*100:.1f}%")
    
    return valid_count == len(results)


def interactive_mode():
    """交互模式"""
    print("\n" + "="*80)
    print("Alpha表达式检查器 - 交互模式")
    print("输入表达式进行检查，输入 'quit' 或 'exit' 退出")
    print("="*80 + "\n")
    
    checker = AlphaExpressionChecker()
    
    while True:
        try:
            expression = input("请输入Alpha表达式: ").strip()
            
            if not expression:
                continue
            
            if expression.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if expression.lower() in ['help', 'h', '?']:
                print("\n可用命令:")
                print("  help, h, ?  - 显示帮助")
                print("  ops         - 列出所有操作符")
                print("  cat <类别>  - 列出指定类别的操作符")
                print("  info <操作符> - 显示操作符详细信息")
                print("  quit, exit  - 退出程序\n")
                continue
            
            if expression.lower() == 'ops':
                ops = checker.list_all_operators()
                print(f"\n共有 {len(ops)} 个操作符:")
                print(', '.join(sorted(ops)))
                continue
            
            if expression.lower().startswith('cat '):
                category = expression[4:].strip()
                ops = checker.get_operators_by_category(category)
                if ops:
                    print(f"\n类别 '{category}' 的操作符 ({len(ops)}):")
                    print(', '.join(sorted(ops)))
                else:
                    print(f"\n未找到类别 '{category}' 的操作符")
                continue
            
            if expression.lower().startswith('info '):
                op_name = expression[5:].strip()
                op_info = checker.get_operator_info(op_name)
                if op_info:
                    print(f"\n操作符: {op_info['name']}")
                    print(f"类别: {op_info['category']}")
                    print(f"定义: {op_info['definition']}")
                    print(f"描述: {op_info['description']}")
                    print(f"适用范围: {', '.join(op_info['scope'])}")
                    if op_info.get('level'):
                        print(f"级别: {op_info['level']}")
                else:
                    print(f"\n未找到操作符 '{op_name}'")
                continue
            
            # 检查表达式
            result = checker.check(expression)
            print(format_result(result, verbose=True))
            print()
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Alpha表达式语法检查器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "rank(field1)"
  %(prog)s --verbose "ts_delay(close, 10)"
  %(prog)s --file expressions.txt
  %(prog)s --interactive
        """
    )
    
    parser.add_argument(
        'expression',
        nargs='?',
        help='要检查的Alpha表达式'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    parser.add_argument(
        '-f', '--file',
        help='从文件读取表达式（每行一个）'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='进入交互模式'
    )
    
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='以JSON格式输出结果'
    )
    
    args = parser.parse_args()
    
    # 交互模式
    if args.interactive:
        interactive_mode()
        return
    
    # 从文件读取
    if args.file:
        success = check_from_file(args.file, args.verbose)
        sys.exit(0 if success else 1)
    
    # 检查单个表达式
    if args.expression:
        result = check_alpha_expression(args.expression)
        
        if args.json:
            # JSON输出
            output = {
                'is_valid': result.is_valid,
                'errors': [
                    {
                        'position': err.position,
                        'message': err.message,
                        'error_type': err.error_type
                    }
                    for err in result.errors
                ],
                'operators_used': list(dict.fromkeys(result.operators_used)),
                'fields_used': result.fields_used,
                'structure_info': result.structure_info
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # 文本输出
            print(format_result(result, args.verbose))
        
        sys.exit(0 if result.is_valid else 1)
    
    # 没有提供任何参数，显示帮助
    parser.print_help()


if __name__ == '__main__':
    main()
