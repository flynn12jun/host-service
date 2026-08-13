import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

import os
import sys

# 确保 /app 在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from core.database import init_db, close_db
from api.routes import router


# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(
        "应用启动",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG
    )
    
    # 初始化数据库
    try:
        await init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error("数据库初始化失败", error=str(e))
    
    yield
    
    # 关闭时
    logger.info("应用关闭")
    await close_db()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HOST轻食多Agent框架 - 基于多Agent协同工作的智能菜品研发工作流系统",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求
    logger.info(
        "请求开始",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown"
    )
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录响应
        logger.info(
            "请求完成",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=f"{duration:.3f}s"
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "请求异常",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration=f"{duration:.3f}s"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "内部服务器错误"}
        )


# 注册路由
app.include_router(router)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# 就绪检查
@app.get("/ready")
async def readiness_check():
    """就绪检查端点"""
    # 可以添加数据库连接检查等
    return {
        "status": "ready",
        "database": "connected",
        "timestamp": time.time()
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )