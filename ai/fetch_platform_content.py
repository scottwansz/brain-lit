#!/usr/bin/env python3
"""
获取WorldQuant平台受限内容的工具脚本
"""

import json
import sys
import os
from typing import List, Dict

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.auth import AutoLoginSession, get_auto_login_session


def fetch_worldquant_contents(urls: List[str]) -> Dict[str, str]:
    """
    获取WorldQuant平台多个页面的内容
    
    Args:
        urls: 要获取内容的URL列表
    
    Returns:
        字典，键为URL，值为对应的内容
    """
    contents = {}
    
    try:
        # 使用现有的AutoLoginSession
        session = get_auto_login_session()
        
        # 获取每个URL的内容
        for url in urls:
            try:
                print(f"正在获取: {url}")
                response = session.get(url)
                
                if response.status_code == 200:
                    contents[url] = response.text
                    print(f"成功获取: {url}")
                else:
                    error_msg = f"获取 {url} 失败，状态码: {response.status_code}"
                    print(error_msg, file=sys.stderr)
                    contents[url] = error_msg
            except Exception as e:
                error_msg = f"获取 {url} 时发生错误: {str(e)}"
                print(error_msg, file=sys.stderr)
                contents[url] = error_msg
                
    except Exception as e:
        error_msg = f"初始化会话时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {url: error_msg for url in urls}
    
    return contents


def save_contents_to_data(contents: Dict[str, str], filename: str = "platform_content.json"):
    """
    将获取到的内容保存到data目录下的JSON文件中
    
    Args:
        contents: 内容字典
        filename: 保存的文件名
    """
    # 确保输出目录存在
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    output_dir = os.path.join(project_root, 'data')
    output_path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存内容
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(contents, f, ensure_ascii=False, indent=2)
    
    print(f"内容已保存到: {output_path}")


def main():
    """主函数"""
    # WorldQuant平台的受限链接
    urls = [
        "https://api.worldquantbrain.com/data-sets?category=sentiment&delay=1&instrumentType=EQUITY&limit=20&offset=0&region=IND&universe=TOP500",
    ]
    
    # 获取内容
    contents = fetch_worldquant_contents(urls)
    
    # 添加字段信息
    try:
        from svc.datafields import get_multi_set_fields
        field_data = get_multi_set_fields(['sentiment21', 'sentiment23', 'sentiment26'], delay=1, region='IND', universe='TOP500')
        contents['data_fields'] = str(list(field_data.keys()))
    except Exception as e:
        print(f"获取字段信息时出错: {e}")
    
    # 保存内容
    save_contents_to_data(contents, "platform_content.json")
    
    # 如果有输出文件参数，则也保存为HTML格式
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        output_dir = os.path.join(project_root, 'data')
        output_path = os.path.join(output_dir, output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for url, content in contents.items():
                f.write(f"<h1>{url}</h1>\n")
                f.write(f"<div>{content}</div>\n\n")
        
        print(f"内容已保存到: {output_path}")


if __name__ == "__main__":
    main()