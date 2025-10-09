import unittest

from brain_lit.logger import setup_logger
from brain_lit.svc.auth import get_auto_login_session
from brain_lit.svc.check import check_alpha, check_by_query

logger = setup_logger(__name__)

class TestMain(unittest.TestCase):
    def test_main(self):
        # 添加测试代码
        self.assertEqual(1, 1)

    def test_check_by_query(self):
        # records = query_submittable_alpha_details("USA", "TOP3000", 1, "1", "socialmedia")
        # logger.info(f"Found {len(records)} submittable records")

        query = {
            "region": "AMR",
            "universe": "TOP600",
            "delay": "0",
            "phase": "1",
            "category": "analyst",
        }

        task_info = {
            "stop": False,
            "submitted_count": 0,
            "progress": 0,
            "details": "Preparing...",
        }

        session = get_auto_login_session()

        # check_alpha(session, 'OgXk5O7', task=task_info)
        check_by_query(session, query, task=task_info)

        self.assertEqual(1, 1)