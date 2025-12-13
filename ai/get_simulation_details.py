#!/usr/bin/env python3
"""
获取WorldQuant平台Alpha表达式回测详细结果的工具脚本
"""

import json
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.auth import AutoLoginSession, get_auto_login_session


def get_simulation_details(simulation_id: str) -> Dict[str, Any]:
    """
    获取模拟的详细结果
    
    Args:
        simulation_id: 模拟ID
    
    Returns:
        模拟的详细结果
    """
    try:
        session = get_auto_login_session()
        
        # 获取模拟详情
        simulation_url = f"https://api.worldquantbrain.com/simulations/{simulation_id}"
        print(f"正在获取模拟详情: {simulation_url}")
        
        response = session.get(simulation_url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                simulation_data = response.json()
                
                # 当模拟状态为ERROR时，获取所有子任务的详细错误信息
                status = simulation_data.get('status', '')
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
                                print(f"第{i+1}个子任务详细信息: {json.dumps(child_data, ensure_ascii=False, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"无法解析第{i+1}个子任务响应内容: {child_response.text}")
                        else:
                            print(f"获取第{i+1}个子任务信息失败，状态码: {child_response.status_code}")
                            if hasattr(child_response, 'text') and child_response.text:
                                print(f"响应内容: {child_response.text}")
                    # 将所有子任务的详细信息添加到结果中
                    simulation_data['children_details'] = children_details
                
                return simulation_data
            except json.JSONDecodeError:
                print(f"无法解析响应内容: {response.text}")
                return {"error": "无法解析响应内容", "response_text": response.text}
        elif response.status_code == 404:
            print("模拟未找到，可能是ID无效")
            return {"error": "模拟未找到"}
        else:
            print(f"获取模拟详情失败，状态码: {response.status_code}")
            if hasattr(response, 'text') and response.text:
                print(f"响应内容: {response.text}")
            return {"error": f"获取模拟详情失败，状态码: {response.status_code}"}
        
    except Exception as e:
        error_msg = f"获取模拟详情时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python get_simulation_details.py <simulation_id>")
        sys.exit(1)
    
    simulation_id = sys.argv[1]
    
    print(f"正在获取模拟ID的详细结果: {simulation_id}")
    
    # 获取详细结果
    result = get_simulation_details(simulation_id)
    
    # 输出结果
    print("\n模拟详细结果:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存结果
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    output_dir = os.path.join(project_root, 'data')
    output_path = os.path.join(output_dir, f"simulation_details_{simulation_id}.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: {output_path}")
    
    # 如果有统计信息，单独显示关键指标
    if "statistics" in result:
        stats = result["statistics"]
        print("\n关键统计指标:")
        print("-" * 30)
        print(f"Sharpe Ratio: {stats.get('sharpe', 'N/A')}")
        print(f"Fitness: {stats.get('fitness', 'N/A')}")
        print(f"Returns: {stats.get('returns', 'N/A')}")
        print(f"Turnover: {stats.get('turnover', 'N/A')}")
        print(f"Margin: {stats.get('margin', 'N/A')}")


if __name__ == "__main__":
    main()