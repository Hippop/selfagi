# SelfAGI 系统使用说明

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行演示
```bash
python demo.py
```

### 3. 启动API服务
```bash
python run_api.py
```

### 4. 直接运行系统
```bash
python run.py
```

## 系统功能演示

### 基本功能演示
运行 `python demo.py` 将展示：
- 系统初始化和启动
- 示例任务创建
- 系统状态监控
- 性能指标收集
- 任务统计信息

### 任务管理演示
演示脚本还会展示：
- 多种类型任务创建
- 任务调度和执行
- 任务状态监控
- 任务搜索和列表
- 系统资源管理

## API接口使用

### 启动API服务
```bash
python run_api.py
```

服务启动后，访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 系统信息：http://localhost:8000/system/info

### 主要API端点

#### 系统管理
- `GET /health` - 健康检查
- `GET /system/info` - 系统信息
- `GET /system/status` - 系统状态
- `GET /system/metrics` - 性能指标

#### 任务管理
- `POST /tasks` - 创建任务
- `GET /tasks/{task_id}` - 获取任务
- `PUT /tasks/{task_id}` - 更新任务
- `DELETE /tasks/{task_id}` - 删除任务
- `POST /tasks/list` - 列出任务
- `POST /tasks/search` - 搜索任务
- `POST /tasks/sample` - 创建示例任务

#### 任务控制
- `GET /tasks/{task_id}/status` - 获取任务状态
- `POST /tasks/{task_id}/pause` - 暂停任务
- `POST /tasks/{task_id}/resume` - 恢复任务
- `POST /tasks/{task_id}/cancel` - 取消任务
- `GET /tasks/{task_id}/history` - 获取任务历史

### 创建任务示例

#### LLM推理任务
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "文本情感分析",
    "description": "使用GPT-4分析文本情感倾向",
    "type": "computation",
    "priority": "normal",
    "actions": [
      {
        "name": "情感分析",
        "type": "llm_inference",
        "parameters": {
          "prompt": "分析以下文本的情感倾向：今天天气很好，心情愉快。",
          "model": "gpt-4",
          "max_tokens": 200,
          "temperature": 0.7
        }
      }
    ],
    "tags": ["LLM", "文本分析"],
    "category": "demo"
  }'
```

#### Shell命令任务
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "系统信息收集",
    "description": "收集系统基本信息",
    "type": "io",
    "priority": "low",
    "actions": [
      {
        "name": "系统检查",
        "type": "system_check",
        "parameters": {
          "check_type": "general"
        }
      }
    ],
    "tags": ["系统", "监控"],
    "category": "demo"
  }'
```

## 配置说明

### 环境变量配置
创建 `.env` 文件：
```env
# LLM API配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
ANTHROPIC_API_KEY=your_anthropic_api_key

# 系统配置
DEBUG=true
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=100
TASK_TIMEOUT=3600
```

### 配置文件
主要配置在 `config/settings.py` 中：
- 数据库连接
- Redis配置
- API设置
- 任务执行配置
- 日志配置

## 监控和日志

### 日志文件
- 位置：`logs/selfagi.log`
- 轮转：每天轮转
- 保留：30天

### 系统监控
- 健康检查：每30秒
- 性能指标：实时收集
- 资源使用：CPU、内存、磁盘

### 任务监控
- 执行状态：实时更新
- 执行时间：自动记录
- 错误信息：详细记录

## 故障排除

### 常见问题

#### 1. 系统启动失败
- 检查Python版本（需要3.8+）
- 检查依赖包是否正确安装
- 查看错误日志

#### 2. API服务无法访问
- 检查端口是否被占用
- 确认防火墙设置
- 验证服务是否正常启动

#### 3. 任务执行失败
- 检查任务配置是否正确
- 查看任务执行日志
- 确认执行器是否可用

#### 4. 存储问题
- 检查存储系统健康状态
- 确认数据目录权限
- 查看存储日志

### 调试模式
设置环境变量：
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### 日志级别
- DEBUG：详细调试信息
- INFO：一般信息
- WARNING：警告信息
- ERROR：错误信息

## 扩展开发

### 添加新执行器
1. 继承 `BaseExecutor` 类
2. 实现必要的方法
3. 在系统中注册

### 添加新存储后端
1. 实现 `TaskStorage` 接口
2. 更新配置
3. 修改初始化逻辑

### 添加新任务类型
1. 在枚举中添加新类型
2. 更新分析器逻辑
3. 添加相应执行器

## 性能优化

### 系统调优
- 调整并发任务数量
- 优化任务超时设置
- 配置合适的重试策略

### 资源管理
- 监控CPU和内存使用
- 设置资源限制
- 优化任务调度

## 安全考虑

### 访问控制
- API接口验证
- 任务执行权限
- 资源访问控制

### 数据安全
- 敏感信息加密
- 审计日志记录
- 输入验证过滤

## 部署建议

### 生产环境
- 使用数据库存储后端
- 配置Redis缓存
- 设置监控和告警
- 配置日志聚合

### 容器化部署
- 使用Docker容器
- 配置健康检查
- 设置资源限制
- 配置网络策略

---

**注意**: 当前版本为开发版本，建议在测试环境中使用。生产环境部署前请进行充分测试。