#!/usr/bin/env python3
"""
获取WorldQuant平台受限文档的工具脚本
"""

import json
import sys
import os

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.auth import AutoLoginSession


def fetch_worldquant_document(url: str, output_file: str = None) -> str:
    """
    获取WorldQuant平台受限文档
    
    Args:
        url: 文档URL
        output_file: 输出文件路径，如果为None则输出到控制台
    
    Returns:
        文档内容
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
            print("警告: 未找到认证信息，尝试匿名访问...", file=sys.stderr)
        
        # 发送请求获取文档
        response = session.get(url)
        
        if response.status_code == 200:
            content = response.text
            
            # 输出到文件或控制台
            if output_file:
                # 确保输出目录存在
                project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
                output_dir = os.path.join(project_root, 'data')
                output_path = os.path.join(output_dir, output_file)
                os.makedirs(output_dir, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"文档已保存到: {output_path}")
            else:
                print(content)
                
            return content
        else:
            error_msg = f"获取文档失败，状态码: {response.status_code}"
            print(error_msg, file=sys.stderr)
            return error_msg
            
    except Exception as e:
        error_msg = f"获取文档时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        return error_msg


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python fetch_restricted_doc.py <URL> [输出文件] [--json]")
        print("示例: python fetch_restricted_doc.py https://platform.worldquantbrain.com/learn/documentation/brain-api/understanding-simulation-limits")
        sys.exit(1)
    
    # 获取URL参数
    doc_url = sys.argv[1]
    
    # 检查命令行参数
    output_file = None
    json_output = False
    
    for arg in sys.argv[2:]:
        if arg == "--json":
            json_output = True
        else:
            output_file = arg
    
    # 获取文档
    content = fetch_worldquant_document(doc_url, output_file)
    
    # 如果需要JSON格式输出
    if json_output:
        result = {
            "url": doc_url,
            "status": "success" if content and not content.startswith("获取文档失败") else "error",
            "content": content
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()