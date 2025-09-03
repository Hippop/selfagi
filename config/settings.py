"""
系统配置文件
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """系统配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "selfagi"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/selfagi"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    
    # 消息队列配置
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # 任务执行配置
    MAX_CONCURRENT_TASKS: int = 100
    TASK_TIMEOUT: int = 3600  # 秒
    TASK_RETRY_ATTEMPTS: int = 3
    
    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/selfagi.log"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 存储配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()