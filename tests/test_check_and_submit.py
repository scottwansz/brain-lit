import unittest

from svc.logger import setup_logger
from svc import check_by_query

logger = setup_logger(__name__)

class TestMain(unittest.TestCase):
    def test_main(self):
        # 添加测试代码
        self.assertEqual(1, 1)

    def test_check_by_query(self):
        # records = query_submittable_alpha_details("USA", "TOP3000", 1, "1", "socialmedia")
        # logger.info(f"Found {len(records)} submittable records")

        query = {
            "region": "USA",
            "universe": "TOP3000",
            "delay": "0",
            "phase": "1",
            "category": "sentiment",
        }

        task_info = {
            "query": query,
            "stop": False,
            "submitted_count": 0,
            "progress": 0,
            "details": "Preparing...",
        }

        # check_alpha(session, 'OgXk5O7', task=task_info)
        check_by_query(task=task_info)

        self.assertEqual(1, 1)