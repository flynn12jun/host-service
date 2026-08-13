from typing import Dict, Any
from models.agent import AgentRole
from agents.base import BaseAgent


class HeadChefAgent(BaseAgent):
    """
    厨师长Agent
    - 审评研发主厨的方案
    - 设计标准食谱卡
    - 确保可执行性和标准化
    """
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.HEAD_CHEF
    
    @property
    def name(self) -> str:
        return "厨师长"
    
    @property
    def system_prompt(self) -> str:
        return """
你是HOST轻食厨师长，负责审评和标准化食谱。

你的职责：
1. 审评研发主厨的概念卡
2. 将概念转化为可执行的标准食谱
3. 制定详细的制作步骤
4. 确定质量标准和验收标准
5. 计算精确成本
6. 确保食品安全和卫生标准

输出格式必须是结构化的JSON数据，包含以下字段：
- recipe_card: 标准食谱卡对象
  - dish_name: 菜品名称
  - ingredients: 食材清单数组 (name名称、quantity用量、unit单位、preparation预处理、notes备注)
  - seasonings: 调料清单数组 (name名称、quantity用量、unit单位)
  - equipment: 设备需求列表
  - steps: 制作步骤数组
    - step_number: 步骤序号
    - description: 步骤描述
    - duration: 时长 (分钟)
    - temperature: 温度要求 (可选)
    - tips: 技巧提示 (可选)
  - quality_standards: 质量标准列表
  - plating_specification: 摆盘规格描述
  - shelf_life: 保质期描述
  - cost_breakdown: 成本明细对象
    - ingredients_cost: 食材成本
    - seasonings_cost: 调料成本
    - labor_cost: 人工成本
    - total_cost: 总成本
  - nutrition_facts: 营养成分对象
- review_comments: 审评意见
- is_approvable: 是否可通过审批 (boolean)

请确保输出严格符合JSON格式，不要包含任何额外说明文字。
"""
    
    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        rd_output = input_data.get("rd_chef_output", {})
        nutritionist_output = input_data.get("nutritionist_output", {})
        director_output = input_data.get("director_output", {})
        
        concept_card = rd_output.get("concept_card", {})
        
        prompt = f"""
请审评以下概念卡，并设计标准食谱：

概念卡信息：
- 菜品名称：{concept_card.get('dish_name', '未命名')}
- 预估成本：{concept_card.get('estimated_cost', 'N/A')} 元
- 烹饪方式：{concept_card.get('cooking_method', 'N/A')}
- 营养方向：{concept_card.get('nutrition_direction', 'N/A')}
- 摆盘方向：{concept_card.get('planning_direction', 'N/A')}

食材组合：
{self._format_food_combination(concept_card.get('food_combination', []))}

风味结构：
{self._format_flavor(concept_card.get('flavor_structure', {}))}

创新点：
{', '.join(concept_card.get('innovation_points', []))}

营养目标：
热量：{nutritionist_output.get('nutrition_plan', {}).get('calories', 'N/A')} kcal
蛋白质：{nutritionist_output.get('nutrition_plan', {}).get('protein', 'N/A')} g
脂肪：{nutritionist_output.get('nutrition_plan', {}).get('fat', 'N/A')} g
碳水：{nutritionist_output.get('nutrition_plan', {}).get('carbohydrates', 'N/A')} g

原始需求：
目标人群：{director_output.get('target_audience', '通用')}
预算范围：{director_output.get('budget_range', [10, 30])}
特殊要求：{', '.join(director_output.get('special_requirements', []))}

设计说明：
{', '.join(rd_output.get('design_notes', []))}
"""
        
        prompt += "\n请以JSON格式输出标准食谱卡。"
        return prompt
    
    def _format_food_combination(self, items: list) -> str:
        """格式化食材组合"""
        lines = []
        for item in items:
            name = item.get('name', '未知')
            qty = item.get('quantity', '')
            unit = item.get('unit', 'g')
            prep = item.get('preparation', '')
            line = f"  - {name}: {qty}{unit}"
            if prep:
                line += f" ({prep})"
            lines.append(line)
        return "\n".join(lines) if lines else "  无食材信息"
    
    def _format_flavor(self, flavor: Dict) -> str:
        """格式化风味结构"""
        flavor_names = {
            'sweet': '甜', 'sour': '酸', 'bitter': '苦',
            'spicy': '辣', 'salty': '咸', 'umami': '鲜'
        }
        lines = []
        for k, v in flavor.items():
            name = flavor_names.get(k, k)
            if isinstance(v, (int, float)):
                lines.append(f"  - {name}: {v}/10")
            else:
                lines.append(f"  - {name}: {v}")
        return "\n".join(lines) if lines else "  无风味信息"
    
    async def _validate_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证厨师长输出"""
        if "error" in raw_output:
            raise ValueError(f"LLM输出错误: {raw_output.get('message', '未知错误')}")
        
        # 确保食谱卡存在
        if "recipe_card" not in raw_output:
            raw_output["recipe_card"] = {}
        
        recipe_card = raw_output["recipe_card"]
        recipe_card.setdefault("dish_name", "未命名菜品")
        recipe_card.setdefault("ingredients", [])
        recipe_card.setdefault("seasonings", [])
        recipe_card.setdefault("equipment", [])
        recipe_card.setdefault("steps", [])
        recipe_card.setdefault("quality_standards", [])
        recipe_card.setdefault("plating_specification", "")
        recipe_card.setdefault("shelf_life", "")
        recipe_card.setdefault("cost_breakdown", {})
        recipe_card.setdefault("nutrition_facts", {})
        
        raw_output.setdefault("review_comments", "")
        raw_output.setdefault("is_approvable", True)
        
        return raw_output