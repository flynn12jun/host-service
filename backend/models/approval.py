from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class Approval(Base):
    """审批记录表"""
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id", ondelete="SET NULL"))
    
    status = Column(String(50), nullable=False)      # approved / rejected
    comments = Column(Text)                          # 审批意见
    reviewer = Column(String(100))                   # 审批人
    reviewed_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="approvals")

    def __repr__(self):
        return f"<Approval(workflow_id={self.workflow_id}, status={self.status})>"