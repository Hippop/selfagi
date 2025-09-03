"""
核心数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    PAUSED = "paused"       # 已暂停
    CANCELLED = "cancelled"  # 已取消


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    """任务类型枚举"""
    COMPUTATION = "computation"  # 计算任务
    IO = "io"                    # IO任务
    NETWORK = "network"          # 网络任务
    STORAGE = "storage"          # 存储任务
    MIXED = "mixed"              # 混合任务


class TaskEnvironment(BaseModel):
    """任务环境配置"""
    input: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class TaskAction(BaseModel):
    """任务执行动作"""
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str
    parameters: Dict[str, Any] = {}
    timeout: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


class TaskCheckpoint(BaseModel):
    """任务断点"""
    checkpoint_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    data: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RetryStrategy(BaseModel):
    """重试策略"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # 秒
    max_delay: float = 60.0     # 秒
    backoff_factor: float = 2.0
    retry_on_exceptions: List[str] = []


class Task(BaseModel):
    """任务模型"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    # 依赖关系
    dependencies: List[str] = []  # 依赖的任务ID列表
    
    # 环境配置
    environment: TaskEnvironment = Field(default_factory=TaskEnvironment)
    
    # 前置条件
    preconditions: List[str] = []
    
    # 执行动作
    actions: List[TaskAction] = []
    
    # 后置处理
    post_processing: List[str] = []
    
    # 配置
    timeout: Optional[int] = None
    retry_strategy: RetryStrategy = Field(default_factory=RetryStrategy)
    
    # 断点
    checkpoints: List[TaskCheckpoint] = []
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 执行结果
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # 标签和分类
    tags: List[str] = []
    category: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskDependency(BaseModel):
    """任务依赖关系"""
    task_id: str
    dependency_id: str
    dependency_type: str = "required"  # required, optional, conditional
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskExecutionLog(BaseModel):
    """任务执行日志"""
    log_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    level: str  # INFO, WARNING, ERROR, DEBUG
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[Dict[str, Any]] = None