from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from core.database import Base


class WorkflowStatus(str, enum.Enum):
    """工作流状态枚举"""
    CREATED = "created"                    # 已创建
    EXTRACTING = "extracting"              # 需求提取中
    NUTRITION_DESIGNING = "nutrition_designing"  # 营养设计中
    CONCEPT_DESIGNING = "concept_designing"      # 概念设计中
    RECIPE_REVIEWING = "recipe_reviewing"        # 食谱审评中
    WAITING_APPROVAL = "waiting_approval"        # 等待审批
    APPROVED = "approved"                  # 已通过
    REJECTED = "rejected"                  # 已驳回
    REVISING = "revising"                  # 修改中
    COMPLETED = "completed"               # 已完成
    FAILED = "failed"                     # 失败


class Workflow(Base):
    """工作流主表"""
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_input = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default=WorkflowStatus.CREATED.value)
    revision_count = Column(Integer, default=0)
    max_revisions = Column(Integer, default=3)
    
    # 各阶段输出（JSON格式）
    director_output = Column(JSONB)
    nutritionist_output = Column(JSONB)
    rd_chef_output = Column(JSONB)
    head_chef_output = Column(JSONB)
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关系
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    concept_cards = relationship("ConceptCard", back_populates="workflow", cascade="all, delete-orphan")
    recipe_cards = relationship("RecipeCard", back_populates="workflow", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow(id={self.id}, status={self.status})>"


class WorkflowStep(Base):
    """工作流步骤表"""
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    agent_role = Column(String(50), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="steps")

    def __repr__(self):
        return f"<WorkflowStep(workflow_id={self.workflow_id}, agent={self.agent_role})>"


