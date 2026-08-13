from typing import Dict, Any
from models.agent import AgentRole
from agents.base import BaseAgent


class NutritionistAgent(BaseAgent):
    """
    营养师Agent
    - 接收运营总监下发的需求
    - 设计营养配比方案
    - 将营养结构转化为食材结构
    """
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.NUTRITIONIST
    
    @property
    def name(self) -> str:
        return "营养师"
    
    @property
    def system_prompt(self) -> str:
        return """
你是HOST轻食专业营养师，负责设计营养配比方案。

你的职责：
1. 根据需求设计营养配比（热量、三大营养素、微量元素）
2. 将营养结构转化为具体食材组合
3. 确保食材组合满足营养需求
4. 考虑食材的季节性、可获得性
5. 标注营养注意事项和禁忌

输出格式必须是结构化的JSON数据，包含以下字段：
- nutrition_plan: 营养方案对象
  - calories: 热量 (kcal)
  - protein: 蛋白质 (g)
  - fat: 脂肪 (g)
  - carbohydrates: 碳水化合物 (g)
  - fiber: 膳食纤维 (g)
  - sodium: 钠 (mg)
  - vitamins: 维生素对象
  - minerals: 矿物质对象
- ingredient_structures: 食材结构数组
  - ingredient_id: 食材ID
  - name: 食材名称
  - category: 类别 (蔬菜/水果/谷物/蛋白质/油脂/调味品)
  - quantity: 用量 (g)
  - nutrition_contribution: 营养贡献度 (0-1)
- nutrition_notes: 营养说明列表
- warnings: 营养警告列表

注意：
- 食材用量精确到克
- 营养数据精确到小数点后1位
- 考虑食材的季节性和可获得性
- 确保营养均衡

请确保输出严格符合JSON格式，不要包含任何额外说明文字。
"""
    
    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        director_output = input_data.get("director_output", {})
        return f"""
请根据以下需求信息，设计营养配比方案：

需求信息：
{self._format_dict(director_output)}

请以JSON格式输出营养配比方案。
"""
    
    def _format_dict(self, d: Dict, indent: int = 0) -> str:
        """格式化字典为可读字符串"""
        lines = []
        for k, v in d.items():
            prefix = "  " * indent
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(self._format_dict(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}: {', '.join(str(x) for x in v)}")
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
    
    async def _validate_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证营养师输出"""
        if "error" in raw_output:
            raise ValueError(f"LLM输出错误: {raw_output.get('message', '未知错误')}")
        
        # 确保必填字段存在
        if "nutrition_plan" not in raw_output:
            raw_output["nutrition_plan"] = {}
        
        if "ingredient_structures" not in raw_output:
            raw_output["ingredient_structures"] = []
        
        raw_output.setdefault("nutrition_notes", [])
        raw_output.setdefault("warnings", [])
        
        return raw_output