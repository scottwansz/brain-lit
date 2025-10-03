import unittest
import sys
import os

from brain_lit.svc.alpha_query import query_alphas_simulation_stats

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# 直接导入main函数
from brain_lit.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # 简单测试确保main函数可以运行
        main()
        self.assertTrue(True)

    def test_query_alphas_simulation_stats(self):
        # 测试查询Alpha模拟状态统计功能
        result = query_alphas_simulation_stats("USA", "TOP3000", 1)
        print(result)
        # 验证返回结果是一个列表
        self.assertIsInstance(result, list)
        # 如果有数据，验证每条记录都有simulated和count字段
        if result:
            for record in result:
                self.assertIn('simulated', record)
                self.assertIn('count', record)

if __name__ == '__main__':
    unittest.main()