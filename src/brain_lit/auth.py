import logging
import os
import requests
import time
from typing import Optional

from brain_lit.logger import setup_logger

logger = logging.getLogger(__name__)

class AutoLoginSession:
    """自动登录会话，在会话失效时自动重新登录"""

    def __init__(self):
        self._session = None
        self.last_login_time = 0
        self.login_refresh_interval = 3600 * 12  # 12小时刷新一次登录
        self.retry_count = 0
        self.max_retries = 3  # 最大重试次数
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None

    def login_with_credentials(self, username: str, password: str):
        """使用提供的用户名和密码执行登录操作"""
        logger.info("正在登录系统...")
        
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        # 创建新会话
        self._session = requests.Session()
        self._session.auth = (username, password)
        self.username = username

        # 发送登录请求
        response = self._session.post('https://api.worldquantbrain.com/authentication')
        logger.info(response.content)

        if response.status_code != 201:
            raise ConnectionError(f"登录失败，状态码: {response.status_code}")

        # 尝试提取用户ID
        try:
            response_json = response.json()
            logger.info('response_data: %s', response_json)
            self.user_id = response_json.get('user', {}).get('id', 'UNKNOWN')
            self.login_refresh_interval = response_json.get('token', {}).get('expiry', 3600 * 4)
        except Exception:
            self.user_id = 'UNKNOWN'

        logger.info("登录成功!")
        self.last_login_time = time.time()
        self.retry_count = 0
        return self._session

    def login(self):
        """执行登录操作并初始化会话（使用环境变量中的凭据）"""
        logger.info("正在登录系统...")
        username = os.getenv('BRAIN_USERNAME')
        password = os.getenv('BRAIN_PASSWORD')

        if not username or not password:
            raise ValueError("未配置环境变量 BRAIN_USERNAME 或 BRAIN_PASSWORD")

        return self.login_with_credentials(username, password)

    def get_time_until_expiry(self) -> int:
        """获取距离登录失效的剩余秒数"""
        if self.last_login_time == 0:
            return 0
        elapsed_time = time.time() - self.last_login_time
        remaining_time = max(0, self.login_refresh_interval - elapsed_time)
        return int(remaining_time)

    def ensure_valid_session(self):
        """确保会话有效，必要时重新登录"""
        current_time = time.time()

        # 检查是否需要刷新登录
        if (current_time - self.last_login_time > self.login_refresh_interval
                or self.retry_count >= self.max_retries):
            # 如果有用户名密码则使用凭据重新登录，否则使用环境变量
            if self.username and self._session and self._session.auth:
                auth = self._session.auth
                self.login_with_credentials(auth[0], auth[1])
            else:
                self.login()

    def request(self, method, url, **kwargs):
        """发送请求并在会话失效时自动重试登录"""
        self.ensure_valid_session()

        try:
            response = self._session.request(method, url, **kwargs)

            # 检测到会话失效
            if response.status_code in (401, 403):
                print(f"会话过期 ({response.status_code})，尝试重新登录...")
                # 如果有用户名密码则使用凭据重新登录，否则使用环境变量
                if self.username and self._session and self._session.auth:
                    auth = self._session.auth
                    self.login_with_credentials(auth[0], auth[1])
                else:
                    self.login()
                response = self._session.request(method, url, **kwargs)

            return response
        except requests.ConnectionError:
            self.retry_count += 1
            print(f"连接失败，重试登录 ({self.retry_count}/{self.max_retries})")
            # 如果有用户名密码则使用凭据重新登录，否则使用环境变量
            if self.username and self._session and self._session.auth:
                auth = self._session.auth
                self.login_with_credentials(auth[0], auth[1])
            else:
                self.login()
            return self._session.request(method, url, **kwargs)

    # 封装常用的HTTP方法
    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request('PATCH', url, **kwargs)

    def head(self, url, **kwargs):
        return self.request('HEAD', url, **kwargs)

    def options(self, url, **kwargs):
        return self.request('OPTIONS', url, **kwargs)

    def close(self):
        """关闭会话"""
        if self._session:
            self._session.close()
            self._session = None
            print("会话已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 使用示例
if __name__ == "__main__":
    from dotenv import load_dotenv
    # 加载.env文件
    load_dotenv()

    logger = setup_logger()
    logger.info("开始执行...")

    username = os.getenv('BRAIN_USERNAME')
    password = os.getenv('BRAIN_PASSWORD')
    if not username or not password:
        logger.error("未配置环境变量 BRAIN_USERNAME 或 BRAIN_PASSWORD")
        exit(1)

    # 根据API特性调整参数
    session = AutoLoginSession()
    session.login_with_credentials(username, password)
    # session.login_refresh_interval = 1800  # 30分钟刷新
    # session.max_retries = 3  # 最多重试3次

    # 调用API（自动处理会话失效）
    try:
        # 获取数据
        url = "https://api.worldquantbrain.com/data-sets?delay=0&instrumentType=EQUITY&limit=20&offset=0&region=EUR&universe=TOP2500"
        data_response = session.get(url)
        print(data_response.json())

        session.delete("https://api.worldquantbrain.com/authentication")

        data_response = session.get(url)
        print(data_response.json())

        # 提交数据
        # payload = {"key": "value"}
        # submit_response = session.post("https://api.worldquantbrain.com/submit", json=payload)
        # print(submit_response.status_code)

    finally:
        # 手动关闭会话（上下文管理器可自动处理）
        session.close()