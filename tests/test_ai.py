import json
import logging

from ai.generate_alpha_by_ai import generate_alphas

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - Line: %(lineno)d')

"""
使用WorldQuant平台内容生成Alpha表达式的AI工具
"""
ai_output = generate_alphas()
with open('ai_output.json', 'w') as f:
    json.dump(ai_output, f, indent=4, ensure_ascii=False)

logging.info("AI输出已保存到ai_output.json")