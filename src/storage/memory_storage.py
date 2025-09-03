"""
内存存储实现
用于开发和测试环境
"""
import json
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from src.storage.task_storage import TaskStorage
from src.core.models import Task, TaskResult, TaskExecutionLog, TaskDependency


class MemoryTaskStorage(TaskStorage):
    """内存任务存储实现"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_logs: Dict[str, List[TaskExecutionLog]] = {}
        self.task_dependencies: Dict[str, List[TaskDependency]] = {}
        self.task_counter = 0
        
        logger.info("内存任务存储初始化完成")
    
    async def save_task(self, task: Task) -> bool:
        """保存任务"""
        try:
            # 如果任务没有ID，生成一个
            if not task.task_id:
                task.task_id = f"task_{self.task_counter}"
                self.task_counter += 1
            
            # 更新时间戳
            task.updated_at = datetime.utcnow()
            
            # 保存任务
            self.tasks[task.task_id] = task
            
            # 初始化相关数据结构
            if task.task_id not in self.task_logs:
                self.task_logs[task.task_id] = []
            if task.task_id not in self.task_dependencies:
                self.task_dependencies[task.task_id] = []
            
            logger.debug(f"任务保存成功: {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"任务保存失败: {str(e)}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        try:
            return self.tasks.get(task_id)
        except Exception as e:
            logger.error(f"获取任务失败: {str(e)}")
            return None
    
    async def update_task(self, task: Task) -> bool:
        """更新任务"""
        try:
            if task.task_id not in self.tasks:
                return False
            
            # 更新时间戳
            task.updated_at = datetime.utcnow()
            
            # 更新任务
            self.tasks[task.task_id] = task
            
            logger.debug(f"任务更新成功: {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"任务更新失败: {str(e)}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            if task_id not in self.tasks:
                return False
            
            # 删除任务及相关数据
            del self.tasks[task_id]
            if task_id in self.task_results:
                del self.task_results[task_id]
            if task_id in self.task_logs:
                del self.task_logs[task_id]
            if task_id in self.task_dependencies:
                del self.task_dependencies[task_id]
            
            logger.debug(f"任务删除成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"任务删除失败: {str(e)}")
            return False
    
    async def list_tasks(self, 
                        status: Optional[str] = None,
                        task_type: Optional[str] = None,
                        priority: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Task]:
        """列出任务"""
        try:
            tasks = list(self.tasks.values())
            
            # 应用过滤条件
            if status:
                tasks = [t for t in tasks if t.status == status]
            if task_type:
                tasks = [t for t in tasks if t.type == task_type]
            if priority:
                tasks = [t for t in tasks if t.priority == priority]
            
            # 按创建时间排序
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            
            # 应用分页
            return tasks[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"列出任务失败: {str(e)}")
            return []
    
    async def save_task_result(self, result: TaskResult) -> bool:
        """保存任务执行结果"""
        try:
            self.task_results[result.task_id] = result
            logger.debug(f"任务结果保存成功: {result.task_id}")
            return True
        except Exception as e:
            logger.error(f"任务结果保存失败: {str(e)}")
            return False
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务执行结果"""
        try:
            return self.task_results.get(task_id)
        except Exception as e:
            logger.error(f"获取任务结果失败: {str(e)}")
            return None
    
    async def save_task_log(self, log: TaskExecutionLog) -> bool:
        """保存任务执行日志"""
        try:
            if log.task_id not in self.task_logs:
                self.task_logs[log.task_id] = []
            
            self.task_logs[log.task_id].append(log)
            
            # 限制日志数量
            if len(self.task_logs[log.task_id]) > 1000:
                self.task_logs[log.task_id] = self.task_logs[log.task_id][-1000:]
            
            logger.debug(f"任务日志保存成功: {log.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"任务日志保存失败: {str(e)}")
            return False
    
    async def get_task_logs(self, task_id: str, 
                           level: Optional[str] = None,
                           limit: int = 100) -> List[TaskExecutionLog]:
        """获取任务执行日志"""
        try:
            logs = self.task_logs.get(task_id, [])
            
            # 应用级别过滤
            if level:
                logs = [log for log in logs if log.level == level]
            
            # 按时间排序
            logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 应用数量限制
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"获取任务日志失败: {str(e)}")
            return []
    
    async def save_task_dependency(self, dependency: TaskDependency) -> bool:
        """保存任务依赖关系"""
        try:
            if dependency.task_id not in self.task_dependencies:
                self.task_dependencies[dependency.task_id] = []
            
            # 检查是否已存在
            existing = [d for d in self.task_dependencies[dependency.task_id] 
                       if d.dependency_id == dependency.dependency_id]
            
            if not existing:
                self.task_dependencies[dependency.task_id].append(dependency)
            
            logger.debug(f"任务依赖保存成功: {dependency.task_id} -> {dependency.dependency_id}")
            return True
            
        except Exception as e:
            logger.error(f"任务依赖保存失败: {str(e)}")
            return False
    
    async def get_task_dependencies(self, task_id: str) -> List[TaskDependency]:
        """获取任务依赖关系"""
        try:
            return self.task_dependencies.get(task_id, [])
        except Exception as e:
            logger.error(f"获取任务依赖失败: {str(e)}")
            return []
    
    async def get_dependent_tasks(self, task_id: str) -> List[TaskDependency]:
        """获取依赖该任务的任务列表"""
        try:
            dependent_tasks = []
            for task_id_key, dependencies in self.task_dependencies.items():
                for dependency in dependencies:
                    if dependency.dependency_id == task_id:
                        dependent_tasks.append(dependency)
            return dependent_tasks
        except Exception as e:
            logger.error(f"获取依赖任务失败: {str(e)}")
            return []
    
    async def search_tasks(self, query: str, 
                          fields: Optional[List[str]] = None,
                          limit: int = 100) -> List[Task]:
        """搜索任务"""
        try:
            if not fields:
                fields = ["name", "description", "tags"]
            
            results = []
            query_lower = query.lower()
            
            for task in self.tasks.values():
                for field in fields:
                    if hasattr(task, field):
                        value = getattr(task, field)
                        if isinstance(value, str) and query_lower in value.lower():
                            results.append(task)
                            break
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and query_lower in item.lower():
                                    results.append(task)
                                    break
                            if task in results:
                                break
            
            # 按相关性排序（简单实现）
            results.sort(key=lambda x: len(x.name), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索任务失败: {str(e)}")
            return []
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            total_tasks = len(self.tasks)
            status_counts = {}
            type_counts = {}
            priority_counts = {}
            
            for task in self.tasks.values():
                # 状态统计
                status = str(task.status)
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # 类型统计
                task_type = str(task.type)
                type_counts[task_type] = type_counts.get(task_type, 0) + 1
                
                # 优先级统计
                priority = str(task.priority)
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # 计算完成率
            completed_tasks = status_counts.get("completed", 0)
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total_tasks": total_tasks,
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "priority_distribution": priority_counts,
                "completion_rate": round(completion_rate, 2),
                "total_results": len(self.task_results),
                "total_logs": sum(len(logs) for logs in self.task_logs.values()),
                "total_dependencies": sum(len(deps) for deps in self.task_dependencies.values())
            }
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {str(e)}")
            return {}
    
    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """清理旧任务"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleaned_count = 0
            
            task_ids_to_clean = []
            for task_id, task in self.tasks.items():
                if task.created_at < cutoff_date and task.status in ["completed", "failed", "cancelled"]:
                    task_ids_to_clean.append(task_id)
            
            for task_id in task_ids_to_clean:
                await self.delete_task(task_id)
                cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧任务")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {str(e)}")
            return 0
    
    async def backup_tasks(self, backup_path: str) -> bool:
        """备份任务数据"""
        try:
            backup_data = {
                "tasks": self.tasks,
                "task_results": self.task_results,
                "task_logs": self.task_logs,
                "task_dependencies": self.task_dependencies,
                "task_counter": self.task_counter,
                "backup_time": datetime.utcnow().isoformat()
            }
            
            # 使用pickle序列化
            with open(backup_path, 'wb') as f:
                pickle.dump(backup_data, f)
            
            logger.info(f"任务数据备份成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"任务数据备份失败: {str(e)}")
            return False
    
    async def restore_tasks(self, backup_path: str) -> bool:
        """恢复任务数据"""
        try:
            with open(backup_path, 'rb') as f:
                backup_data = pickle.load(f)
            
            # 恢复数据
            self.tasks = backup_data.get("tasks", {})
            self.task_results = backup_data.get("task_results", {})
            self.task_logs = backup_data.get("task_logs", {})
            self.task_dependencies = backup_data.get("task_dependencies", {})
            self.task_counter = backup_data.get("task_counter", 0)
            
            logger.info(f"任务数据恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"任务数据恢复失败: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查基本数据结构
            if not isinstance(self.tasks, dict):
                return False
            if not isinstance(self.task_results, dict):
                return False
            if not isinstance(self.task_logs, dict):
                return False
            if not isinstance(self.task_dependencies, dict):
                return False
            
            # 检查计数器
            if not isinstance(self.task_counter, int) or self.task_counter < 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭存储连接"""
        try:
            # 清理内存数据
            self.tasks.clear()
            self.task_results.clear()
            self.task_logs.clear()
            self.task_dependencies.clear()
            self.task_counter = 0
            
            logger.info("内存任务存储已关闭")
            
        except Exception as e:
            logger.error(f"关闭存储失败: {str(e)}")
    
    def get_memory_usage(self) -> Dict[str, int]:
        """获取内存使用情况"""
        try:
            return {
                "tasks_count": len(self.tasks),
                "results_count": len(self.task_results),
                "logs_count": sum(len(logs) for logs in self.task_logs.values()),
                "dependencies_count": sum(len(deps) for deps in self.task_dependencies.values())
            }
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {str(e)}")
            return {}