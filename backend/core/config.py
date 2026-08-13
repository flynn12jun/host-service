from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
from functools import lru_cache
import json


class Settings(BaseSettings):
    """应用配置"""
    
    # App
    APP_NAME: str = "HOST轻食多Agent框架"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/host_light_food"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM - LongCat（美团龙猫）
    LONGCAT_API_KEY: str = ""
    LONGCAT_BASE_URL: str = "https://api.longcat.chat/v1"
    
    # LLM - 智谱 GLM
    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "LongCat-2.0"
    LLM_TEMPERATURE: float = 0.7
    
    # CORS - 使用字符串存储，避免解析问题
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # Workflow
    MAX_REVISION_COUNT: int = 3
    AGENT_TIMEOUT: int = 120  # seconds
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """获取允许的来源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()