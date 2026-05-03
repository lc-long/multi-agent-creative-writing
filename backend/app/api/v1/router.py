"""
API v1 Router

汇总所有API路由。
"""

from fastapi import APIRouter

from app.api.v1.stories import router as stories_router
from app.api.v1.agents import router as agents_router

# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(stories_router, prefix="/stories", tags=["stories"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])


@api_router.get("/health", tags=["health"])
async def api_health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "version": "v1",
    }
