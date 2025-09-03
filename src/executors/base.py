"""
执行器基础接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.core.models import Task


class BaseExecutor(ABC):
    """执行器基础类"""
    
    def __init__(self, name: str, executor_type: str):
        self.name = name
        self.executor_type = executor_type
        self.is_available = True
        self.current_load = 0
        self.max_load = 100
    
    @abstractmethod
    async def execute(self, task: Task) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 要执行的任务
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    async def validate_task(self, task: Task) -> bool:
        """
        验证任务是否可以执行
        
        Args:
            task: 要验证的任务
            
        Returns:
            是否可以执行
        """
        pass
    
    async def pre_execute(self, task: Task) -> Dict[str, Any]:
        """
        任务执行前的准备工作
        
        Args:
            task: 要执行的任务
            
        Returns:
            准备结果
        """
        return {"status": "ready"}
    
    async def post_execute(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        任务执行后的清理工作
        
        Args:
            task: 已执行的任务
            result: 执行结果
            
        Returns:
            清理结果
        """
        return {"status": "cleaned"}
    
    async def handle_error(self, task: Task, error: Exception) -> Dict[str, Any]:
        """
        处理执行错误
        
        Args:
            task: 执行失败的任务
            error: 错误信息
            
        Returns:
            错误处理结果
        """
        return {
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取执行器状态
        
        Returns:
            状态信息
        """
        return {
            "name": self.name,
            "type": self.executor_type,
            "available": self.is_available,
            "current_load": self.current_load,
            "max_load": self.max_load,
            "load_percentage": (self.current_load / self.max_load) * 100 if self.max_load > 0 else 0
        }
    
    def can_accept_task(self) -> bool:
        """
        检查是否可以接受新任务
        
        Returns:
            是否可以接受任务
        """
        return self.is_available and self.current_load < self.max_load
    
    def update_load(self, load_change: int):
        """
        更新当前负载
        
        Args:
            load_change: 负载变化量
        """
        self.current_load = max(0, min(self.max_load, self.current_load + load_change))
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        return self.is_available and self.current_load < self.max_load * 0.9
    
    async def shutdown(self):
        """
        关闭执行器
        """
        self.is_available = False
        self.current_load = 0