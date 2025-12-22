#!/usr/bin/env python3
"""
监控WorldQuant平台Alpha表达式回测进度的工具脚本
"""

import json
import sys
import os
import time
from typing import Dict, Any

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.auth import AutoLoginSession, get_auto_login_session


def monitor_simulation_progress(simulation_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
    """
    监控模拟进度
    
    Args:
        simulation_id: 模拟ID
        max_wait_time: 最大等待时间(秒)
    
    Returns:
        模拟结果
    """
    try:
        # 使用现有的AutoLoginSession
        session = get_auto_login_session()
        
        # 监控模拟进度
        start_time = time.time()
        simulation_url = f"https://api.worldquantbrain.com/simulations/{simulation_id}"
        
        print(f"开始监控模拟进度，最大等待时间: {max_wait_time}秒")
        print(f"模拟URL: {simulation_url}")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = session.get(simulation_url)
                elapsed_time = int(time.time() - start_time)
                print(f"\r检查模拟状态，响应状态码: {response.status_code} 时间: {elapsed_time}", flush=True, end="")
                
                if response.status_code == 200:
                    try:
                        simulation_data = response.json()
                        # 检查响应内容是否是一个简单的值而不是对象
                        # if not isinstance(simulation_data, dict):
                        #     print(f"响应不是一个对象: {simulation_data}")
                        #     continue
                            
                        status = simulation_data.get('status', 'UNKNOWN')
                        # print(f"当前模拟状态: {status}")
                        
                        # 如果模拟已完成，返回结果
                        if status in ['SUCCESS', 'ERROR', 'FAILED', 'COMPLETE']:
                            print(f"\n模拟已完成，最终状态: {status}")  # 添加换行符使输出更清晰
                            # 当状态为ERROR时，获取所有子任务的详细错误信息
                            if status == 'ERROR' and 'children' in simulation_data and simulation_data['children']:
                                children_details = []
                                for i, child_id in enumerate(simulation_data['children']):
                                    child_url = f"https://api.worldquantbrain.com/simulations/{child_id}"
                                    print(f"获取第{i+1}个子任务的详细信息: {child_url}")
                                    child_response = session.get(child_url)
                                    if child_response.status_code == 200:
                                        try:
                                            child_data = child_response.json()
                                            children_details.append(child_data)
                                            print(f"子任务{i+1}详细信息: {json.dumps(child_data, ensure_ascii=False, indent=2)}")
                                        except json.JSONDecodeError:
                                            print(f"无法解析第{i+1}个子任务响应内容: {child_response.text}")
                                    else:
                                        print(f"获取第{i+1}个子任务信息失败，状态码: {child_response.status_code}")
                                        if hasattr(child_response, 'text') and child_response.text:
                                            print(f"响应内容: {child_response.text}")
                                # 将所有子任务的详细信息添加到结果中
                                simulation_data['children_details'] = children_details
                            
                            # 尝试获取更详细的统计信息
                            if 'statistics' not in simulation_data or not simulation_data['statistics']:
                                # 如果响应中没有详细统计信息，尝试获取完整结果
                                detail_response = session.get(simulation_url)
                                if detail_response.status_code == 200:
                                    try:
                                        detailed_data = detail_response.json()
                                        # 检查detailed_data是否为字典类型
                                        if isinstance(detailed_data, dict):
                                            return detailed_data
                                    except json.JSONDecodeError:
                                        pass
                            return simulation_data
                        elif status == 'UNKNOWN':
                            # 如果状态是UNKNOWN，等待一段时间再检查
                            # print("\n状态为UNKNOWN，等待下次检查...")  # 添加换行符使输出更清晰
                            continue
                        
                        # 显示进度信息
                        progress = simulation_data.get('progress', {})
                        if progress:
                            progress_percentage = progress.get('percentage', 0)
                            print(f"\r模拟进度: {progress_percentage}%", flush=True, end="")  # 在同一行更新进度
                            
                        # 显示统计信息
                        statistics = simulation_data.get('statistics', {})
                        if statistics:
                            sharpe = statistics.get('sharpe', 'N/A')
                            fitness = statistics.get('fitness', 'N/A')
                            print(f"\r当前统计: Sharpe={sharpe}, Fitness={fitness}", flush=True, end="")  # 在同一行更新统计信息
                            
                    except json.JSONDecodeError:
                        print(f"\n无法解析响应内容: {response.text}")  # 添加换行符使输出更清晰
                elif response.status_code == 404:
                    print("\n模拟未找到，可能是ID无效")  # 添加换行符使输出更清晰
                    return {"error": "模拟未找到"}
                else:
                    print(f"\n获取模拟状态失败，状态码: {response.status_code}")  # 添加换行符使输出更清晰
                    if hasattr(response, 'text') and response.text:
                        print(f"响应内容: {response.text}")
                
                # 等待一段时间再检查
                time.sleep(10)
                
            except Exception as e:
                print(f"\n检查模拟状态时出错: {str(e)}")  # 添加换行符使输出更清晰
                time.sleep(10)
                continue
        
        # 超时
        print("\n监控超时，模拟可能仍在进行中")  # 添加换行符使输出更清晰
        return {"error": "监控超时，模拟可能仍在进行中"}
        
    except Exception as e:
        error_msg = f"监控模拟进度时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python monitor_simulation.py <simulation_id> [max_wait_time]")
        sys.exit(1)
    
    simulation_id = sys.argv[1]
    max_wait_time = 300  # 默认5分钟
    
    if len(sys.argv) > 2:
        max_wait_time = int(sys.argv[2])
    
    print(f"正在监控模拟ID: {simulation_id}")
    
    # 监控进度
    result = monitor_simulation_progress(simulation_id, max_wait_time)
    
    # 输出结果
    print("\n监控结果:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存结果
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    output_dir = os.path.join(project_root, 'data')
    output_path = os.path.join(output_dir, f"simulation_result_{simulation_id}.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()