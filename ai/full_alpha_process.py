#!/usr/bin/env python3
"""
完整的Alpha生成、回测、监控和结果展示流程
"""

import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from ai.generate_alpha_with_content import generate_alphas_with_platform_knowledge
from ai.backtest_alpha import simulate_alpha
from ai.monitor_simulation import monitor_simulation_progress
from ai.get_alpha_details import get_alpha_details


def setup_logging(log_file: str = None):
    """
    设置日志记录
    
    Args:
        log_file: 日志文件路径
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 如果没有指定日志文件，则使用时间戳创建文件名
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"alpha_process_{timestamp}.log")
    
    # 配置日志格式，包含模块名和代码行号
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info(f"日志文件已创建: {log_file}")
    return log_file


def generate_alpha_expressions(topic: str = "sentiment analysis", count: int = 3) -> list[dict[str, Any]]:
    """
    生成Alpha表达式
    
    Args:
        topic: Alpha主题
        count: 生成的Alpha表达式数量
    
    Returns:
        生成的Alpha表达式字典
    """
    logging.info(f"开始生成Alpha表达式，主题: {topic}, 数量: {count}")
    
    try:
        alphas = generate_alphas_with_platform_knowledge(topic, count)
        logging.info(f"成功生成Alpha表达式: {json.dumps(alphas, ensure_ascii=False, indent=2)}")
        return alphas
    except Exception as e:
        logging.error(f"生成Alpha表达式时出错: {str(e)}")
        raise


def backtest_alpha_expression(alpha_expr: str) -> Dict[str, Any]:
    """
    对Alpha表达式进行回测
    
    Args:
        alpha_expr: Alpha表达式
    
    Returns:
        回测结果
    """
    logging.info(f"开始回测Alpha表达式: {alpha_expr}")
    
    try:
        result = simulate_alpha(alpha_expr)
        logging.info(f"Alpha表达式回测提交结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        logging.error(f"回测Alpha表达式时出错: {str(e)}")
        raise


def monitor_backtest_progress(simulation_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
    """
    监控回测进度
    
    Args:
        simulation_id: 模拟ID
        max_wait_time: 最大等待时间(秒)
    
    Returns:
        监控结果
    """
    logging.info(f"开始监控回测进度，模拟ID: {simulation_id}, 最大等待时间: {max_wait_time}秒")
    
    try:
        result = monitor_simulation_progress(simulation_id, max_wait_time)
        logging.info(f"回测监控结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        logging.error(f"监控回测进度时出错: {str(e)}")
        raise


def get_alpha_statistics(alpha_id: str) -> Dict[str, Any]:
    """
    获取Alpha统计结果
    
    Args:
        alpha_id: Alpha ID
    
    Returns:
        Alpha统计结果
    """
    logging.info(f"开始获取Alpha统计结果，Alpha ID: {alpha_id}")
    
    try:
        result = get_alpha_details(alpha_id)
        logging.info(f"Alpha统计结果获取成功")
        return result
    except Exception as e:
        logging.error(f"获取Alpha统计结果时出错: {str(e)}")
        raise


def save_process_result(data, filename: str):
    """
    保存流程结果到文件
    
    Args:
        data: 要保存的数据
        filename: 文件名
    """
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logging.info(f"流程结果已保存到: {output_path}")


def main():
    """主函数"""
    # 设置日志
    log_file = setup_logging()
    logging.info("开始执行完整的Alpha生成、回测、监控和结果展示流程")
    
    try:
        # 1. 生成Alpha表达式
        logging.info("步骤1: 生成Alpha表达式")
        alphas = generate_alpha_expressions("sentiment analysis", 3)
        save_process_result(alphas, "generated_alphas_full_process.json")
        
        # 收集所有Alpha表达式进行回测
        if not alphas:
            logging.error("未生成任何Alpha表达式")
            return
            
        # 收集所有表达式（现在alphas已经是扁平结构的列表）
        all_expressions = []
        
        # 直接使用扁平结构
        for i, alpha_item in enumerate(alphas):
            expr_info = {
                'expression': alpha_item['expression'],
                'field': alpha_item['field_name'],
                'template': alpha_item['template_name']
            }
            all_expressions.append(expr_info)
        
        logging.info(f"总共收集到 {len(all_expressions)} 个Alpha表达式进行回测")
        
        # 存储所有回测结果
        all_backtest_results = []
        all_monitor_results = []
        all_alpha_stats = []
        
        # 对每个表达式进行回测
        for i, expr_info in enumerate(all_expressions):
            alpha_expression = expr_info['expression']
            field = expr_info['field']
            template = expr_info['template']
            
            logging.info(f"步骤2.{i+1}: 回测Alpha表达式 (字段: {field}, 模板: {template})")
            logging.info(f"表达式内容: {alpha_expression}")
            
            # 回测Alpha表达式
            backtest_result = backtest_alpha_expression(alpha_expression)
            
            # 为每次回测创建唯一的文件名
            backtest_filename = f"backtest_submission_result_{field}_{template}_{i+1}.json"
            save_process_result(backtest_result, backtest_filename)
            
            # 检查回测是否成功提交
            if backtest_result.get("status") != "SUBMITTED":
                logging.error(f"Alpha表达式回测提交失败: {alpha_expression}")
                continue
                
            simulation_id = backtest_result.get("simulation_id")
            if not simulation_id:
                logging.error(f"未获取到模拟ID: {alpha_expression}")
                continue
                
            logging.info(f"Alpha表达式回测已提交，模拟ID: {simulation_id}")
            
            # 添加到结果列表
            backtest_result['expression_info'] = expr_info
            all_backtest_results.append(backtest_result)
            
            # 3. 监控回测进度
            logging.info(f"步骤3.{i+1}: 监控回测进度，模拟ID: {simulation_id}")
            monitor_result = monitor_backtest_progress(simulation_id, 60)  # 等待1分钟
            
            # 为每次监控创建唯一的文件名
            monitor_filename = f"monitor_result_{simulation_id}_{i+1}.json"
            save_process_result(monitor_result, monitor_filename)
            
            # 检查监控结果
            if "error" in monitor_result:
                logging.warning(f"监控过程中出现错误: {monitor_result['error']}")
                
            # 添加到监控结果列表
            monitor_result['expression_info'] = expr_info
            monitor_result['simulation_id'] = simulation_id
            all_monitor_results.append(monitor_result)
            
            # 4. 获取Alpha统计结果
            logging.info(f"步骤4.{i+1}: 获取Alpha统计结果")
            
            # 从监控结果中获取Alpha ID
            alpha_id = None
            if "alpha" in monitor_result:
                alpha_id = monitor_result["alpha"]
                
            # 如果我们有Alpha ID，获取详细统计结果
            if alpha_id:
                logging.info(f"获取到Alpha ID: {alpha_id}")
                alpha_stats = get_alpha_statistics(alpha_id)
                
                # 为每次统计创建唯一的文件名
                stats_filename = f"alpha_statistics_{alpha_id}_{i+1}.json"
                save_process_result(alpha_stats, stats_filename)
                
                # 显示关键统计指标
                if "is" in alpha_stats:
                    stats = alpha_stats["is"]
                    logging.info("关键统计指标:")
                    logging.info(f"  Sharpe Ratio: {stats.get('sharpe', 'N/A')}")
                    logging.info(f"  Fitness: {stats.get('fitness', 'N/A')}")
                    logging.info(f"  Returns: {stats.get('returns', 'N/A')}")
                    logging.info(f"  Turnover: {stats.get('turnover', 'N/A')}")
                    logging.info(f"  Margin: {stats.get('margin', 'N/A')}")
                    logging.info(f"  Long Count: {stats.get('longCount', 'N/A')}")
                    logging.info(f"  Short Count: {stats.get('shortCount', 'N/A')}")
                
                # 添加到统计结果列表
                alpha_stats['expression_info'] = expr_info
                alpha_stats['alpha_id'] = alpha_id
                all_alpha_stats.append(alpha_stats)
            else:
                logging.warning("未获取到Alpha ID，无法获取详细统计结果")
            
        # 保存汇总结果
        summary_results = {
            "total_expressions": len(all_expressions),
            "successful_submissions": len(all_backtest_results),
            "monitor_results_count": len(all_monitor_results),
            "statistics_results_count": len(all_alpha_stats),
            "backtest_results": all_backtest_results,
            "monitor_results": all_monitor_results,
            "alpha_statistics": all_alpha_stats
        }
        save_process_result(summary_results, "full_process_summary.json")
            
        logging.info("完整的Alpha生成、回测、监控和结果展示流程执行完成")
        logging.info(f"详细日志已保存到: {log_file}")
        
    except Exception as e:
        logging.error(f"执行流程时发生错误: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()