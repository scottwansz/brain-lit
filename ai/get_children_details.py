#!/usr/bin/env python3
"""
获取模拟任务中所有子任务的详细信息
"""

import json
import sys
import os
from typing import Dict, Any, List

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from ai.get_simulation_details import get_simulation_details


def get_all_children_details(simulation_id: str) -> List[Dict[str, Any]]:
    """
    获取模拟任务中所有子任务的详细信息
    
    Args:
        simulation_id: 模拟ID
    
    Returns:
        所有子任务的详细信息列表
    """
    # 首先获取模拟的总体信息，其中包括子任务ID列表
    simulation_details = get_simulation_details(simulation_id)
    
    if "error" in simulation_details:
        print(f"获取模拟详情失败: {simulation_details['error']}")
        return []
    
    children_ids = simulation_details.get("children", [])
    
    if not children_ids:
        print("未找到子任务")
        return []
    
    print(f"找到 {len(children_ids)} 个子任务，开始获取详细信息...")
    
    children_details = []
    for i, child_id in enumerate(children_ids):
        print(f"正在获取第 {i+1}/{len(children_ids)} 个子任务详情: {child_id}")
        child_details = get_simulation_details(child_id)
        children_details.append(child_details)
    
    return children_details


def save_children_details(simulation_id: str, children_details: List[Dict[str, Any]]) -> None:
    """
    保存所有子任务的详细信息到文件
    
    Args:
        simulation_id: 模拟ID
        children_details: 子任务详细信息列表
    """
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    output_path = os.path.join(output_dir, f"all_children_details_{simulation_id}.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(children_details, f, ensure_ascii=False, indent=2)
    
    print(f"所有子任务详情已保存到: {output_path}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python get_children_details.py <simulation_id>")
        sys.exit(1)
    
    simulation_id = sys.argv[1]
    
    print(f"正在获取模拟ID的所有子任务详情: {simulation_id}")
    
    # 获取所有子任务的详细信息
    children_details = get_all_children_details(simulation_id)
    
    if children_details:
        # 保存结果
        save_children_details(simulation_id, children_details)
        
        # 显示摘要信息
        print("\n子任务摘要:")
        print("=" * 80)
        for i, child_detail in enumerate(children_details):
            child_id = child_detail.get("id", "Unknown")
            status = child_detail.get("status", "Unknown")
            alpha_id = child_detail.get("alpha", "N/A")
            regular_expr = child_detail.get("regular", "N/A")
            
            print(f"子任务 {i+1}:")
            print(f"  ID: {child_id}")
            print(f"  状态: {status}")
            print(f"  Alpha ID: {alpha_id}")
            print(f"  表达式: {regular_expr}")
            print("-" * 40)
    else:
        print("未能获取到子任务详情")


if __name__ == "__main__":
    main()