import os
import sys

from sidebar import render_sidebar

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages.home import render_main_page
from svc.logger import setup_logger

# 设置logger
logger = setup_logger(__name__)

def main():

    render_sidebar()
    render_main_page()

if __name__ == "__main__":
    main()