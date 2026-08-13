import json
import backoff
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI

from core.config import settings


class LLMAPIError(Exception):
    """LLM API 调用异常"""
    def __init__(self, error_code: str, message: str, status_code: Optional[int] = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def _classify_openai_error(e: openai.APIError) -> LLMAPIError:
    """分类 OpenAI API 错误"""
    status = getattr(e, 'status_code', None)
    error_body = getattr(e, 'body', {}) or {}
    error_msg = error_body.get('message', str(e)) if isinstance(error_body, dict) else str(e)
    
    if status == 401:
        return LLMAPIError('API_KEY_INVALID', 'API Key 无效或已过期，请检查配置', status)
    elif status == 403:
        return LLMAPIError('FORBIDDEN', 'API Key 无权限访问该模型', status)
    elif status == 429:
        return LLMAPIError('RATE_LIMIT', 'API 调用频率超限或额度已用完，请稍后重试或更换 API Key', status)
    elif status == 500:
        return LLMAPIError('SERVER_ERROR', 'LLM 服务内部错误，请稍后重试', status)
    elif status == 502:
        return LLMAPIError('BAD_GATEWAY', 'LLM 服务暂时不可用，请稍后重试', status)
    elif status == 503:
        return LLMAPIError('SERVICE_UNAVAILABLE', 'LLM 服务过载或维护中，请稍后重试', status)
    elif status == 404:
        return LLMAPIError('MODEL_NOT_FOUND', f'请求的模型不存在或不可用', status)
    else:
        return LLMAPIError('LLM_ERROR', f'LLM 调用失败: {error_msg}', status)


# 模型路由配置：模型名 -> (api_key, base_url, provider)
# 注：key 为前端显示的名称，也作为 API 调用的 model 参数
MODEL_ROUTERS = {
    # LongCat（美团龙猫）
    "LongCat-2.0": {
        "api_key": settings.LONGCAT_API_KEY,
        "base_url": settings.LONGCAT_BASE_URL,
        "provider": "openai_compatible",
    },
    # 智谱 GLM
    "glm-4": {
        "api_key": settings.ZHIPU_API_KEY,
        "base_url": settings.ZHIPU_BASE_URL,
        "provider": "openai_compatible",
    },
}


class LLMService:
    """
    LLM服务封装
    支持 LongCat（美团龙猫）、智谱 GLM 大模型
    """
    
    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model = model or settings.DEFAULT_LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        
        # 解析模型路由（同时更新 self.model 为正确的模型名）
        router = self._get_model_router(self.model)
        # 如果传入的是旧模型名，更新为路由表中的标准名称
        if self.model in self._LEGACY_MODEL_MAP:
            self.model = self._LEGACY_MODEL_MAP[self.model]
        self._provider = router["provider"]
        
        # 设置API Key
        if api_key:
            self.api_key = api_key
        elif router.get("api_key"):
            self.api_key = router["api_key"]
        else:
            self.api_key = settings.LONGCAT_API_KEY
        
        # 设置base_url
        self._base_url = base_url or router.get("base_url")
        
        # 初始化OpenAI兼容客户端（LongCat使用OpenAI兼容格式）
        if self._provider in ("openai", "openai_compatible"):
            client_kwargs = {"api_key": self.api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._openai_client = AsyncOpenAI(**client_kwargs)
    
    # 旧模型名映射（兼容前端旧版本缓存）
    _LEGACY_MODEL_MAP = {
        "longcat": "LongCat-2.0",
        "longcat-chat": "LongCat-2.0",
        "glm": "glm-4",
        "glm-4v": "glm-4",
    }

    def _get_model_router(self, model: str) -> Dict[str, str]:
        """根据模型名称获取路由配置"""
        # 先检查是否是旧版模型名，转换为新版
        if model in self._LEGACY_MODEL_MAP:
            model = self._LEGACY_MODEL_MAP[model]
        # 精确匹配
        if model in MODEL_ROUTERS:
            return MODEL_ROUTERS[model]
        # 前缀匹配（不区分大小写）
        model_lower = model.lower()
        for prefix, config in MODEL_ROUTERS.items():
            if model_lower == prefix.lower() or model_lower.startswith(prefix.lower() + "-"):
                return config
        # 默认使用LongCat
        return {
            "api_key": settings.LONGCAT_API_KEY,
            "base_url": settings.LONGCAT_BASE_URL,
            "provider": "openai_compatible",
        }
    
    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: str = "json",
        temperature: Optional[float] = None,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        调用LLM生成内容
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response_format: 响应格式 (json/text)
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            解析后的响应数据
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 如果要求JSON格式，添加JSON格式指令
        if response_format == "json":
            messages.append({
                "role": "assistant",
                "content": "请以JSON格式输出结果，确保JSON格式正确且完整。不要包含任何markdown代码块标记。"
            })
        
        # LongCat 使用 OpenAI 兼容格式
        return await self._call_openai(messages, response_format, temperature, max_tokens)
    
    async def _call_openai(
        self,
        messages: List[Dict],
        response_format: str,
        temperature: Optional[float],
        max_tokens: int
    ) -> Dict[str, Any]:
        """调用LongCat API（OpenAI兼容格式）"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        try:
            response = await self._openai_client.chat.completions.create(**kwargs)
        except openai.APIError as e:
            raise _classify_openai_error(e)
        except Exception as e:
            raise LLMAPIError('NETWORK_ERROR', f'网络连接失败: {str(e)}')
        
        content = response.choices[0].message.content
        
        if response_format == "json":
            return self._parse_json_content(content)
        
        return {"content": content}
    
    def _parse_json_content(self, content: str) -> Dict[str, Any]:
        """解析JSON内容，尝试修复常见错误"""
        # 处理 None 或空内容
        if content is None:
            return {
                "error": "LLM_EMPTY_RESPONSE",
                "message": "LLM 返回空响应（content 为 None），可能是模型未返回有效内容"
            }
        # 清理内容
        content = content.strip()
        
        # 移除可能的markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # 尝试修复JSON
            return self._attempt_json_repair(content, str(e))
    
    def _attempt_json_repair(self, content: str, error_msg: str) -> Dict[str, Any]:
        """尝试修复损坏的JSON"""
        import re
        
        # 尝试找到第一个{和最后一个}
        start = content.find("{")
        end = content.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start:end+1])
            except json.JSONDecodeError:
                pass
        
        # 尝试使用正则提取关键内容
        try:
            # 简单的键值对提取
            result = {}
            # 匹配 "key": value 模式
            pattern = r'"([^"]+)"\s*:\s*("(?:[^"\\]|\\.)*"|null|\d+\.?\d*|\{[^}]*\}|\[[^\]]*\])'
            matches = re.findall(pattern, content)
            for key, value in matches:
                try:
                    result[key] = json.loads(value)
                except:
                    result[key] = value.strip('"')
            
            if result:
                return result
        except:
            pass
        
        # 如果所有修复尝试都失败，返回错误信息
        return {
            "error": "JSON_PARSE_ERROR",
            "message": f"无法解析LLM输出: {error_msg}",
            "raw_content": content[:500]
        }
    
    async def close(self):
        """关闭客户端"""
        if self._openai_client:
            await self._openai_client.close()


# 全局LLM服务实例缓存（按模型名称缓存）
_llm_services: Dict[str, LLMService] = {}


def get_llm_service(model: Optional[str] = None) -> LLMService:
    """
    获取LLM服务实例
    
    Args:
        model: 模型名称，如果指定则创建/返回对应模型的服务实例
        
    Returns:
        LLMService: LLM服务实例
    """
    global _llm_services
    
    cache_key = model or "__default__"
    
    if cache_key not in _llm_services:
        _llm_services[cache_key] = LLMService(model=model)
    
    return _llm_services[cache_key]