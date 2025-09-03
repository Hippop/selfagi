"""
Shell执行器
用于系统命令执行、文件操作、环境配置等任务
"""
import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from src.executors.base import BaseExecutor
from src.core.models import Task, TaskType


class ShellExecutor(BaseExecutor):
    """Shell执行器"""
    
    def __init__(self):
        super().__init__("Shell执行器", "shell")
        self.safe_commands = {
            "file_operations": ["ls", "cat", "head", "tail", "grep", "find", "wc"],
            "system_info": ["uname", "whoami", "pwd", "date", "uptime"],
            "network": ["ping", "curl", "wget", "netstat", "ss"],
            "process": ["ps", "top", "htop", "kill", "nice", "renice"]
        }
        self.dangerous_commands = ["rm", "rmdir", "chmod", "chown", "sudo", "su"]
        self.working_directory = os.getcwd()
        self.environment_vars = os.environ.copy()
    
    async def validate_task(self, task: Task) -> bool:
        """验证任务是否可以执行"""
        # 检查任务类型
        if task.type not in [TaskType.IO, TaskType.STORAGE, TaskType.MIXED]:
            return False
        
        # 检查是否有执行动作
        if not task.actions:
            return False
        
        # 检查命令安全性
        for action in task.actions:
            if not await self._is_command_safe(action):
                return False
        
        return True
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行Shell任务"""
        try:
            # 更新负载
            self.update_load(5)
            
            # 执行前准备
            await self.pre_execute(task)
            
            results = []
            
            # 执行每个动作
            for action in task.actions:
                action_result = await self._execute_action(action, task)
                results.append(action_result)
            
            # 后处理
            final_result = await self.post_execute(task, {"actions": results})
            
            # 更新负载
            self.update_load(-5)
            
            return {
                "status": "success",
                "results": results,
                "final_result": final_result,
                "executor": self.name
            }
            
        except Exception as e:
            # 更新负载
            self.update_load(-5)
            
            # 处理错误
            error_result = await self.handle_error(task, e)
            logger.error(f"Shell任务执行失败: {str(e)}")
            return error_result
    
    async def _execute_action(self, action: Any, task: Task) -> Dict[str, Any]:
        """执行单个动作"""
        try:
            action_type = action.type
            parameters = action.parameters
            
            if action_type == "shell_command":
                return await self._execute_shell_command(parameters, task)
            elif action_type == "file_operation":
                return await self._execute_file_operation(parameters, task)
            elif action_type == "environment_setup":
                return await self._setup_environment(parameters, task)
            elif action_type == "system_check":
                return await self._system_check(parameters, task)
            else:
                raise ValueError(f"不支持的Shell动作类型: {action_type}")
                
        except Exception as e:
            logger.error(f"Shell动作执行失败: {str(e)}")
            return {
                "status": "error",
                "action_type": action.type,
                "error": str(e)
            }
    
    async def _execute_shell_command(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """执行Shell命令"""
        try:
            command = parameters.get("command", "")
            args = parameters.get("args", [])
            timeout = parameters.get("timeout", 30)
            working_dir = parameters.get("working_dir", self.working_directory)
            
            # 构建完整命令
            full_command = [command] + args
            
            # 检查命令安全性
            if not await self._is_command_safe({"command": command, "args": args}):
                raise Exception(f"命令不安全: {command}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=self.environment_vars
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"命令执行超时: {command}")
            
            return {
                "status": "success",
                "action_type": "shell_command",
                "command": full_command,
                "return_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "working_dir": working_dir
            }
            
        except Exception as e:
            logger.error(f"Shell命令执行失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "shell_command",
                "error": str(e),
                "command": parameters.get("command", "")
            }
    
    async def _execute_file_operation(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """执行文件操作"""
        try:
            operation = parameters.get("operation", "")
            source = parameters.get("source", "")
            destination = parameters.get("destination", "")
            
            if operation == "copy":
                result = await self._copy_file(source, destination)
            elif operation == "move":
                result = await self._move_file(source, destination)
            elif operation == "delete":
                result = await self._delete_file(source)
            elif operation == "create":
                result = await self._create_file(source, parameters.get("content", ""))
            elif operation == "read":
                result = await self._read_file(source)
            else:
                raise ValueError(f"不支持的文件操作: {operation}")
            
            return {
                "status": "success",
                "action_type": "file_operation",
                "operation": operation,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"文件操作失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "file_operation",
                "error": str(e),
                "operation": parameters.get("operation", "")
            }
    
    async def _setup_environment(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """设置环境"""
        try:
            env_vars = parameters.get("environment_variables", {})
            working_dir = parameters.get("working_directory", "")
            
            # 设置环境变量
            for key, value in env_vars.items():
                self.environment_vars[key] = str(value)
            
            # 设置工作目录
            if working_dir and os.path.exists(working_dir):
                self.working_directory = working_dir
            
            return {
                "status": "success",
                "action_type": "environment_setup",
                "environment_variables": env_vars,
                "working_directory": self.working_directory
            }
            
        except Exception as e:
            logger.error(f"环境设置失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "environment_setup",
                "error": str(e)
            }
    
    async def _system_check(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """系统检查"""
        try:
            check_type = parameters.get("check_type", "general")
            
            if check_type == "disk_space":
                result = await self._check_disk_space()
            elif check_type == "memory_usage":
                result = await self._check_memory_usage()
            elif check_type == "cpu_usage":
                result = await self._check_cpu_usage()
            elif check_type == "network_status":
                result = await self._check_network_status()
            else:
                result = await self._general_system_check()
            
            return {
                "status": "success",
                "action_type": "system_check",
                "check_type": check_type,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"系统检查失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "system_check",
                "error": str(e)
            }
    
    async def _copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """复制文件"""
        try:
            if os.path.isfile(source):
                shutil.copy2(source, destination)
                return {"message": f"文件复制成功: {source} -> {destination}"}
            elif os.path.isdir(source):
                shutil.copytree(source, destination)
                return {"message": f"目录复制成功: {source} -> {destination}"}
            else:
                raise Exception(f"源路径不存在: {source}")
        except Exception as e:
            raise Exception(f"复制失败: {str(e)}")
    
    async def _move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """移动文件"""
        try:
            shutil.move(source, destination)
            return {"message": f"文件移动成功: {source} -> {destination}"}
        except Exception as e:
            raise Exception(f"移动失败: {str(e)}")
    
    async def _delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            if os.path.isfile(path):
                os.remove(path)
                return {"message": f"文件删除成功: {path}"}
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return {"message": f"目录删除成功: {path}"}
            else:
                raise Exception(f"路径不存在: {path}")
        except Exception as e:
            raise Exception(f"删除失败: {str(e)}")
    
    async def _create_file(self, path: str, content: str) -> Dict[str, Any]:
        """创建文件"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"message": f"文件创建成功: {path}"}
        except Exception as e:
            raise Exception(f"创建文件失败: {str(e)}")
    
    async def _read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            if not os.path.exists(path):
                raise Exception(f"文件不存在: {path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "content": content,
                "size": len(content),
                "path": path
            }
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            stat = shutil.disk_usage(self.working_directory)
            return {
                "total": stat.total,
                "used": stat.used,
                "free": stat.free,
                "percentage_used": (stat.used / stat.total) * 100
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = int(value.strip().split()[0])
            
            total = mem_info.get('MemTotal', 0)
            available = mem_info.get('MemAvailable', 0)
            used = total - available
            
            return {
                "total": total,
                "used": used,
                "available": available,
                "percentage_used": (used / total) * 100 if total > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """检查CPU使用"""
        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().strip().split()
            
            return {
                "load_1min": float(load_avg[0]),
                "load_5min": float(load_avg[1]),
                "load_15min": float(load_avg[2])
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_network_status(self) -> Dict[str, Any]:
        """检查网络状态"""
        try:
            # 简单的网络检查
            result = await self._execute_shell_command({
                "command": "ping",
                "args": ["-c", "1", "8.8.8.8"],
                "timeout": 5
            }, None)
            
            return {
                "ping_result": result,
                "network_status": "connected" if result.get("return_code") == 0 else "disconnected"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _general_system_check(self) -> Dict[str, Any]:
        """通用系统检查"""
        try:
            disk = await self._check_disk_space()
            memory = await self._check_memory_usage()
            cpu = await self._check_cpu_usage()
            
            return {
                "disk": disk,
                "memory": memory,
                "cpu": cpu,
                "working_directory": self.working_directory,
                "environment_variables_count": len(self.environment_vars)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _is_command_safe(self, action: Dict[str, Any]) -> bool:
        """检查命令是否安全"""
        command = action.get("command", "")
        args = action.get("args", [])
        
        # 检查危险命令
        if command in self.dangerous_commands:
            return False
        
        # 检查命令参数
        full_command = f"{command} {' '.join(args)}"
        if any(dangerous in full_command for dangerous in self.dangerous_commands):
            return False
        
        # 检查路径遍历
        if ".." in full_command or "~" in full_command:
            return False
        
        return True
    
    def get_working_directory(self) -> str:
        """获取当前工作目录"""
        return self.working_directory
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境变量"""
        return self.environment_vars.copy()
    
    async def change_working_directory(self, new_dir: str) -> bool:
        """改变工作目录"""
        try:
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.working_directory = new_dir
                return True
            return False
        except Exception:
            return False