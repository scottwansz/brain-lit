import unittest
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# 直接导入main函数
from brain_lit.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # 简单测试确保main函数可以运行
        main()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()