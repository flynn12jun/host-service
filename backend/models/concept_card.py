from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class ConceptCard(Base):
    """概念卡表"""
    __tablename__ = "concept_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    
    dish_name = Column(String(200), nullable=False)
    food_combination = Column(JSON, nullable=False)  # 食材组合
    flavor_structure = Column(JSON)                  # 风味结构
    plating_direction = Column(Text)                 # 摆盘方向
    estimated_cost = Column(Float)                   # 预估成本
    nutrition_direction = Column(Text)               # 营养方向
    cooking_method = Column(String(100))             # 烹饪方式
    innovation_points = Column(ARRAY(Text))          # 创新点
    reference_images = Column(ARRAY(Text))           # 参考图片URL
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="concept_cards")

    def __repr__(self):
        return f"<ConceptCard(dish_name={self.dish_name})>"