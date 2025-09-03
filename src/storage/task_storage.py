"""
任务存储接口
定义任务数据的存储和检索方法
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.models import Task, TaskResult, TaskExecutionLog, TaskDependency


class TaskStorage(ABC):
    """任务存储接口"""
    
    @abstractmethod
    async def save_task(self, task: Task) -> bool:
        """
        保存任务
        
        Args:
            task: 要保存的任务
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在返回None
        """
        pass
    
    @abstractmethod
    async def update_task(self, task: Task) -> bool:
        """
        更新任务
        
        Args:
            task: 要更新的任务
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_tasks(self, 
                        status: Optional[str] = None,
                        task_type: Optional[str] = None,
                        priority: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Task]:
        """
        列出任务
        
        Args:
            status: 任务状态过滤
            task_type: 任务类型过滤
            priority: 任务优先级过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def save_task_result(self, result: TaskResult) -> bool:
        """
        保存任务执行结果
        
        Args:
            result: 任务执行结果
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        获取任务执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务执行结果，如果不存在返回None
        """
        pass
    
    @abstractmethod
    async def save_task_log(self, log: TaskExecutionLog) -> bool:
        """
        保存任务执行日志
        
        Args:
            log: 任务执行日志
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def get_task_logs(self, task_id: str, 
                           level: Optional[str] = None,
                           limit: int = 100) -> List[TaskExecutionLog]:
        """
        获取任务执行日志
        
        Args:
            task_id: 任务ID
            level: 日志级别过滤
            limit: 返回数量限制
            
        Returns:
            日志列表
        """
        pass
    
    @abstractmethod
    async def save_task_dependency(self, dependency: TaskDependency) -> bool:
        """
        保存任务依赖关系
        
        Args:
            dependency: 任务依赖关系
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def get_task_dependencies(self, task_id: str) -> List[TaskDependency]:
        """
        获取任务依赖关系
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖关系列表
        """
        pass
    
    @abstractmethod
    async def get_dependent_tasks(self, task_id: str) -> List[TaskDependency]:
        """
        获取依赖该任务的任务列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖该任务的任务列表
        """
        pass
    
    @abstractmethod
    async def search_tasks(self, query: str, 
                          fields: Optional[List[str]] = None,
                          limit: int = 100) -> List[Task]:
        """
        搜索任务
        
        Args:
            query: 搜索查询
            fields: 搜索字段列表
            limit: 返回数量限制
            
        Returns:
            匹配的任务列表
        """
        pass
    
    @abstractmethod
    async def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        pass
    
    @abstractmethod
    async def backup_tasks(self, backup_path: str) -> bool:
        """
        备份任务数据
        
        Args:
            backup_path: 备份路径
            
        Returns:
            是否备份成功
        """
        pass
    
    @abstractmethod
    async def restore_tasks(self, backup_path: str) -> bool:
        """
        恢复任务数据
        
        Args:
            backup_path: 备份路径
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            存储系统是否健康
        """
        pass
    
    @abstractmethod
    async def close(self):
        """关闭存储连接"""
        pass