"""
基本功能测试
"""
import pytest
import asyncio
from src.core.models import Task, TaskStatus, TaskPriority, TaskType
from src.storage.memory_storage import MemoryTaskStorage
from src.utils.task_analyzer import TaskAnalyzer


@pytest.fixture
def storage():
    """创建存储实例"""
    return MemoryTaskStorage()


@pytest.fixture
def analyzer():
    """创建分析器实例"""
    return TaskAnalyzer()


@pytest.fixture
def sample_task():
    """创建示例任务"""
    return Task(
        name="测试任务",
        description="这是一个测试任务",
        type=TaskType.COMPUTATION,
        priority=TaskPriority.NORMAL,
        actions=[],
        tags=["测试"],
        category="test"
    )


@pytest.mark.asyncio
async def test_storage_save_and_get(storage, sample_task):
    """测试存储的保存和获取功能"""
    # 保存任务
    success = await storage.save_task(sample_task)
    assert success is True
    
    # 获取任务
    retrieved_task = await storage.get_task(sample_task.task_id)
    assert retrieved_task is not None
    assert retrieved_task.name == sample_task.name
    assert retrieved_task.description == sample_task.description


@pytest.mark.asyncio
async def test_storage_update(storage, sample_task):
    """测试存储的更新功能"""
    # 保存任务
    await storage.save_task(sample_task)
    
    # 更新任务
    sample_task.name = "更新后的任务"
    success = await storage.update_task(sample_task)
    assert success is True
    
    # 验证更新
    updated_task = await storage.get_task(sample_task.task_id)
    assert updated_task.name == "更新后的任务"


@pytest.mark.asyncio
async def test_storage_delete(storage, sample_task):
    """测试存储的删除功能"""
    # 保存任务
    await storage.save_task(sample_task)
    
    # 删除任务
    success = await storage.delete_task(sample_task.task_id)
    assert success is True
    
    # 验证删除
    deleted_task = await storage.get_task(sample_task.task_id)
    assert deleted_task is None


@pytest.mark.asyncio
async def test_storage_list_tasks(storage, sample_task):
    """测试存储的列表功能"""
    # 保存任务
    await storage.save_task(sample_task)
    
    # 列出任务
    tasks = await storage.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].task_id == sample_task.task_id


@pytest.mark.asyncio
async def test_analyzer_analyze_dependencies(analyzer, sample_task):
    """测试分析器的依赖分析功能"""
    dependencies = await analyzer.analyze_dependencies(sample_task)
    assert isinstance(dependencies, list)


@pytest.mark.asyncio
async def test_analyzer_decompose_task(analyzer, sample_task):
    """测试分析器的任务分解功能"""
    sub_tasks = await analyzer.decompose_task(sample_task)
    assert isinstance(sub_tasks, list)


@pytest.mark.asyncio
async def test_analyzer_analyze_patterns(analyzer, sample_task):
    """测试分析器的模式分析功能"""
    patterns = await analyzer.analyze_task_patterns(sample_task)
    assert isinstance(patterns, dict)


@pytest.mark.asyncio
async def test_analyzer_suggest_optimizations(analyzer, sample_task):
    """测试分析器的优化建议功能"""
    suggestions = await analyzer.suggest_optimizations(sample_task)
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_storage_statistics(storage, sample_task):
    """测试存储的统计功能"""
    # 保存任务
    await storage.save_task(sample_task)
    
    # 获取统计
    stats = await storage.get_task_statistics()
    assert isinstance(stats, dict)
    assert "total_tasks" in stats
    assert stats["total_tasks"] == 1


@pytest.mark.asyncio
async def test_storage_search(storage, sample_task):
    """测试存储的搜索功能"""
    # 保存任务
    await storage.save_task(sample_task)
    
    # 搜索任务
    results = await storage.search_tasks("测试")
    assert len(results) == 1
    assert results[0].task_id == sample_task.task_id


@pytest.mark.asyncio
async def test_storage_health_check(storage):
    """测试存储的健康检查功能"""
    healthy = await storage.health_check()
    assert healthy is True


if __name__ == "__main__":
    pytest.main([__file__])