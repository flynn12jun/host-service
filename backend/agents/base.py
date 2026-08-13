from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from models.agent import AgentRole, AgentStatus
from services.llm_service import LLMService, LLMAPIError



class AgentResultStatus(Enum):
    """Agent执行结果状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Agent执行结果"""
    status: AgentResultStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """执行耗时"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self._status = AgentStatus.IDLE
        self._current_task: Optional[str] = None
    
    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Agent角色"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent名称"""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """系统提示词"""
        pass
    
    @property
    def status(self) -> AgentStatus:
        return self._status
    
    @property
    def current_task(self) -> Optional[str]:
        return self._current_task
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        执行Agent任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            AgentResult: 执行结果
        """
        self._status = AgentStatus.PROCESSING
        started_at = datetime.utcnow()
        
        try:
            # 构建用户提示词
            user_prompt = self._build_user_prompt(input_data)
            
            # 调用LLM
            result = await self.llm_service.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_format="json"
            )
            
            # 验证输出
            validated_data = await self._validate_output(result)
            
            completed_at = datetime.utcnow()
            self._status = AgentStatus.COMPLETED
            
            return AgentResult(
                status=AgentResultStatus.SUCCESS,
                data=validated_data,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except LLMAPIError:
            self._status = AgentStatus.FAILED
            raise
        except Exception as e:
            self._status = AgentStatus.FAILED
            return AgentResult(
                status=AgentResultStatus.FAILURE,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    @abstractmethod
    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        """构建用户提示词"""
        pass
    
    @abstractmethod
    async def _validate_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证并处理LLM输出"""
        pass
    
    def reset(self):
        """重置Agent状态"""
        self._status = AgentStatus.IDLE
        self._current_task = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "name": self.name,
            "status": self.status.value,
            "current_task": self._current_task,
        }