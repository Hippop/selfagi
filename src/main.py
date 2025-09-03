"""
主程序入口
初始化并启动整个系统
"""
import asyncio
import signal
import sys
from pathlib import Path
from loguru import logger

from src.managers.task_manager import TaskManager
from src.managers.system_coordinator import SystemCoordinator
from src.storage.memory_storage import MemoryTaskStorage
from src.executors.llm_executor import LLMExecutor
from src.executors.shell_executor import ShellExecutor
from src.utils.task_analyzer import TaskAnalyzer
from config.settings import settings


class SelfAGISystem:
    """自主任务执行系统"""
    
    def __init__(self):
        self.storage = None
        self.task_analyzer = None
        self.task_manager = None
        self.system_coordinator = None
        self.executors = []
        self.is_running = False
        
        # 设置日志
        self._setup_logging()
        
        logger.info("SelfAGI系统初始化开始")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志
        logger.remove()  # 移除默认处理器
        
        # 控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL
        )
        
        # 文件输出
        logger.add(
            settings.LOG_FILE,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.LOG_LEVEL,
            rotation="1 day",
            retention="30 days"
        )
        
        logger.info("日志系统初始化完成")
    
    async def initialize(self):
        """初始化系统"""
        try:
            logger.info("开始初始化系统组件...")
            
            # 初始化存储
            self.storage = MemoryTaskStorage()
            logger.info("存储系统初始化完成")
            
            # 初始化任务分析器
            self.task_analyzer = TaskAnalyzer()
            logger.info("任务分析器初始化完成")
            
            # 初始化任务管理器
            self.task_manager = TaskManager(self.storage, self.task_analyzer)
            logger.info("任务管理器初始化完成")
            
            # 初始化执行器
            await self._initialize_executors()
            logger.info("执行器初始化完成")
            
            # 初始化系统协调器
            self.system_coordinator = SystemCoordinator(self.task_manager, self.storage)
            logger.info("系统协调器初始化完成")
            
            # 注册执行器到协调器
            for executor in self.executors:
                await self.system_coordinator.register_executor(executor)
            
            logger.info("系统初始化完成")
            
        except Exception as e:
            logger.error(f"系统初始化失败: {str(e)}")
            raise
    
    async def _initialize_executors(self):
        """初始化执行器"""
        try:
            # 初始化LLM执行器
            llm_executor = LLMExecutor()
            self.executors.append(llm_executor)
            logger.info("LLM执行器初始化完成")
            
            # 初始化Shell执行器
            shell_executor = ShellExecutor()
            self.executors.append(shell_executor)
            logger.info("Shell执行器初始化完成")
            
            # 这里可以添加更多执行器
            # 如网络执行器、文件执行器等
            
        except Exception as e:
            logger.error(f"执行器初始化失败: {str(e)}")
            raise
    
    async def start(self):
        """启动系统"""
        try:
            if self.is_running:
                logger.warning("系统已在运行")
                return
            
            logger.info("启动系统...")
            
            # 启动系统协调器
            await self.system_coordinator.start()
            
            self.is_running = True
            logger.info("系统启动成功")
            
            # 运行主循环
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"系统启动失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止系统"""
        try:
            if not self.is_running:
                logger.warning("系统未在运行")
                return
            
            logger.info("停止系统...")
            
            # 停止系统协调器
            await self.system_coordinator.stop()
            
            self.is_running = False
            logger.info("系统已停止")
            
        except Exception as e:
            logger.error(f"系统停止失败: {str(e)}")
            raise
    
    async def _main_loop(self):
        """主循环"""
        try:
            while self.is_running:
                # 检查系统状态
                status = await self.system_coordinator.get_system_status()
                
                # 如果系统状态异常，尝试恢复
                if status.get("system_status") == "error":
                    logger.warning("检测到系统异常，尝试恢复...")
                    await self._recover_system()
                
                # 等待一段时间
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            logger.info("主循环被取消")
        except Exception as e:
            logger.error(f"主循环错误: {str(e)}")
            raise
    
    async def _recover_system(self):
        """恢复系统"""
        try:
            logger.info("开始系统恢复...")
            
            # 重新初始化系统
            await self.initialize()
            
            # 重新启动系统
            await self.start()
            
            logger.info("系统恢复完成")
            
        except Exception as e:
            logger.error(f"系统恢复失败: {str(e)}")
            # 如果恢复失败，执行紧急关闭
            await self._emergency_shutdown()
    
    async def _emergency_shutdown(self):
        """紧急关闭"""
        try:
            logger.error("执行紧急关闭")
            
            if self.system_coordinator:
                await self.system_coordinator.emergency_shutdown()
            
            self.is_running = False
            
            logger.info("紧急关闭完成")
            
        except Exception as e:
            logger.error(f"紧急关闭失败: {str(e)}")
    
    async def create_sample_task(self):
        """创建示例任务"""
        try:
            # 创建一个LLM推理任务
            llm_task_data = {
                "name": "示例LLM推理任务",
                "description": "使用GPT-4进行文本分析",
                "type": "computation",
                "priority": "normal",
                "actions": [
                    {
                        "name": "文本分析",
                        "type": "llm_inference",
                        "parameters": {
                            "prompt": "请分析以下文本的情感倾向：'今天天气很好，心情愉快。'",
                            "model": "gpt-4",
                            "max_tokens": 200,
                            "temperature": 0.7
                        }
                    }
                ],
                "tags": ["示例", "LLM", "文本分析"],
                "category": "demo"
            }
            
            # 创建任务
            task = await self.task_manager.create_task(llm_task_data)
            logger.info(f"示例任务创建成功: {task.task_id}")
            
            # 调度任务
            scheduled = await self.task_manager.schedule_task(task)
            if scheduled:
                logger.info("示例任务已调度")
            else:
                logger.warning("示例任务调度失败")
            
            return task
            
        except Exception as e:
            logger.error(f"创建示例任务失败: {str(e)}")
            return None
    
    async def get_system_info(self):
        """获取系统信息"""
        try:
            if not self.system_coordinator:
                return {"error": "系统未初始化"}
            
            # 获取系统状态
            status = await self.system_coordinator.get_system_status()
            
            # 获取性能指标
            metrics = await self.system_coordinator.get_performance_metrics()
            
            # 获取任务统计
            task_stats = await self.storage.get_task_statistics()
            
            return {
                "system_status": status,
                "performance_metrics": metrics,
                "task_statistics": task_stats,
                "version": settings.VERSION,
                "project_name": settings.PROJECT_NAME
            }
            
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}")
            return {"error": str(e)}


async def main():
    """主函数"""
    system = SelfAGISystem()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，开始关闭系统...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化系统
        await system.initialize()
        
        # 启动系统
        await system.start()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"系统运行错误: {str(e)}")
    finally:
        # 确保系统正确关闭
        if system.is_running:
            await system.stop()
        
        logger.info("系统已完全关闭")


if __name__ == "__main__":
    try:
        # 运行主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
        sys.exit(1)