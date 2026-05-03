"""
Multi-Agent Creative Writing System - Configuration

使用pydantic-settings管理配置，支持从环境变量和.env文件加载配置。
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_ENV: str = Field(default="development", description="应用环境")
    APP_DEBUG: bool = Field(default=True, description="调试模式")
    APP_HOST: str = Field(default="0.0.0.0", description="监听地址")
    APP_PORT: int = Field(default=8000, description="监听端口")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/writing.db",
        description="数据库连接字符串"
    )
    
    # LLM配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_API_BASE: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API Base URL"
    )
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI模型名称")
    
    # Agent配置
    MAX_TOKENS: int = Field(default=4000, description="最大Token数")
    TEMPERATURE: float = Field(default=0.7, description="温度参数")
    DISCUSSION_ROUNDS: int = Field(default=3, description="讨论轮数")
    AGENT_TIMEOUT: int = Field(default=60, description="Agent超时时间（秒）")
    
    # 安全配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS允许的源"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 速率限制
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求数限制")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings
