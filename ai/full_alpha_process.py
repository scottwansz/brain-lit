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

from ai.generate_alpha_by_ai import generate_alphas
from ai.backtest_alpha import simulate_alpha, simulate_multiple_alphas
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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        alphas = generate_alphas(topic, count)
        logging.info(f"成功生成Alpha表达式: {json.dumps(alphas, ensure_ascii=False, indent=2)}")
        return alphas
    except Exception as e:
        logging.error(f"生成Alpha表达式时出错: {str(e)}")
        raise


def backtest_alpha_expression(
        alpha_expr: str,
        region='IND',
        universe='TOP500',
        delay=1,
) -> Dict[str, Any]:
    """
    对Alpha表达式进行回测
    
    Args:
        alpha_expr: Alpha表达式
    
    Returns:
        回测结果
    """
    logging.info(f"开始回测Alpha表达式: {alpha_expr}")
    
    try:
        result = simulate_alpha(alpha_expr, region, universe, delay)
        logging.info(f"Alpha表达式回测提交结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        logging.error(f"回测Alpha表达式时出错: {str(e)}")
        raise


def backtest_alpha_expressions(
        alpha_exprs: list,
        region='IND',
        universe='TOP500',
        delay=1,
) -> None | dict[str, str] | dict[str, Any] | Any:
    """
    对多个Alpha表达式进行回测
    
    Args:
        alpha_exprs: Alpha表达式列表
    
    Returns:
        回测结果
    """
    logging.info(f"开始回测 {len(alpha_exprs)} 个Alpha表达式")
    
    # 如果只有一个表达式，使用单个提交方式
    if len(alpha_exprs) == 1:
        return backtest_alpha_expression(alpha_exprs[0], region, universe, delay)
    
    # 如果有多个表达式，分批处理，每批最多10个
    if len(alpha_exprs) > 1:
        # 分批处理Alpha表达式，每批最多10个
        batch_size = 10
        batches = [alpha_exprs[i:i + batch_size] for i in range(0, len(alpha_exprs), batch_size)]
        
        logging.info(f"将 {len(alpha_exprs)} 个Alpha表达式分为 {len(batches)} 批进行提交")
        
        results = []
        for i, batch in enumerate(batches):
            logging.info(f"提交第 {i+1}/{len(batches)} 批，包含 {len(batch)} 个Alpha表达式")
            try:
                result = simulate_multiple_alphas(batch, region, universe, delay)
                results.append(result)
                logging.info(f"第 {i+1} 批Alpha表达式提交结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except Exception as e:
                logging.error(f"批量回测第 {i+1} 批Alpha表达式时出错: {str(e)}")
                results.append({"error": str(e)})
        
        # 返回第一批的结果作为主要结果，其他结果可以通过日志查看
        return results[0] if results else {"error": "没有成功提交任何批次"}

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

    region = 'IND'
    universe = 'TOP500'
    delay = 1
    category = 'sentiment'
    dataset = 'sentiment21'
    
    try:
        # 使用预定义的Alpha表达式代替自动生成
        alpha_expressions = [
            "rank(subtract(snt21_2pos_mean, snt21_2neut_mean)) - rank(ts_delta(snt21_2neut_mean, 5))",
            "ts_zscore(snt21_2neg_mean, 20) * reverse(ts_returns(snt21_2neg_mean, 5))",
            "ts_delta(subtract(snt21_2pos_mean, snt21_2neg_mean), 5) - ts_delta(subtract(snt21_2pos_mean, snt21_2neg_mean), 20)",
            "ts_decay_linear(snt21_2neut_std, 10, dense=false) * reverse(rank(snt21_2neut_mean))",
            "subtract(rank(ts_backfill(snt21_3pos_median, 5)), rank(ts_backfill(snt21_3neg_median, 5)))",
            "ts_returns(subtract(snt21_2pos_conf_up, snt21_2pos_conf_low), 5) - ts_returns(subtract(snt21_2neg_conf_up, snt21_2neg_conf_low), 5)",
            "ts_regression(snt21_2neut_mean, ts_step(1), 20, lag=0, rettype=1)",
            "hump_decay(ts_zscore(snt21_2neg_mean, 63), p=0.05)",
            "divide(ts_decay_exp_window(snt21_2pos_std, 10, factor=0.8), ts_decay_exp_window(snt21_2neg_std, 10, factor=0.8))",
            "ts_rank(ts_delta(ts_backfill(snt21_3pos_mean, 3), 5), 20)",
            "ts_delta(rank(snt21_2neut_median), 5) - ts_delta(rank(snt21_2pos_median), 5)",
            "reverse(ts_scale(snt21_2neg_conf_up, 20, constant=0)) - ts_scale(ts_delay(snt21_2neg_conf_up, 1), 20, constant=0)",
            "ts_rank(divide(ts_backfill(snt21_2pos_mean, 5), add(ts_backfill(snt21_2neut_mean, 5), 0.000001)), 30)",
            "ts_decay_linear(power(ts_delta(snt21_3neg_std, 1), 2), 5, dense=false)",
            "subtract(rank(snt21_2pos_min), rank(snt21_2neg_max))",
            "hump(ts_av_diff(snt21_2neut_mean, 20), hump=0.01)",
            "scale_down(multiply(subtract(snt21_2pos_mean, snt21_2neg_mean), reverse(snt21_2neut_mean)), constant=0)",
            "ts_delta(rank(ts_backfill(snt21_3pos_median, 3)), 3) - ts_delta(rank(ts_backfill(snt21_3neg_median, 3)), 3)",
            "ts_regression(snt21_2neg_std, ts_step(1), 10, lag=0, rettype=1) * reverse(ts_mean(snt21_2neg_std, 10))",
            "ts_rank(ts_decay_linear(snt21_2pos_mean, 5, dense=false), 20) - ts_rank(ts_delay(snt21_2pos_mean, 5), 20)",
            "ts_mean(subtract(snt21_2neut_conf_up, snt21_2neut_conf_low), 10)",
            "ts_zscore(subtract(snt21_3pos_mean, snt21_3neg_mean), 63)",
            "jump_decay(snt21_2neg_median, d=5, sensitivity=0.5, force=0.1)",
            "if_else(ts_mean(snt21_2pos_std, 5) > ts_delay(ts_mean(snt21_2pos_std, 20), 5), ts_returns(snt21_2pos_mean, 3), reverse(ts_returns(snt21_2pos_mean, 3)))",
            "ts_returns(divide(add(snt21_2neut_mean, 0.0001), add(snt21_2pos_mean, 0.0001)), 5)",
            "ts_rank(reverse(snt21_3neg_mean), 10) - ts_rank(snt21_3neg_mean, 30)",
            "ts_corr(subtract(snt21_2pos_mean, snt21_2neg_mean), ts_step(1), 10)",
            "hump_decay(ts_delta(snt21_2neut_median, 1), p=0.02) - ts_delta(snt21_2neut_median, 5)",
            "ts_av_diff(ts_backfill(snt21_4neg_mean, 10), 20) * reverse(ts_zscore(snt21_4neg_mean, 20))",
            "rank(ts_decay_exp_window(snt21_2pos_mean, 5, factor=0.7)) + rank(reverse(ts_decay_exp_window(snt21_2neg_std, 5, factor=0.7)))"
        ]
        
        logging.info(f"使用预定义的Alpha表达式，共 {len(alpha_expressions)} 个表达式")
        save_process_result(alpha_expressions, "predefined_alphas_full_process.json")
        
        # 存储所有回测结果
        all_backtest_results = []
        all_monitor_results = []
        all_alpha_stats = []
        
        # 对每个表达式进行回测 - 现在已经改为批量处理
        logging.info(f"步骤2: 批量回测 {len(alpha_expressions)} 个Alpha表达式")
        
        # 批量回测Alpha表达式
        backtest_result = backtest_alpha_expressions(alpha_expressions, region=region, universe=universe, delay=delay)
        
        # 为每次回测创建唯一的文件名
        backtest_filename = f"backtest_submission_result_batch.json"
        save_process_result(backtest_result, backtest_filename)
        
        # 检查回测是否成功提交
        if backtest_result.get("status") != "SUBMITTED":
            logging.error("Alpha表达式批量回测提交失败")
            
        simulation_id = backtest_result.get("simulation_id")
        if not simulation_id:
            logging.error("未获取到模拟ID")
            
        logging.info(f"Alpha表达式批量回测已提交，模拟ID: {simulation_id}")
        
        # 修改后续处理逻辑，适应批量提交的情况
        if len(alpha_expressions) > 0:
            logging.info(f"步骤3: 监控回测进度，模拟ID: {simulation_id}")
            monitor_result = monitor_backtest_progress(simulation_id, 1800)
            
            # 为监控结果创建文件名
            monitor_filename = f"monitor_result_{simulation_id}_batch.json"
            save_process_result(monitor_result, monitor_filename)
            
            # 检查监控结果
            if "error" in monitor_result:
                logging.warning(f"监控过程中出现错误: {monitor_result['error']}")
                
            # 添加到监控结果列表
            monitor_result['simulation_id'] = simulation_id
            all_monitor_results.append(monitor_result)
            
            # 4. 获取Alpha统计结果
            logging.info("步骤4: 获取Alpha统计结果")
            
            # 从监控结果中获取Alpha ID
            alpha_id = None
            if "alpha" in monitor_result:
                alpha_id = monitor_result["alpha"]
                
            # 如果我们有Alpha ID，获取详细统计结果
            if alpha_id:
                logging.info(f"获取到Alpha ID: {alpha_id}")
                alpha_stats = get_alpha_statistics(alpha_id)
                
                # 为统计结果创建文件名
                stats_filename = f"alpha_statistics_{alpha_id}_batch.json"
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
                alpha_stats['alpha_id'] = alpha_id
                all_alpha_stats.append(alpha_stats)
            else:
                logging.warning("未获取到Alpha ID，无法获取详细统计结果")

        # 保存汇总结果
        summary_results = {
            "total_expressions": len(alpha_expressions),
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