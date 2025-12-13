#!/usr/bin/env python3
"""
获取WorldQuant平台Alpha表达式的详细统计结果
"""

import json
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.auth import AutoLoginSession


def get_alpha_details(alpha_id: str) -> Dict[str, Any]:
    """
    获取Alpha的详细统计结果
    
    Args:
        alpha_id: Alpha ID
    
    Returns:
        Alpha的详细统计结果
    """
    try:
        # 使用现有的AutoLoginSession
        session = AutoLoginSession()
        
        # 尝试从环境变量或secrets获取认证信息
        username = os.environ.get("BRAIN_USERNAME") or getattr(session, 'username', None)
        password = os.environ.get("BRAIN_PASSWORD") or getattr(session, 'password', None)
        
        if not username or not password:
            # 尝试从Streamlit secrets获取
            try:
                import streamlit as st
                username = st.secrets.get("brain", {}).get("username")
                password = st.secrets.get("brain", {}).get("password")
            except:
                pass
        
        if username and password:
            session.login_with_credentials(username, password)
        else:
            print("警告: 未找到认证信息，无法获取Alpha详情...", file=sys.stderr)
            return {"error": "未找到认证信息，无法获取Alpha详情"}
        
        # 获取Alpha详情
        alpha_url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
        print(f"正在获取Alpha详情: {alpha_url}")
        
        response = session.get(alpha_url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                alpha_data = response.json()
                return alpha_data
            except json.JSONDecodeError:
                print(f"无法解析响应内容: {response.text}")
                return {"error": "无法解析响应内容", "response_text": response.text}
        elif response.status_code == 404:
            print("Alpha未找到，可能是ID无效")
            return {"error": "Alpha未找到"}
        else:
            print(f"获取Alpha详情失败，状态码: {response.status_code}")
            if hasattr(response, 'text') and response.text:
                print(f"响应内容: {response.text}")
            return {"error": f"获取Alpha详情失败，状态码: {response.status_code}"}
        
    except Exception as e:
        error_msg = f"获取Alpha详情时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python get_alpha_details.py <alpha_id>")
        sys.exit(1)
    
    alpha_id = sys.argv[1]
    
    print(f"正在获取Alpha ID的详细统计结果: {alpha_id}")
    
    # 获取详细结果
    result = get_alpha_details(alpha_id)
    
    # 输出结果
    print("\nAlpha详细统计结果:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存结果
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    output_dir = os.path.join(project_root, 'data')
    output_path = os.path.join(output_dir, f"alpha_details_{alpha_id}.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nAlpha详细结果已保存到: {output_path}")
    
    # 如果有统计信息，单独显示关键指标
    if "is" in result:
        stats = result["is"]
        print("\n关键统计指标:")
        print("-" * 30)
        print(f"Sharpe Ratio: {stats.get('sharpe', 'N/A')}")
        print(f"Fitness: {stats.get('fitness', 'N/A')}")
        print(f"Returns: {stats.get('returns', 'N/A')}")
        print(f"Turnover: {stats.get('turnover', 'N/A')}")
        print(f"Margin: {stats.get('margin', 'N/A')}")
        print(f"Long Count: {stats.get('longCount', 'N/A')}")
        print(f"Short Count: {stats.get('shortCount', 'N/A')}")


if __name__ == "__main__":
    main()