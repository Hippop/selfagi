"""
系统协调器
负责协调各个组件的工作
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from loguru import logger

from src.managers.task_manager import TaskManager
from src.storage.task_storage import TaskStorage
from src.executors.base import BaseExecutor
from src.core.models import Task, TaskStatus
from config.settings import settings
import os


class SystemCoordinator:
    """系统协调器"""
    
    def __init__(self, task_manager: TaskManager, storage: TaskStorage):
        self.task_manager = task_manager
        self.storage = storage
        self.executors: Dict[str, BaseExecutor] = {}
        self.system_status = "initializing"
        self.start_time = datetime.utcnow()
        self.health_check_interval = 30  # 秒
        self.cleanup_interval = 3600     # 秒
        self.backup_interval = 86400     # 秒
        
        # 监控指标
        self.metrics = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "system_uptime": 0,
            "last_health_check": None,
            "last_cleanup": None,
            "last_backup": None
        }
        
        # 运行状态
        self.is_running = False
        self.background_tasks: Set[asyncio.Task] = set()
        
        logger.info("系统协调器初始化完成")
    
    async def start(self):
        """启动系统协调器"""
        try:
            if self.is_running:
                logger.warning("系统协调器已在运行")
                return
            
            self.is_running = True
            self.system_status = "running"
            
            # 启动后台任务
            await self._start_background_tasks()
            
            # 启动任务管理器
            await self.task_manager.start_scheduler()
            
            logger.info("系统协调器启动成功")
            
        except Exception as e:
            logger.error(f"系统协调器启动失败: {str(e)}")
            self.system_status = "error"
            raise
    
    async def stop(self):
        """停止系统协调器"""
        try:
            if not self.is_running:
                logger.warning("系统协调器未在运行")
                return
            
            self.is_running = False
            self.system_status = "stopping"
            
            # 停止所有后台任务
            await self._stop_background_tasks()
            
            # 等待任务完成
            await self._wait_for_tasks_completion()
            
            self.system_status = "stopped"
            logger.info("系统协调器已停止")
            
        except Exception as e:
            logger.error(f"系统协调器停止失败: {str(e)}")
            self.system_status = "error"
            raise
    
    async def register_executor(self, executor: BaseExecutor):
        """注册执行器"""
        try:
            executor_key = f"{executor.executor_type}_{executor.name}"
            self.executors[executor_key] = executor
            
            # 注册到任务管理器
            self.task_manager.register_executor(executor.executor_type, executor)
            
            logger.info(f"执行器注册成功: {executor_key}")
            
        except Exception as e:
            logger.error(f"执行器注册失败: {str(e)}")
            raise
    
    async def unregister_executor(self, executor_key: str):
        """注销执行器"""
        try:
            if executor_key in self.executors:
                executor = self.executors[executor_key]
                await executor.shutdown()
                del self.executors[executor_key]
                
                logger.info(f"执行器注销成功: {executor_key}")
            else:
                logger.warning(f"执行器不存在: {executor_key}")
                
        except Exception as e:
            logger.error(f"执行器注销失败: {str(e)}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 更新运行时间
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            self.metrics["system_uptime"] = uptime
            
            # 获取执行器状态
            executor_statuses = {}
            for key, executor in self.executors.items():
                executor_statuses[key] = executor.get_status()
            
            # 获取任务统计
            task_stats = await self.storage.get_task_statistics()
            
            # 获取系统资源使用情况
            resource_usage = await self._get_resource_usage()
            
            return {
                "system_status": self.system_status,
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": uptime,
                "executors": executor_statuses,
                "task_statistics": task_stats,
                "resource_usage": resource_usage,
                "metrics": self.metrics,
                "background_tasks_count": len(self.background_tasks)
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                "system_status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """系统健康检查"""
        try:
            # 检查存储系统
            storage_healthy = await self.storage.health_check()
            if not storage_healthy:
                logger.error("存储系统健康检查失败")
                return False
            
            # 检查执行器
            executor_healthy = await self._check_executors_health()
            if not executor_healthy:
                logger.error("执行器健康检查失败")
                return False
            
            # 检查任务管理器
            task_manager_healthy = await self._check_task_manager_health()
            if not task_manager_healthy:
                logger.error("任务管理器健康检查失败")
                return False
            
            # 更新健康检查时间
            self.metrics["last_health_check"] = datetime.utcnow()
            
            logger.debug("系统健康检查通过")
            return True
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {str(e)}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # 计算平均执行时间
            if self.metrics["total_tasks_processed"] > 0:
                avg_time = self.metrics["average_execution_time"] / self.metrics["total_tasks_processed"]
            else:
                avg_time = 0.0
            
            # 计算成功率
            success_rate = 0.0
            if self.metrics["total_tasks_processed"] > 0:
                success_rate = (self.metrics["successful_tasks"] / self.metrics["total_tasks_processed"]) * 100
            
            return {
                "total_tasks_processed": self.metrics["total_tasks_processed"],
                "successful_tasks": self.metrics["successful_tasks"],
                "failed_tasks": self.metrics["failed_tasks"],
                "success_rate": round(success_rate, 2),
                "average_execution_time": round(avg_time, 3),
                "system_uptime_hours": round(self.metrics["system_uptime"] / 3600, 2),
                "executors_count": len(self.executors),
                "active_background_tasks": len(self.background_tasks)
            }
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {str(e)}")
            return {}
    
    async def update_metrics(self, task_result: Dict[str, Any]):
        """更新性能指标"""
        try:
            self.metrics["total_tasks_processed"] += 1
            
            if task_result.get("status") == "success":
                self.metrics["successful_tasks"] += 1
            else:
                self.metrics["failed_tasks"] += 1
            
            # 更新平均执行时间
            execution_time = task_result.get("execution_time", 0.0)
            if execution_time > 0:
                current_avg = self.metrics["average_execution_time"]
                total_tasks = self.metrics["total_tasks_processed"]
                self.metrics["average_execution_time"] = (current_avg * (total_tasks - 1) + execution_time) / total_tasks
            
        except Exception as e:
            logger.error(f"更新性能指标失败: {str(e)}")
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        try:
            # 健康检查任务
            health_check_task = asyncio.create_task(self._health_check_loop())
            self.background_tasks.add(health_check_task)
            
            # 清理任务
            cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.background_tasks.add(cleanup_task)
            
            # 备份任务
            backup_task = asyncio.create_task(self._backup_loop())
            self.background_tasks.add(backup_task)
            
            # 监控任务
            monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.background_tasks.add(monitoring_task)
            
            logger.info("后台任务启动完成")
            
        except Exception as e:
            logger.error(f"启动后台任务失败: {str(e)}")
            raise
    
    async def _stop_background_tasks(self):
        """停止后台任务"""
        try:
            # 取消所有后台任务
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            logger.info("后台任务已取消")
            
        except Exception as e:
            logger.error(f"停止后台任务失败: {str(e)}")
    
    async def _wait_for_tasks_completion(self):
        """等待任务完成"""
        try:
            # 等待所有后台任务完成
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # 清空任务集合
            self.background_tasks.clear()
            
            logger.info("所有后台任务已完成")
            
        except Exception as e:
            logger.error(f"等待任务完成失败: {str(e)}")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        try:
            while self.is_running:
                await asyncio.sleep(self.health_check_interval)
                
                if self.is_running:
                    healthy = await self.health_check()
                    if not healthy:
                        logger.warning("系统健康检查失败，可能需要干预")
                        
        except asyncio.CancelledError:
            logger.debug("健康检查循环已取消")
        except Exception as e:
            logger.error(f"健康检查循环错误: {str(e)}")
    
    async def _cleanup_loop(self):
        """清理循环"""
        try:
            while self.is_running:
                await asyncio.sleep(self.cleanup_interval)
                
                if self.is_running:
                    await self._perform_cleanup()
                    
        except asyncio.CancelledError:
            logger.debug("清理循环已取消")
        except Exception as e:
            logger.error(f"清理循环错误: {str(e)}")
    
    async def _backup_loop(self):
        """备份循环"""
        try:
            while self.is_running:
                await asyncio.sleep(self.backup_interval)
                
                if self.is_running:
                    await self._perform_backup()
                    
        except asyncio.CancelledError:
            logger.debug("备份循环已取消")
        except Exception as e:
            logger.error(f"备份循环错误: {str(e)}")
    
    async def _monitoring_loop(self):
        """监控循环"""
        try:
            while self.is_running:
                await asyncio.sleep(60)  # 每分钟监控一次
                
                if self.is_running:
                    await self._update_monitoring_data()
                    
        except asyncio.CancelledError:
            logger.debug("监控循环已取消")
        except Exception as e:
            logger.error(f"监控循环错误: {str(e)}")
    
    async def _perform_cleanup(self):
        """执行清理操作"""
        try:
            # 清理旧任务
            cleaned_count = await self.storage.cleanup_old_tasks(days=30)
            
            # 更新清理时间
            self.metrics["last_cleanup"] = datetime.utcnow()
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个旧任务")
                
        except Exception as e:
            logger.error(f"执行清理操作失败: {str(e)}")
    
    async def _perform_backup(self):
        """执行备份操作"""
        try:
            # 创建备份路径
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{backup_dir}/backup_{timestamp}.pkl"
            
            # 执行备份
            success = await self.storage.backup_tasks(backup_path)
            
            if success:
                self.metrics["last_backup"] = datetime.utcnow()
                logger.info(f"系统备份成功: {backup_path}")
            else:
                logger.error("系统备份失败")
                
        except Exception as e:
            logger.error(f"执行备份操作失败: {str(e)}")
    
    async def _update_monitoring_data(self):
        """更新监控数据"""
        try:
            # 更新系统运行时间
            self.metrics["system_uptime"] = (datetime.utcnow() - self.start_time).total_seconds()
            
            # 检查执行器状态
            for executor_key, executor in self.executors.items():
                if not await executor.health_check():
                    logger.warning(f"执行器健康检查失败: {executor_key}")
                    
        except Exception as e:
            logger.error(f"更新监控数据失败: {str(e)}")
    
    async def _check_executors_health(self) -> bool:
        """检查执行器健康状态"""
        try:
            for executor_key, executor in self.executors.items():
                if not await executor.health_check():
                    logger.warning(f"执行器不健康: {executor_key}")
                    return False
            return True
        except Exception as e:
            logger.error(f"检查执行器健康状态失败: {str(e)}")
            return False
    
    async def _check_task_manager_health(self) -> bool:
        """检查任务管理器健康状态"""
        try:
            # 检查任务管理器是否正在运行
            # 这里可以添加更多的健康检查逻辑
            return True
        except Exception as e:
            logger.error(f"检查任务管理器健康状态失败: {str(e)}")
            return False
    
    async def _get_resource_usage(self) -> Dict[str, Any]:
        """获取系统资源使用情况"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
            
        except ImportError:
            logger.warning("psutil未安装，无法获取系统资源信息")
            return {"error": "psutil not available"}
        except Exception as e:
            logger.error(f"获取系统资源使用情况失败: {str(e)}")
            return {"error": str(e)}
    
    async def emergency_shutdown(self):
        """紧急关闭"""
        try:
            logger.warning("执行紧急关闭")
            
            # 立即停止所有任务
            self.is_running = False
            self.system_status = "emergency_shutdown"
            
            # 取消所有后台任务
            await self._stop_background_tasks()
            
            # 关闭所有执行器
            for executor_key, executor in self.executors.items():
                try:
                    await executor.shutdown()
                except Exception as e:
                    logger.error(f"关闭执行器失败: {executor_key}, {str(e)}")
            
            # 保存当前状态
            await self._save_emergency_state()
            
            logger.info("紧急关闭完成")
            
        except Exception as e:
            logger.error(f"紧急关闭失败: {str(e)}")
    
    async def _save_emergency_state(self):
        """保存紧急状态"""
        try:
            # 保存当前系统状态到文件
            emergency_state = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_status": self.system_status,
                "metrics": self.metrics,
                "executors_count": len(self.executors)
            }
            
            import json
            with open("emergency_state.json", "w") as f:
                json.dump(emergency_state, f, indent=2)
                
            logger.info("紧急状态已保存")
            
        except Exception as e:
            logger.error(f"保存紧急状态失败: {str(e)}")