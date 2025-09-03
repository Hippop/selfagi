#!/usr/bin/env python3
"""
SelfAGI系统演示脚本
展示系统的主要功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import SelfAGISystem
from src.core.models import TaskType, TaskPriority
from loguru import logger


async def demo_basic_functionality():
    """演示基本功能"""
    print("=" * 60)
    print("SelfAGI 系统演示 - 基本功能")
    print("=" * 60)
    
    # 初始化系统
    system = SelfAGISystem()
    await system.initialize()
    
    print("✓ 系统初始化完成")
    
    # 启动系统
    await system.start()
    print("✓ 系统启动完成")
    
    # 创建示例任务
    print("\n创建示例任务...")
    task = await system.create_sample_task()
    if task:
        print(f"✓ 示例任务创建成功: {task.task_id}")
        print(f"  任务名称: {task.name}")
        print(f"  任务状态: {task.status}")
    else:
        print("✗ 示例任务创建失败")
    
    # 获取系统信息
    print("\n获取系统信息...")
    info = await system.get_system_info()
    if "error" not in info:
        print("✓ 系统信息获取成功")
        print(f"  项目名称: {info.get('project_name')}")
        print(f"  版本: {info.get('version')}")
    else:
        print(f"✗ 系统信息获取失败: {info.get('error')}")
    
    # 获取系统状态
    print("\n获取系统状态...")
    if system.system_coordinator:
        status = await system.system_coordinator.get_system_status()
        print("✓ 系统状态获取成功")
        print(f"  系统状态: {status.get('system_status')}")
        print(f"  运行时间: {status.get('uptime_seconds', 0):.2f} 秒")
    else:
        print("✗ 系统协调器未初始化")
    
    # 获取性能指标
    print("\n获取性能指标...")
    if system.system_coordinator:
        metrics = await system.system_coordinator.get_performance_metrics()
        print("✓ 性能指标获取成功")
        print(f"  总任务数: {metrics.get('total_tasks_processed', 0)}")
        print(f"  成功率: {metrics.get('success_rate', 0):.2f}%")
        print(f"  平均执行时间: {metrics.get('average_execution_time', 0):.3f} 秒")
    else:
        print("✗ 系统协调器未初始化")
    
    # 获取任务统计
    print("\n获取任务统计...")
    if system.storage:
        stats = await system.storage.get_task_statistics()
        print("✓ 任务统计获取成功")
        print(f"  总任务数: {stats.get('total_tasks', 0)}")
        print(f"  完成率: {stats.get('completion_rate', 0):.2f}%")
        print(f"  状态分布: {stats.get('status_distribution', {})}")
    else:
        print("✗ 存储系统未初始化")
    
    # 等待一段时间让任务执行
    print("\n等待任务执行...")
    await asyncio.sleep(5)
    
    # 获取任务状态
    if task:
        print(f"\n检查任务 {task.task_id} 状态...")
        if system.task_manager:
            status = await system.task_manager.get_task_status(task.task_id)
            if status:
                print(f"✓ 任务状态: {status}")
            else:
                print("✗ 无法获取任务状态")
        else:
            print("✗ 任务管理器未初始化")
    
    # 停止系统
    print("\n停止系统...")
    await system.stop()
    print("✓ 系统已停止")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


async def demo_task_management():
    """演示任务管理功能"""
    print("\n" + "=" * 60)
    print("SelfAGI 系统演示 - 任务管理")
    print("=" * 60)
    
    # 初始化系统
    system = SelfAGISystem()
    await system.initialize()
    
    print("✓ 系统初始化完成")
    
    # 启动系统
    await system.start()
    print("✓ 系统启动完成")
    
    # 创建多个任务
    print("\n创建多个任务...")
    
    # 任务1: LLM推理任务
    llm_task_data = {
        "name": "LLM文本分析任务",
        "description": "使用GPT-4分析文本情感",
        "type": "computation",
        "priority": "high",
        "actions": [
            {
                "name": "情感分析",
                "type": "llm_inference",
                "parameters": {
                    "prompt": "分析以下文本的情感倾向：'今天天气很好，心情愉快。'",
                    "model": "gpt-4",
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            }
        ],
        "tags": ["LLM", "文本分析", "情感分析"],
        "category": "demo"
    }
    
    # 任务2: Shell命令任务
    shell_task_data = {
        "name": "系统信息收集任务",
        "description": "收集系统基本信息",
        "type": "io",
        "priority": "normal",
        "actions": [
            {
                "name": "系统检查",
                "type": "system_check",
                "parameters": {
                    "check_type": "general"
                }
            }
        ],
        "tags": ["系统", "信息收集", "监控"],
        "category": "demo"
    }
    
    # 创建任务
    tasks = []
    for i, task_data in enumerate([llm_task_data, shell_task_data], 1):
        print(f"\n创建任务 {i}...")
        task = await system.task_manager.create_task(task_data)
        if task:
            tasks.append(task)
            print(f"✓ 任务 {i} 创建成功: {task.task_id}")
            print(f"  名称: {task.name}")
            print(f"  类型: {task.type}")
            print(f"  优先级: {task.priority}")
        else:
            print(f"✗ 任务 {i} 创建失败")
    
    # 调度任务
    print("\n调度任务...")
    for i, task in enumerate(tasks, 1):
        scheduled = await system.task_manager.schedule_task(task)
        if scheduled:
            print(f"✓ 任务 {i} 调度成功")
        else:
            print(f"✗ 任务 {i} 调度失败")
    
    # 等待任务执行
    print("\n等待任务执行...")
    await asyncio.sleep(10)
    
    # 检查任务状态
    print("\n检查任务状态...")
    for i, task in enumerate(tasks, 1):
        if system.task_manager:
            status = await system.task_manager.get_task_status(task.task_id)
            if status:
                print(f"任务 {i}: {status}")
            else:
                print(f"任务 {i}: 状态未知")
        else:
            print(f"任务 {i}: 无法获取状态")
    
    # 获取任务列表
    print("\n获取任务列表...")
    if system.storage:
        all_tasks = await system.storage.list_tasks(limit=100)
        print(f"✓ 总任务数: {len(all_tasks)}")
        
        # 按状态分组
        status_groups = {}
        for task in all_tasks:
            status = str(task.status)
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(task)
        
        for status, task_list in status_groups.items():
            print(f"  {status}: {len(task_list)} 个")
    else:
        print("✗ 无法获取任务列表")
    
    # 搜索任务
    print("\n搜索任务...")
    if system.storage:
        search_results = await system.storage.search_tasks("LLM")
        print(f"✓ 搜索 'LLM' 找到 {len(search_results)} 个任务")
        
        for task in search_results:
            print(f"  - {task.name} ({task.task_id})")
    else:
        print("✗ 无法搜索任务")
    
    # 停止系统
    print("\n停止系统...")
    await system.stop()
    print("✓ 系统已停止")
    
    print("\n" + "=" * 60)
    print("任务管理演示完成！")
    print("=" * 60)


async def main():
    """主函数"""
    print("SelfAGI 自主任务执行系统演示")
    print("=" * 60)
    
    try:
        # 演示基本功能
        await demo_basic_functionality()
        
        # 演示任务管理
        await demo_task_management()
        
        print("\n所有演示完成！")
        print("\n要启动API服务，请运行: python run_api.py")
        print("要直接运行系统，请运行: python run.py")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        print(f"\n演示失败: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"演示异常退出: {str(e)}")
        sys.exit(1)