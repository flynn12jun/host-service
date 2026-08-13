from typing import Dict, Any
from models.agent import AgentRole
from agents.base import BaseAgent


class OperationsDirectorAgent(BaseAgent):
    """
    运营总监Agent
    - 接收客户原始输入
    - 提取关键信息
    - 结构化需求并下发
    """
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.OPERATIONS_DIRECTOR
    
    @property
    def name(self) -> str:
        return "运营总监"
    
    @property
    def system_prompt(self) -> str:
        return """
你是HOST轻食运营总监，负责接收客户需求并提取关键信息。

你的职责：
1. 识别任务类型（单品菜品设计 / 团餐方案设计）
2. 提取菜品要求：口味偏好、烹饪方式、食材禁忌等
3. 提取营养要求：热量范围、蛋白质需求、特殊饮食等
4. 提取团餐信息：人数、餐数、用餐场景等
5. 识别目标人群：儿童、上班族、健身人群等
6. 确定预算范围

输出格式必须是结构化的JSON数据，包含以下字段：
- task_type: 任务类型 ("dish" 单品菜品 / "group_meal" 团餐方案)
- dish_requirements: 菜品要求对象 (flavor口味、cooking_method烹饪方式、ingredient_restrictions食材禁忌)
- nutrition_requirements: 营养要求对象 (calories_range热量范围、protein_min蛋白质需求、fat_max脂肪限制、special_diet特殊饮食)
- group_meal_info: 团餐信息对象 (仅团餐任务，包含people_count人数、meal_count餐数、scene场景)
- target_audience: 目标人群字符串
- budget_range: 预算范围数组 [min, max]
- special_requirements: 特殊要求列表

请确保输出严格符合JSON格式，不要包含任何额外说明文字。
"""
    
    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        customer_input = input_data.get("customer_input") or ""
        return f"""
请分析以下客户需求，提取关键信息：

客户需求：
{customer_input}

请以JSON格式输出提取结果。
"""
    
    async def _validate_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证运营总监输出"""
        # 检查错误
        if "error" in raw_output:
            raise ValueError(f"LLM输出错误: {raw_output.get('message', '未知错误')}")
        
        # 确保必填字段存在
        required_fields = ["task_type", "dish_requirements", "nutrition_requirements"]
        for field in required_fields:
            if field not in raw_output:
                raw_output[field] = {} if field != "task_type" else "dish"
        
        # 设置默认值
        raw_output.setdefault("target_audience", "通用")
        raw_output.setdefault("budget_range", [10, 30])
        raw_output.setdefault("special_requirements", [])
        
        return raw_output