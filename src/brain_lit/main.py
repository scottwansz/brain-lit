from .logger import setup_logger

# 设置日志
logger = setup_logger()

def main():
    logger.info("Starting brain-lit application")
    print("Hello from brain-lit!")
    logger.info("Application finished successfully")

if __name__ == "__main__":
    main()