"""
任务分析器
用于分析任务依赖、分解复杂任务等
"""
import re
from typing import List, Dict, Any, Optional
from loguru import logger

from src.core.models import Task, TaskType, TaskPriority


class TaskAnalyzer:
    """任务分析器"""
    
    def __init__(self):
        self.complexity_thresholds = {
            "simple": 1,      # 简单任务
            "medium": 3,      # 中等任务
            "complex": 5,     # 复杂任务
            "very_complex": 10  # 非常复杂的任务
        }
        
        self.task_patterns = {
            "file_processing": r"(file|read|write|copy|move|delete|process)",
            "data_analysis": r"(analyze|process|transform|calculate|compute)",
            "network_request": r"(http|api|request|fetch|download|upload)",
            "system_operation": r"(system|command|shell|execute|run)",
            "ai_inference": r"(ai|llm|model|inference|generate|analyze)"
        }
    
    async def analyze_dependencies(self, task: Task) -> List[str]:
        """
        分析任务依赖关系
        
        Args:
            task: 要分析的任务
            
        Returns:
            依赖任务ID列表
        """
        try:
            dependencies = []
            
            # 分析任务描述中的依赖
            desc_deps = self._extract_dependencies_from_description(task.description)
            dependencies.extend(desc_deps)
            
            # 分析任务动作中的依赖
            for action in task.actions:
                action_deps = self._extract_dependencies_from_action(action)
                dependencies.extend(action_deps)
            
            # 分析环境配置中的依赖
            env_deps = self._extract_dependencies_from_environment(task.environment)
            dependencies.extend(env_deps)
            
            # 去重
            dependencies = list(set(dependencies))
            
            logger.info(f"任务 {task.task_id} 依赖分析完成，发现 {len(dependencies)} 个依赖")
            return dependencies
            
        except Exception as e:
            logger.error(f"依赖分析失败: {str(e)}")
            return []
    
    async def decompose_task(self, task: Task) -> List[Task]:
        """
        分解复杂任务为子任务
        
        Args:
            task: 要分解的任务
            
        Returns:
            子任务列表
        """
        try:
            # 评估任务复杂度
            complexity = await self._evaluate_complexity(task)
            
            # 如果任务不够复杂，不需要分解
            if complexity < self.complexity_thresholds["complex"]:
                logger.info(f"任务 {task.task_id} 复杂度较低，无需分解")
                return []
            
            # 根据任务类型选择分解策略
            if task.type == TaskType.COMPUTATION:
                sub_tasks = await self._decompose_computation_task(task)
            elif task.type == TaskType.IO:
                sub_tasks = await self._decompose_io_task(task)
            elif task.type == TaskType.NETWORK:
                sub_tasks = await self._decompose_network_task(task)
            elif task.type == TaskType.STORAGE:
                sub_tasks = await self._decompose_storage_task(task)
            else:
                sub_tasks = await self._decompose_mixed_task(task)
            
            logger.info(f"任务 {task.task_id} 分解完成，生成 {len(sub_tasks)} 个子任务")
            return sub_tasks
            
        except Exception as e:
            logger.error(f"任务分解失败: {str(e)}")
            return []
    
    async def analyze_task_patterns(self, task: Task) -> Dict[str, Any]:
        """
        分析任务模式
        
        Args:
            task: 要分析的任务
            
        Returns:
            模式分析结果
        """
        try:
            patterns = {}
            
            # 分析任务描述中的模式
            for pattern_name, pattern_regex in self.task_patterns.items():
                matches = re.findall(pattern_regex, task.description.lower())
                if matches:
                    patterns[pattern_name] = {
                        "matches": matches,
                        "count": len(matches)
                    }
            
            # 分析任务动作中的模式
            action_patterns = {}
            for action in task.actions:
                action_type = action.type
                if action_type not in action_patterns:
                    action_patterns[action_type] = 0
                action_patterns[action_type] += 1
            
            patterns["action_types"] = action_patterns
            
            # 分析任务优先级模式
            priority_analysis = self._analyze_priority_pattern(task)
            patterns["priority"] = priority_analysis
            
            return patterns
            
        except Exception as e:
            logger.error(f"任务模式分析失败: {str(e)}")
            return {}
    
    async def suggest_optimizations(self, task: Task) -> List[str]:
        """
        为任务提供优化建议
        
        Args:
            task: 要优化的任务
            
        Returns:
            优化建议列表
        """
        try:
            suggestions = []
            
            # 分析任务复杂度
            complexity = await self._evaluate_complexity(task)
            if complexity > self.complexity_thresholds["complex"]:
                suggestions.append("任务复杂度较高，建议分解为多个子任务")
            
            # 分析任务依赖
            dependencies = await self.analyze_dependencies(task)
            if len(dependencies) > 5:
                suggestions.append("任务依赖较多，建议优化依赖结构")
            
            # 分析任务优先级
            if task.priority == TaskPriority.URGENT:
                suggestions.append("高优先级任务，建议设置超时和重试策略")
            
            # 分析任务类型
            if task.type == TaskType.NETWORK:
                suggestions.append("网络任务，建议添加重试机制和超时设置")
            
            # 分析任务动作
            if len(task.actions) > 10:
                suggestions.append("任务动作过多，建议合并或优化")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"优化建议生成失败: {str(e)}")
            return []
    
    def _extract_dependencies_from_description(self, description: str) -> List[str]:
        """从任务描述中提取依赖"""
        dependencies = []
        
        # 查找可能的依赖引用
        # 这里可以使用更复杂的NLP技术来提取依赖关系
        # 目前使用简单的关键词匹配
        
        # 查找"依赖"、"需要"、"前提"等关键词
        dependency_keywords = ["依赖", "需要", "前提", "基于", "在...之后", "等待"]
        
        for keyword in dependency_keywords:
            if keyword in description:
                # 提取依赖信息
                # 这里需要更复杂的解析逻辑
                pass
        
        return dependencies
    
    def _extract_dependencies_from_action(self, action: Any) -> List[str]:
        """从任务动作中提取依赖"""
        dependencies = []
        
        # 分析动作参数中的依赖
        parameters = action.parameters if hasattr(action, 'parameters') else {}
        
        # 查找文件依赖
        if 'input_file' in parameters:
            dependencies.append(f"file:{parameters['input_file']}")
        
        # 查找API依赖
        if 'api_endpoint' in parameters:
            dependencies.append(f"api:{parameters['api_endpoint']}")
        
        # 查找服务依赖
        if 'service_name' in parameters:
            dependencies.append(f"service:{parameters['service_name']}")
        
        return dependencies
    
    def _extract_dependencies_from_environment(self, environment: Any) -> List[str]:
        """从环境配置中提取依赖"""
        dependencies = []
        
        if not environment:
            return dependencies
        
        # 分析环境变量依赖
        variables = environment.variables if hasattr(environment, 'variables') else {}
        for key, value in variables.items():
            if isinstance(value, str) and value.startswith("dep:"):
                dependencies.append(value[4:])  # 移除"dep:"前缀
        
        # 分析资源依赖
        resources = environment.resources if hasattr(environment, 'resources') else {}
        if 'required_services' in resources:
            for service in resources['required_services']:
                dependencies.append(f"service:{service}")
        
        return dependencies
    
    async def _evaluate_complexity(self, task: Task) -> int:
        """评估任务复杂度"""
        complexity_score = 0
        
        # 基于任务描述长度
        complexity_score += len(task.description) // 100
        
        # 基于动作数量
        complexity_score += len(task.actions) * 2
        
        # 基于依赖数量
        dependencies = await self.analyze_dependencies(task)
        complexity_score += len(dependencies)
        
        # 基于任务类型
        type_complexity = {
            TaskType.COMPUTATION: 3,
            TaskType.IO: 2,
            TaskType.NETWORK: 2,
            TaskType.STORAGE: 1,
            TaskType.MIXED: 4
        }
        complexity_score += type_complexity.get(task.type, 1)
        
        # 基于优先级
        priority_complexity = {
            TaskPriority.LOW: 0,
            TaskPriority.NORMAL: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.URGENT: 3
        }
        complexity_score += priority_complexity.get(task.priority, 1)
        
        return complexity_score
    
    async def _decompose_computation_task(self, task: Task) -> List[Task]:
        """分解计算任务"""
        sub_tasks = []
        
        # 根据动作类型分解
        for i, action in enumerate(task.actions):
            sub_task = Task(
                name=f"{task.name}_计算步骤_{i+1}",
                description=f"执行计算动作: {action.type}",
                type=TaskType.COMPUTATION,
                priority=task.priority,
                actions=[action],
                category=f"{task.category}_computation",
                tags=task.tags + ["computation_step"]
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    async def _decompose_io_task(self, task: Task) -> List[Task]:
        """分解IO任务"""
        sub_tasks = []
        
        # 根据文件操作类型分解
        file_operations = []
        other_operations = []
        
        for action in task.actions:
            if action.type in ["file_operation", "read", "write"]:
                file_operations.append(action)
            else:
                other_operations.append(action)
        
        # 创建文件操作子任务
        if file_operations:
            sub_task = Task(
                name=f"{task.name}_文件操作",
                description="执行文件相关操作",
                type=TaskType.IO,
                priority=task.priority,
                actions=file_operations,
                category=f"{task.category}_file_io",
                tags=task.tags + ["file_operation"]
            )
            sub_tasks.append(sub_task)
        
        # 创建其他操作子任务
        if other_operations:
            sub_task = Task(
                name=f"{task.name}_其他操作",
                description="执行其他IO操作",
                type=TaskType.IO,
                priority=task.priority,
                actions=other_operations,
                category=f"{task.category}_other_io",
                tags=task.tags + ["other_operation"]
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    async def _decompose_network_task(self, task: Task) -> List[Task]:
        """分解网络任务"""
        sub_tasks = []
        
        # 根据网络操作类型分解
        for i, action in enumerate(task.actions):
            sub_task = Task(
                name=f"{task.name}_网络操作_{i+1}",
                description=f"执行网络操作: {action.type}",
                type=TaskType.NETWORK,
                priority=task.priority,
                actions=[action],
                category=f"{task.category}_network",
                tags=task.tags + ["network_operation"]
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    async def _decompose_storage_task(self, task: Task) -> List[Task]:
        """分解存储任务"""
        sub_tasks = []
        
        # 根据存储操作类型分解
        read_operations = []
        write_operations = []
        
        for action in task.actions:
            if action.type in ["read", "read_file"]:
                read_operations.append(action)
            elif action.type in ["write", "write_file", "save"]:
                write_operations.append(action)
        
        # 创建读取操作子任务
        if read_operations:
            sub_task = Task(
                name=f"{task.name}_读取操作",
                description="执行数据读取操作",
                type=TaskType.STORAGE,
                priority=task.priority,
                actions=read_operations,
                category=f"{task.category}_read",
                tags=task.tags + ["read_operation"]
            )
            sub_tasks.append(sub_task)
        
        # 创建写入操作子任务
        if write_operations:
            sub_task = Task(
                name=f"{task.name}_写入操作",
                description="执行数据写入操作",
                type=TaskType.STORAGE,
                priority=task.priority,
                actions=write_operations,
                category=f"{task.category}_write",
                tags=task.tags + ["write_operation"]
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    async def _decompose_mixed_task(self, task: Task) -> List[Task]:
        """分解混合任务"""
        sub_tasks = []
        
        # 按任务类型分组
        type_groups = {}
        for action in task.actions:
            action_type = action.type
            if action_type not in type_groups:
                type_groups[action_type] = []
            type_groups[action_type].append(action)
        
        # 为每种类型创建子任务
        for action_type, actions in type_groups.items():
            sub_task = Task(
                name=f"{task.name}_{action_type}",
                description=f"执行{action_type}类型的操作",
                type=TaskType.MIXED,
                priority=task.priority,
                actions=actions,
                category=f"{task.category}_{action_type}",
                tags=task.tags + [f"{action_type}_operation"]
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    def _analyze_priority_pattern(self, task: Task) -> Dict[str, Any]:
        """分析任务优先级模式"""
        return {
            "current_priority": task.priority,
            "priority_level": {
                TaskPriority.LOW: 1,
                TaskPriority.NORMAL: 2,
                TaskPriority.HIGH: 3,
                TaskPriority.URGENT: 4
            }.get(task.priority, 2),
            "suggested_priority": self._suggest_priority(task),
            "priority_factors": self._identify_priority_factors(task)
        }
    
    def _suggest_priority(self, task: Task) -> TaskPriority:
        """建议任务优先级"""
        # 基于任务类型和复杂度建议优先级
        if task.type == TaskType.COMPUTATION and len(task.actions) > 5:
            return TaskPriority.HIGH
        
        if "urgent" in task.description.lower() or "critical" in task.description.lower():
            return TaskPriority.URGENT
        
        if task.type == TaskType.NETWORK:
            return TaskPriority.NORMAL
        
        return TaskPriority.LOW
    
    def _identify_priority_factors(self, task: Task) -> List[str]:
        """识别影响优先级的因素"""
        factors = []
        
        # 任务类型因素
        if task.type == TaskType.COMPUTATION:
            factors.append("计算密集型任务")
        
        if task.type == TaskType.NETWORK:
            factors.append("网络依赖任务")
        
        # 动作数量因素
        if len(task.actions) > 10:
            factors.append("动作数量较多")
        
        # 描述关键词因素
        if "urgent" in task.description.lower():
            factors.append("包含紧急关键词")
        
        if "critical" in task.description.lower():
            factors.append("包含关键关键词")
        
        return factors