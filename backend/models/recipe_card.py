from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class RecipeCard(Base):
    """标准食谱卡表"""
    __tablename__ = "recipe_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    
    dish_name = Column(String(200), nullable=False)
    ingredients = Column(JSON, nullable=False)       # 食材清单
    seasonings = Column(JSON)                        # 调料清单
    equipment = Column(ARRAY(Text))                  # 设备需求
    steps = Column(JSON, nullable=False)             # 制作步骤
    quality_standards = Column(ARRAY(Text))         # 质量标准
    plating_specification = Column(Text)             # 摆盘规格
    shelf_life = Column(String(50))                  # 保质期
    cost_breakdown = Column(JSON)                    # 成本明细
    nutrition_facts = Column(JSON)                   # 营养成分
    version = Column(String(20), default="1.0")     # 版本
    
    # 评审信息
    review_status = Column(String(50), default="pending")
    reviewed_by = Column(String(100))
    review_comments = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="recipe_cards")

    def __repr__(self):
        return f"<RecipeCard(dish_name={self.dish_name}, version={self.version})>"