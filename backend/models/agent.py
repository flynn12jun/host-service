from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from core.database import Base


class AgentRole(str, enum.Enum):
    """Agent角色枚举"""
    OPERATIONS_DIRECTOR = "operations_director"  # 运营总监
    NUTRITIONIST = "nutritionist"                  # 营养师
    RD_CHEF = "rd_chef"                            # 研发主厨
    HEAD_CHEF = "head_chef"                        # 厨师长


class AgentStatus(str, enum.Enum):
    """Agent状态枚举"""
    IDLE = "idle"                    # 空闲
    PROCESSING = "processing"        # 处理中
    WAITING_REVIEW = "waiting_review" # 等待审批
    COMPLETED = "completed"          # 完成
    REJECTED = "rejected"            # 被驳回
    FAILED = "failed"               # 失败


class Agent(Base):
    """Agent配置表"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    model_config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Agent(role={self.role}, name={self.name})>"