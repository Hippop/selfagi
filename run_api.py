#!/usr/bin/env python3
"""
SelfAGI API服务启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.app import app
import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print(f"启动 {settings.PROJECT_NAME} API服务...")
    print(f"服务地址: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"API文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS
    )