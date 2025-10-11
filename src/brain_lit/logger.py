import logging
import sys

def setup_logger(name: str = "brain-lit", level: int = logging.INFO) -> logging.Logger:
    """
    设置并返回一个配置好的logger实例
    
    Args:
        name: logger名称
        level: 日志级别
        
    Returns:
        配置好的logger实例
    """
    # 创建logger实例
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 创建格式化器，包含模块名和行号
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        logger.addHandler(console_handler)
    
    return logger