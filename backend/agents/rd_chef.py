from typing import Dict, Any
from models.agent import AgentRole
from agents.base import BaseAgent


class RDChefAgent(BaseAgent):
    """
    研发主厨Agent
    - 接收营养师的食材结构
    - 设计菜品概念卡
    - 设计团餐定制方案
    """
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.RD_CHEF
    
    @property
    def name(self) -> str:
        return "研发主厨"
    
    @property
    def system_prompt(self) -> str:
        return """
你是HOST轻食研发主厨，负责创新菜品设计。

你的职责：
1. 根据食材结构设计创新菜品
2. 设计风味结构（酸甜苦辣咸鲜平衡）
3. 确定摆盘方向和视觉呈现
4. 估算成本
5. 突出营养方向
6. 设计团餐方案（如适用）

输出格式必须是结构化的JSON数据，包含以下字段：
- concept_card: 概念卡对象
  - dish_name: 菜品名称
  - food_combination: 食材组合数组 (包含name、quantity、preparation备注)
  - flavor_structure: 风味结构对象 (sweet甜、sour酸、bitter苦、spicy辣、salty咸、umami鲜)
  - plating_direction: 摆盘方向描述
  - estimated_cost: 预估成本 (元)
  - nutrition_direction: 营养方向描述
  - cooking_method: 烹饪方式
  - innovation_points: 创新点列表
- group_meal_plan: 团餐方案对象 (仅团餐任务)
  - menu_items: 菜单项数组
  - total_cost: 总成本
  - serving_size: 服务人数
  - meal_count: 餐数
  - preparation_timeline: 准备时间线
- design_notes: 设计说明列表
- alternatives: 备选方案列表

请确保输出严格符合JSON格式，不要包含任何额外说明文字。
"""
    
    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        nutritionist_output = input_data.get("nutritionist_output", {})
        director_output = input_data.get("director_output", {})
        
        task_type = director_output.get("task_type", "dish")
        
        prompt = f"""
请根据以下营养方案设计菜品概念：

任务类型：{'单品菜品设计' if task_type == 'dish' else '团餐方案设计'}

营养方案：
热量：{nutritionist_output.get('nutrition_plan', {}).get('calories', 'N/A')} kcal
蛋白质：{nutritionist_output.get('nutrition_plan', {}).get('protein', 'N/A')} g
脂肪：{nutritionist_output.get('nutrition_plan', {}).get('fat', 'N/A')} g
碳水：{nutritionist_output.get('nutrition_plan', {}).get('carbohydrates', 'N/A')} g

食材结构：
{self._format_ingredients(nutritionist_output.get('ingredient_structures', []))}

营养说明：
{', '.join(nutritionist_output.get('nutrition_notes', []))}

营养警告：
{', '.join(nutritionist_output.get('warnings', []))}

原始需求：
{self._format_dict(director_output)}
"""
        
        if task_type == "group_meal":
            group_info = director_output.get("group_meal_info", {})
            prompt += f"""

团餐信息：
- 人数：{group_info.get('people_count', 'N/A')}
- 餐数：{group_info.get('meal_count', 'N/A')}
- 场景：{group_info.get('scene', 'N/A')}
"""
        
        prompt += "\n请以JSON格式输出概念卡设计。"
        return prompt
    
    def _format_ingredients(self, ingredients: list) -> str:
        """格式化食材列表"""
        lines = []
        for ing in ingredients:
            lines.append(
                f"  - {ing.get('name', '未知')}: {ing.get('quantity', 0)}g "
                f"({ing.get('category', '未知')})"
            )
        return "\n".join(lines) if lines else "  无食材信息"
    
    def _format_dict(self, d: Dict, indent: int = 0) -> str:
        """格式化字典"""
        lines = []
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                continue
            prefix = "  " * indent
            lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
    
    async def _validate_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证研发主厨输出"""
        if "error" in raw_output:
            raise ValueError(f"LLM输出错误: {raw_output.get('message', '未知错误')}")
        
        # 确保概念卡存在
        if "concept_card" not in raw_output:
            raw_output["concept_card"] = {}
        
        concept_card = raw_output["concept_card"]
        concept_card.setdefault("dish_name", "未命名菜品")
        concept_card.setdefault("food_combination", [])
        concept_card.setdefault("flavor_structure", {})
        concept_card.setdefault("plating_direction", "")
        concept_card.setdefault("estimated_cost", 0)
        concept_card.setdefault("nutrition_direction", "")
        concept_card.setdefault("cooking_method", "")
        concept_card.setdefault("innovation_points", [])
        
        raw_output.setdefault("design_notes", [])
        raw_output.setdefault("alternatives", [])
        
        return raw_output