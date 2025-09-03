"""
任务管理器
负责任务的创建、分解、调度和监控
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from loguru import logger

from src.core.models import (
    Task, TaskStatus, TaskPriority, TaskType, 
    TaskResult, TaskDependency, TaskExecutionLog
)
from src.executors.base import BaseExecutor
from src.storage.task_storage import TaskStorage
from src.utils.task_analyzer import TaskAnalyzer


class TaskManager:
    """任务管理器"""
    
    def __init__(self, storage: TaskStorage, analyzer: TaskAnalyzer):
        self.storage = storage
        self.analyzer = analyzer
        self.executors: Dict[str, BaseExecutor] = {}
        self.running_tasks: Set[str] = set()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent_tasks = 100
        
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建新任务"""
        try:
            # 创建任务实例
            task = Task(**task_data)
            
            # 分析任务依赖
            dependencies = await self.analyzer.analyze_dependencies(task)
            task.dependencies = dependencies
            
            # 保存任务到存储
            await self.storage.save_task(task)
            
            # 记录日志
            await self._log_task_event(task.task_id, "INFO", f"任务创建成功: {task.name}")
            
            logger.info(f"任务创建成功: {task.task_id} - {task.name}")
            return task
            
        except Exception as e:
            logger.error(f"任务创建失败: {str(e)}")
            raise
    
    async def decompose_task(self, task: Task) -> List[Task]:
        """分解复杂任务为子任务"""
        try:
            # 使用任务分析器分解任务
            sub_tasks = await self.analyzer.decompose_task(task)
            
            # 为每个子任务设置依赖关系
            for i, sub_task in enumerate(sub_tasks):
                if i > 0:
                    sub_task.dependencies = [sub_tasks[i-1].task_id]
                sub_task.priority = task.priority
                sub_task.category = f"{task.category}_subtask"
                
                # 保存子任务
                await self.storage.save_task(sub_task)
            
            # 更新原任务
            task.dependencies = [sub_tasks[-1].task_id] if sub_tasks else []
            await self.storage.update_task(task)
            
            await self._log_task_event(task.task_id, "INFO", f"任务分解完成，生成 {len(sub_tasks)} 个子任务")
            
            return sub_tasks
            
        except Exception as e:
            logger.error(f"任务分解失败: {str(e)}")
            raise
    
    async def schedule_task(self, task: Task) -> bool:
        """调度任务执行"""
        try:
            # 检查任务依赖是否满足
            if not await self._check_dependencies(task):
                await self._log_task_event(task.task_id, "INFO", "任务依赖未满足，等待中")
                return False
            
            # 检查资源是否足够
            if not await self._check_resources(task):
                await self._log_task_event(task.task_id, "WARNING", "资源不足，等待中")
                return False
            
            # 将任务加入队列
            await self.task_queue.put(task)
            await self._log_task_event(task.task_id, "INFO", "任务已加入执行队列")
            
            return True
            
        except Exception as e:
            logger.error(f"任务调度失败: {str(e)}")
            return False
    
    async def execute_task(self, task: Task) -> TaskResult:
        """执行任务"""
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self.storage.update_task(task)
            
            self.running_tasks.add(task.task_id)
            await self._log_task_event(task.task_id, "INFO", "任务开始执行")
            
            # 选择执行器
            executor = self._select_executor(task)
            if not executor:
                raise Exception(f"未找到合适的执行器: {task.type}")
            
            # 执行任务
            start_time = datetime.utcnow()
            result = await executor.execute(task)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            await self.storage.update_task(task)
            
            # 创建执行结果
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )
            await self.storage.save_task_result(task_result)
            
            await self._log_task_event(task.task_id, "INFO", "任务执行完成")
            
            return task_result
            
        except Exception as e:
            # 处理执行失败
            await self._handle_task_failure(task, str(e))
            raise
            
        finally:
            self.running_tasks.discard(task.task_id)
    
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            task = await self.storage.get_task(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PAUSED
                await self.storage.update_task(task)
                await self._log_task_event(task_id, "INFO", "任务已暂停")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"暂停任务失败: {str(e)}")
            return False
    
    async def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            task = await self.storage.get_task(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PAUSED:
                # 重新调度任务
                return await self.schedule_task(task)
            
            return False
            
        except Exception as e:
            logger.error(f"恢复任务失败: {str(e)}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            task = await self.storage.get_task(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.CANCELLED
                await self.storage.update_task(task)
                await self._log_task_event(task_id, "INFO", "任务已取消")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        try:
            task = await self.storage.get_task(task_id)
            return task.status if task else None
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}")
            return None
    
    async def get_running_tasks(self) -> List[Task]:
        """获取正在运行的任务"""
        try:
            return [await self.storage.get_task(task_id) for task_id in self.running_tasks]
        except Exception as e:
            logger.error(f"获取运行中任务失败: {str(e)}")
            return []
    
    async def get_task_history(self, task_id: str) -> List[TaskExecutionLog]:
        """获取任务执行历史"""
        try:
            return await self.storage.get_task_logs(task_id)
        except Exception as e:
            logger.error(f"获取任务历史失败: {str(e)}")
            return []
    
    async def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖是否满足"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = await self.storage.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _check_resources(self, task: Task) -> bool:
        """检查资源是否足够"""
        # 检查并发任务数量
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return False
        
        # 这里可以添加更多资源检查逻辑
        # 如CPU、内存、磁盘空间等
        
        return True
    
    def _select_executor(self, task: Task) -> Optional[BaseExecutor]:
        """选择合适的执行器"""
        executor_key = f"{task.type}_executor"
        return self.executors.get(executor_key)
    
    async def _handle_task_failure(self, task: Task, error_message: str):
        """处理任务执行失败"""
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        await self.storage.update_task(task)
        
        # 创建失败结果
        task_result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            error_message=error_message
        )
        await self.storage.save_task_result(task_result)
        
        await self._log_task_event(task.task_id, "ERROR", f"任务执行失败: {error_message}")
    
    async def _log_task_event(self, task_id: str, level: str, message: str):
        """记录任务事件日志"""
        log = TaskExecutionLog(
            task_id=task_id,
            level=level,
            message=message
        )
        await self.storage.save_task_log(log)
    
    def register_executor(self, task_type: TaskType, executor: BaseExecutor):
        """注册任务执行器"""
        executor_key = f"{task_type}_executor"
        self.executors[executor_key] = executor
        logger.info(f"注册执行器: {executor_key}")
    
    async def start_scheduler(self):
        """启动任务调度器"""
        logger.info("任务调度器启动")
        asyncio.create_task(self._scheduler_loop())
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while True:
            try:
                # 从队列获取任务
                task = await self.task_queue.get()
                
                # 检查任务是否仍然有效
                current_task = await self.storage.get_task(task.task_id)
                if not current_task or current_task.status != TaskStatus.PENDING:
                    continue
                
                # 执行任务
                asyncio.create_task(self.execute_task(current_task))
                
            except Exception as e:
                logger.error(f"调度器错误: {str(e)}")
                await asyncio.sleep(1)