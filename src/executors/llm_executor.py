"""
LLM执行器
用于大模型推理、代码生成、决策制定等任务
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from loguru import logger

from src.executors.base import BaseExecutor
from src.core.models import Task, TaskType
from config.settings import settings


class LLMExecutor(BaseExecutor):
    """LLM执行器"""
    
    def __init__(self):
        super().__init__("LLM执行器", "llm")
        self.supported_models = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet", "claude-3-haiku"],
            "local": ["llama2", "codellama"]
        }
        self.model_configs = {}
        self._init_models()
    
    def _init_models(self):
        """初始化模型配置"""
        if settings.OPENAI_API_KEY:
            self.model_configs["openai"] = {
                "api_key": settings.OPENAI_API_KEY,
                "base_url": settings.OPENAI_BASE_URL,
                "default_model": "gpt-4"
            }
        
        if settings.ANTHROPIC_API_KEY:
            self.model_configs["anthropic"] = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "default_model": "claude-3-sonnet"
            }
    
    async def validate_task(self, task: Task) -> bool:
        """验证任务是否可以执行"""
        # 检查任务类型
        if task.type != TaskType.COMPUTATION:
            return False
        
        # 检查是否有可用的模型
        if not self.model_configs:
            return False
        
        # 检查任务参数
        if not task.actions:
            return False
        
        return True
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行LLM任务"""
        try:
            # 更新负载
            self.update_load(10)
            
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
            self.update_load(-10)
            
            return {
                "status": "success",
                "results": results,
                "final_result": final_result,
                "executor": self.name
            }
            
        except Exception as e:
            # 更新负载
            self.update_load(-10)
            
            # 处理错误
            error_result = await self.handle_error(task, e)
            logger.error(f"LLM任务执行失败: {str(e)}")
            return error_result
    
    async def _execute_action(self, action: Any, task: Task) -> Dict[str, Any]:
        """执行单个动作"""
        try:
            action_type = action.type
            parameters = action.parameters
            
            if action_type == "llm_inference":
                return await self._llm_inference(parameters, task)
            elif action_type == "code_generation":
                return await self._code_generation(parameters, task)
            elif action_type == "decision_making":
                return await self._decision_making(parameters, task)
            elif action_type == "text_analysis":
                return await self._text_analysis(parameters, task)
            else:
                raise ValueError(f"不支持的LLM动作类型: {action_type}")
                
        except Exception as e:
            logger.error(f"动作执行失败: {str(e)}")
            return {
                "status": "error",
                "action_type": action.type,
                "error": str(e)
            }
    
    async def _llm_inference(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """LLM推理"""
        try:
            prompt = parameters.get("prompt", "")
            model = parameters.get("model", "gpt-4")
            max_tokens = parameters.get("max_tokens", 1000)
            temperature = parameters.get("temperature", 0.7)
            
            # 选择模型提供商
            provider = self._select_provider(model)
            if not provider:
                raise Exception(f"未找到可用的模型提供商: {model}")
            
            # 调用LLM API
            response = await self._call_llm_api(provider, model, prompt, max_tokens, temperature)
            
            return {
                "status": "success",
                "action_type": "llm_inference",
                "response": response,
                "model": model,
                "parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"LLM推理失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "llm_inference",
                "error": str(e)
            }
    
    async def _code_generation(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """代码生成"""
        try:
            description = parameters.get("description", "")
            language = parameters.get("language", "python")
            framework = parameters.get("framework", "")
            
            # 构建代码生成提示
            prompt = self._build_code_prompt(description, language, framework)
            
            # 调用LLM生成代码
            response = await self._call_llm_api("openai", "gpt-4", prompt, 2000, 0.3)
            
            # 解析代码
            code = self._extract_code_from_response(response, language)
            
            return {
                "status": "success",
                "action_type": "code_generation",
                "code": code,
                "language": language,
                "framework": framework,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"代码生成失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "code_generation",
                "error": str(e)
            }
    
    async def _decision_making(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """决策制定"""
        try:
            context = parameters.get("context", "")
            options = parameters.get("options", [])
            criteria = parameters.get("criteria", [])
            
            # 构建决策提示
            prompt = self._build_decision_prompt(context, options, criteria)
            
            # 调用LLM进行决策
            response = await self._call_llm_api("anthropic", "claude-3-sonnet", prompt, 1000, 0.1)
            
            # 解析决策结果
            decision = self._extract_decision_from_response(response)
            
            return {
                "status": "success",
                "action_type": "decision_making",
                "decision": decision,
                "reasoning": response,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"决策制定失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "decision_making",
                "error": str(e)
            }
    
    async def _text_analysis(self, parameters: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """文本分析"""
        try:
            text = parameters.get("text", "")
            analysis_type = parameters.get("analysis_type", "general")
            
            # 构建分析提示
            prompt = self._build_analysis_prompt(text, analysis_type)
            
            # 调用LLM进行分析
            response = await self._call_llm_api("openai", "gpt-4", prompt, 1500, 0.5)
            
            return {
                "status": "success",
                "action_type": "text_analysis",
                "analysis": response,
                "analysis_type": analysis_type,
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"文本分析失败: {str(e)}")
            return {
                "status": "error",
                "action_type": "text_analysis",
                "error": str(e)
            }
    
    def _select_provider(self, model: str) -> Optional[str]:
        """选择模型提供商"""
        for provider, models in self.supported_models.items():
            if model in models and provider in self.model_configs:
                return provider
        return None
    
    async def _call_llm_api(self, provider: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """调用LLM API"""
        # 这里应该实现具体的API调用逻辑
        # 为了演示，返回模拟响应
        
        if provider == "openai":
            # 模拟OpenAI API调用
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return f"OpenAI {model} 响应: {prompt[:50]}..."
        elif provider == "anthropic":
            # 模拟Anthropic API调用
            await asyncio.sleep(0.1)
            return f"Anthropic {model} 响应: {prompt[:50]}..."
        else:
            raise Exception(f"不支持的提供商: {provider}")
    
    def _build_code_prompt(self, description: str, language: str, framework: str) -> str:
        """构建代码生成提示"""
        return f"""
请根据以下要求生成{language}代码：

描述: {description}
编程语言: {language}
框架: {framework}

请生成完整、可运行的代码，并添加必要的注释。
"""
    
    def _build_decision_prompt(self, context: str, options: List[str], criteria: List[str]) -> str:
        """构建决策制定提示"""
        options_str = "\n".join([f"- {opt}" for opt in options])
        criteria_str = "\n".join([f"- {c}" for c in criteria])
        
        return f"""
请根据以下信息做出决策：

上下文: {context}

可选方案:
{options_str}

决策标准:
{criteria_str}

请分析每个方案，并给出最佳选择及其理由。
"""
    
    def _build_analysis_prompt(self, text: str, analysis_type: str) -> str:
        """构建文本分析提示"""
        return f"""
请对以下文本进行{analysis_type}分析：

文本内容:
{text}

请提供详细的分析结果。
"""
    
    def _extract_code_from_response(self, response: str, language: str) -> str:
        """从响应中提取代码"""
        # 简单的代码提取逻辑
        if "```" in response:
            start = response.find("```") + 3
            end = response.rfind("```")
            if end > start:
                return response[start:end].strip()
        return response
    
    def _extract_decision_from_response(self, response: str) -> Dict[str, Any]:
        """从响应中提取决策结果"""
        # 简单的决策提取逻辑
        return {
            "decision": "基于分析的最佳选择",
            "confidence": 0.85,
            "reasoning": response
        }
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """获取可用的模型列表"""
        available = {}
        for provider, models in self.supported_models.items():
            if provider in self.model_configs:
                available[provider] = models
        return available
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 测试每个可用的提供商
            for provider in self.model_configs:
                test_prompt = "Hello, this is a test."
                await self._call_llm_api(provider, "test", test_prompt, 10, 0.1)
            return True
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False