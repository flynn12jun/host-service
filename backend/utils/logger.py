import structlog
from functools import lru_cache


@lru_cache()
def get_logger(name: str = "host_service"):
    """
    获取结构化日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        BoundLogger: 结构化日志记录器
    """
    return structlog.get_logger(name)