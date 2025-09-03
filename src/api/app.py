"""
FastAPI应用
提供RESTful API接口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn

from src.main import SelfAGISystem
from src.core.models import Task, TaskStatus, TaskPriority, TaskType, UserGoal, GoalStatus, GoalDependency
from config.settings import settings


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="自主任务执行系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局系统实例
system: Optional[SelfAGISystem] = None


# 请求模型
class CreateTaskRequest(BaseModel):
    name: str
    description: str
    type: str
    priority: str = "normal"
    actions: List[Dict[str, Any]]
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    timeout: Optional[int] = None


class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class TaskFilterRequest(BaseModel):
    status: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[str] = None
    limit: int = 100
    offset: int = 0


class SearchRequest(BaseModel):
    query: str
    fields: Optional[List[str]] = None
    limit: int = 100


class CreateGoalRequest(BaseModel):
    """创建目标请求模型"""
    title: str
    description: str
    priority: str = "normal"
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    target_completion_date: Optional[str] = None
    estimated_effort: Optional[int] = None
    parent_goal: Optional[str] = None


class UpdateGoalRequest(BaseModel):
    """更新目标请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    target_completion_date: Optional[str] = None
    estimated_effort: Optional[int] = None
    progress_percentage: Optional[float] = None


class GoalFilterRequest(BaseModel):
    """目标过滤请求模型"""
    status: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    limit: int = 100
    offset: int = 0


# 响应模型
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global system
    
    try:
        # 初始化系统
        system = SelfAGISystem()
        await system.initialize()
        
        # 启动系统
        await system.start()
        
        print("SelfAGI系统启动成功")
        
        # 挂载静态文件
        import os
        static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
            print(f"静态文件服务已挂载: {static_dir}")
        
    except Exception as e:
        print(f"SelfAGI系统启动失败: {str(e)}")
        raise


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global system
    
    if system:
        try:
            await system.stop()
            print("SelfAGI系统已关闭")
        except Exception as e:
            print(f"SelfAGI系统关闭失败: {str(e)}")


# 根路径重定向到前端页面
@app.get("/")
async def root():
    """根路径，返回前端页面"""
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {"message": "SelfAGI系统API", "docs": "/docs"}


# 健康检查
@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查接口"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 获取系统状态
        status = await system.get_system_info()
        
        return ApiResponse(
            success=True,
            message="系统运行正常",
            data=status
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="系统异常",
            error=str(e)
        )


# 系统信息
@app.get("/system/info", response_model=ApiResponse)
async def get_system_info():
    """获取系统信息"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        info = await system.get_system_info()
        
        return ApiResponse(
            success=True,
            message="获取系统信息成功",
            data=info
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取系统信息失败",
            error=str(e)
        )


# 系统状态
@app.get("/system/status", response_model=ApiResponse)
async def get_system_status():
    """获取系统状态"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.system_coordinator:
            raise HTTPException(status_code=503, detail="系统协调器未初始化")
        
        status = await system.system_coordinator.get_system_status()
        
        return ApiResponse(
            success=True,
            message="获取系统状态成功",
            data=status
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取系统状态失败",
            error=str(e)
        )


# 性能指标
@app.get("/system/metrics", response_model=ApiResponse)
async def get_performance_metrics():
    """获取性能指标"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.system_coordinator:
            raise HTTPException(status_code=503, detail="系统协调器未初始化")
        
        metrics = await system.system_coordinator.get_performance_metrics()
        
        return ApiResponse(
            success=True,
            message="获取性能指标成功",
            data=metrics
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取性能指标失败",
            error=str(e)
        )


# 创建任务
@app.post("/tasks", response_model=ApiResponse)
async def create_task(request: CreateTaskRequest):
    """创建任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        # 验证任务类型
        try:
            task_type = TaskType(request.type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的任务类型: {request.type}")
        
        # 验证优先级
        try:
            priority = TaskPriority(request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的优先级: {request.priority}")
        
        # 构建任务数据
        task_data = {
            "name": request.name,
            "description": request.description,
            "type": task_type,
            "priority": priority,
            "actions": request.actions,
            "tags": request.tags or [],
            "category": request.category,
            "timeout": request.timeout
        }
        
        # 创建任务
        task = await system.task_manager.create_task(task_data)
        
        return ApiResponse(
            success=True,
            message="任务创建成功",
            data={
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status,
                "created_at": task.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务创建失败",
            error=str(e)
        )


# 获取任务
@app.get("/tasks/{task_id}", response_model=ApiResponse)
async def get_task(task_id: str):
    """获取任务详情"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        task = await system.storage.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return ApiResponse(
            success=True,
            message="获取任务成功",
            data=task.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取任务失败",
            error=str(e)
        )


# 更新任务
@app.put("/tasks/{task_id}", response_model=ApiResponse)
async def update_task(task_id: str, request: UpdateTaskRequest):
    """更新任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        # 获取任务
        task = await system.storage.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新字段
        if request.name is not None:
            task.name = request.name
        
        if request.description is not None:
            task.description = request.description
        
        if request.priority is not None:
            try:
                task.priority = TaskPriority(request.priority)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的优先级: {request.priority}")
        
        if request.status is not None:
            try:
                task.status = TaskStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {request.status}")
        
        if request.tags is not None:
            task.tags = request.tags
        
        if request.category is not None:
            task.category = request.category
        
        # 保存更新
        success = await system.storage.update_task(task)
        
        if not success:
            raise HTTPException(status_code=500, detail="任务更新失败")
        
        return ApiResponse(
            success=True,
            message="任务更新成功",
            data={
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status,
                "updated_at": task.updated_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务更新失败",
            error=str(e)
        )


# 删除任务
@app.delete("/tasks/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: str):
    """删除任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        # 删除任务
        success = await system.storage.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或删除失败")
        
        return ApiResponse(
            success=True,
            message="任务删除成功",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务删除失败",
            error=str(e)
        )


# 列出任务
@app.post("/tasks/list", response_model=ApiResponse)
async def list_tasks(request: TaskFilterRequest):
    """列出任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        # 获取任务列表
        tasks = await system.storage.list_tasks(
            status=request.status,
            task_type=request.task_type,
            priority=request.priority,
            limit=request.limit,
            offset=request.offset
        )
        
        # 转换为字典列表
        task_list = [task.dict() for task in tasks]
        
        return ApiResponse(
            success=True,
            message="获取任务列表成功",
            data={
                "tasks": task_list,
                "total": len(task_list),
                "limit": request.limit,
                "offset": request.offset
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取任务列表失败",
            error=str(e)
        )


# 搜索任务
@app.post("/tasks/search", response_model=ApiResponse)
async def search_tasks(request: SearchRequest):
    """搜索任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        # 搜索任务
        tasks = await system.storage.search_tasks(
            query=request.query,
            fields=request.fields,
            limit=request.limit
        )
        
        # 转换为字典列表
        task_list = [task.dict() for task in tasks]
        
        return ApiResponse(
            success=True,
            message="搜索任务成功",
            data={
                "tasks": task_list,
                "query": request.query,
                "total": len(task_list)
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="搜索任务失败",
            error=str(e)
        )


# 获取任务状态
@app.get("/tasks/{task_id}/status", response_model=ApiResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        status = await system.task_manager.get_task_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return ApiResponse(
            success=True,
            message="获取任务状态成功",
            data={
                "task_id": task_id,
                "status": status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取任务状态失败",
            error=str(e)
        )


# 暂停任务
@app.post("/tasks/{task_id}/pause", response_model=ApiResponse)
async def pause_task(task_id: str):
    """暂停任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        success = await system.task_manager.pause_task(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="任务暂停失败")
        
        return ApiResponse(
            success=True,
            message="任务暂停成功",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务暂停失败",
            error=str(e)
        )


# 恢复任务
@app.post("/tasks/{task_id}/resume", response_model=ApiResponse)
async def resume_task(task_id: str):
    """恢复任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        success = await system.task_manager.resume_task(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="任务恢复失败")
        
        return ApiResponse(
            success=True,
            message="任务恢复成功",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务恢复失败",
            error=str(e)
        )


# 取消任务
@app.post("/tasks/{task_id}/cancel", response_model=ApiResponse)
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        success = await system.task_manager.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="任务取消失败")
        
        return ApiResponse(
            success=True,
            message="任务取消成功",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="任务取消失败",
            error=str(e)
        )


# 获取任务历史
@app.get("/tasks/{task_id}/history", response_model=ApiResponse)
async def get_task_history(task_id: str, level: Optional[str] = None, limit: int = 100):
    """获取任务执行历史"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.task_manager:
            raise HTTPException(status_code=503, detail="任务管理器未初始化")
        
        logs = await system.task_manager.get_task_history(task_id)
        
        # 过滤日志级别
        if level:
            logs = [log for log in logs if log.level == level]
        
        # 限制数量
        logs = logs[:limit]
        
        # 转换为字典列表
        log_list = [log.dict() for log in logs]
        
        return ApiResponse(
            success=True,
            message="获取任务历史成功",
            data={
                "task_id": task_id,
                "logs": log_list,
                "total": len(log_list)
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取任务历史失败",
            error=str(e)
        )


# 获取任务统计
@app.get("/tasks/statistics", response_model=ApiResponse)
async def get_task_statistics():
    """获取任务统计信息"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        if not system.storage:
            raise HTTPException(status_code=503, detail="存储系统未初始化")
        
        stats = await system.storage.get_task_statistics()
        
        return ApiResponse(
            success=True,
            message="获取任务统计成功",
            data=stats
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="获取任务统计失败",
            error=str(e)
        )


# 创建示例任务
@app.post("/tasks/sample", response_model=ApiResponse)
async def create_sample_task():
    """创建示例任务"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        task = await system.create_sample_task()
        
        if not task:
            raise HTTPException(status_code=500, detail="示例任务创建失败")
        
        return ApiResponse(
            success=True,
            message="示例任务创建成功",
            data={
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message="示例任务创建失败",
            error=str(e)
        )


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "内部服务器错误",
            "error": str(exc)
        }
    )


# ==================== 用户目标相关API ====================

# 创建用户目标
@app.post("/goals", response_model=ApiResponse)
async def create_goal(request: CreateGoalRequest):
    """创建用户目标"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 创建目标对象
        goal = UserGoal(
            title=request.title,
            description=request.description,
            priority=TaskPriority(request.priority),
            category=request.category,
            tags=request.tags or [],
            estimated_effort=request.estimated_effort,
            parent_goal=request.parent_goal
        )
        
        # 这里应该调用系统的目标管理功能
        # 暂时返回创建的目标
        return ApiResponse(
            success=True,
            message="目标创建成功",
            data=goal.dict()
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="目标创建失败",
            error=str(e)
        )


# 获取用户目标列表
@app.post("/goals/list", response_model=ApiResponse)
async def get_goals_list(request: GoalFilterRequest):
    """获取用户目标列表"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 这里应该调用系统的目标查询功能
        # 暂时返回示例数据
        sample_goals = [
            {
                "goal_id": "goal-1",
                "title": "开发Web应用",
                "description": "创建一个完整的Web应用程序",
                "status": "in_progress",
                "progress_percentage": 45.0,
                "tasks": ["task-1", "task-2", "task-3"],
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "goal_id": "goal-2", 
                "title": "学习机器学习",
                "description": "掌握机器学习基础知识和实践",
                "status": "pending",
                "progress_percentage": 0.0,
                "tasks": ["task-4", "task-5"],
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        return ApiResponse(
            success=True,
            message="目标列表获取成功",
            data=sample_goals
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="目标列表获取失败",
            error=str(e)
        )


# 获取单个用户目标详情
@app.get("/goals/{goal_id}", response_model=ApiResponse)
async def get_goal_detail(goal_id: str):
    """获取用户目标详情"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 这里应该调用系统的目标查询功能
        # 暂时返回示例数据
        sample_goal = {
            "goal_id": goal_id,
            "title": "开发Web应用",
            "description": "创建一个完整的Web应用程序，包括前端界面和后端API",
            "status": "in_progress",
            "progress_percentage": 45.0,
            "priority": "high",
            "category": "development",
            "tags": ["web", "development", "fullstack"],
            "tasks": [
                {
                    "task_id": "task-1",
                    "name": "设计数据库架构",
                    "status": "completed",
                    "description": "设计并创建数据库表结构"
                },
                {
                    "task_id": "task-2", 
                    "name": "开发后端API",
                    "status": "in_progress",
                    "description": "实现RESTful API接口"
                },
                {
                    "task_id": "task-3",
                    "name": "开发前端界面",
                    "status": "pending", 
                    "description": "创建用户界面和交互逻辑"
                }
            ],
            "sub_goals": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "target_completion_date": "2024-02-01T00:00:00Z"
        }
        
        return ApiResponse(
            success=True,
            message="目标详情获取成功",
            data=sample_goal
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="目标详情获取失败",
            error=str(e)
        )


# 获取目标的任务依赖图
@app.get("/goals/{goal_id}/dependency-graph", response_model=ApiResponse)
async def get_goal_dependency_graph(goal_id: str):
    """获取目标的任务依赖图"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 这里应该调用系统的依赖图生成功能
        # 暂时返回示例数据
        dependency_graph = {
            "nodes": [
                {
                    "id": "task-1",
                    "label": "设计数据库架构",
                    "type": "task",
                    "status": "completed",
                    "priority": "high"
                },
                {
                    "id": "task-2",
                    "label": "开发后端API", 
                    "type": "task",
                    "status": "in_progress",
                    "priority": "high"
                },
                {
                    "id": "task-3",
                    "label": "开发前端界面",
                    "type": "task", 
                    "status": "pending",
                    "priority": "normal"
                },
                {
                    "id": "task-4",
                    "label": "集成测试",
                    "type": "task",
                    "status": "pending",
                    "priority": "normal"
                }
            ],
            "edges": [
                {
                    "from": "task-1",
                    "to": "task-2",
                    "type": "dependency",
                    "label": "数据库设计完成后才能开发API"
                },
                {
                    "from": "task-2", 
                    "to": "task-3",
                    "type": "dependency",
                    "label": "API开发完成后才能开发前端"
                },
                {
                    "from": "task-3",
                    "to": "task-4",
                    "type": "dependency", 
                    "label": "前后端都完成后进行集成测试"
                }
            ]
        }
        
        return ApiResponse(
            success=True,
            message="依赖图获取成功",
            data=dependency_graph
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="依赖图获取失败",
            error=str(e)
        )


# 更新用户目标
@app.put("/goals/{goal_id}", response_model=ApiResponse)
async def update_goal(goal_id: str, request: UpdateGoalRequest):
    """更新用户目标"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 这里应该调用系统的目标更新功能
        return ApiResponse(
            success=True,
            message="目标更新成功",
            data={"goal_id": goal_id}
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="目标更新失败",
            error=str(e)
        )


# 删除用户目标
@app.delete("/goals/{goal_id}", response_model=ApiResponse)
async def delete_goal(goal_id: str):
    """删除用户目标"""
    try:
        if not system:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        # 这里应该调用系统的目标删除功能
        return ApiResponse(
            success=True,
            message="目标删除成功",
            data={"goal_id": goal_id}
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="目标删除失败",
            error=str(e)
        )


# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS
    )