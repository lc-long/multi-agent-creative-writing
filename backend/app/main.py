"""
Multi-Agent Creative Writing System - FastAPI Application

主应用入口，配置中间件、路由和启动事件。
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import api_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动和关闭时执行必要的操作。
    """
    # 启动时
    logger.info("Starting Multi-Agent Creative Writing System...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.APP_DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # 创建数据目录
    import os
    os.makedirs("data", exist_ok=True)
    
    yield
    
    # 关闭时
    logger.info("Shutting down Multi-Agent Creative Writing System...")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI: 配置好的应用实例
    """
    app = FastAPI(
        title="Multi-Agent Creative Writing System",
        description="多Agent创意写作系统 - 多个AI Agent协作生成创意故事",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 健康检查端点
    @app.get("/health", tags=["health"])
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
        }
    
    # 根端点
    @app.get("/", tags=["root"])
    async def root():
        """根端点"""
        return {
            "name": "Multi-Agent Creative Writing System",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    return app


# 创建应用实例
app = create_app()


def main():
    """主函数，用于启动应用"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
