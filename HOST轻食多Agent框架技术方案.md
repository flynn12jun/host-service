# HOST轻食 多Agent框架 技术方案

## 1. 项目概述

### 1.1 项目背景
HOST轻食多Agent框架是一个基于多Agent协同工作的智能菜品研发工作流系统。通过模拟真实厨房团队的角色分工，实现从客户需求输入到标准化食谱输出的全流程自动化，同时提供可视化审批机制。

### 1.2 核心价值
- **智能化研发**：AI驱动的菜品创新与设计
- **流程标准化**：从需求到食谱的标准化流程
- **可视化协作**：实时展示各Agent工作状态与产出
- **人工审批**：关键环节人工把控，确保质量

### 1.3 技术目标
- 支持多Agent协同工作流
- 实时状态推送与可视化展示
- 可扩展的Agent角色体系
- 标准化的数据流转协议

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           前端展示层 (Frontend)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  需求输入    │  │  Agent状态   │  │  概念卡展示  │  │  审批面板    │   │
│  │   模块      │  │   面板      │  │   模块      │  │   模块      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket / HTTP
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API网关层 (API Gateway)                        │
│                    路由 / 认证 / 限流 / 日志                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         工作流引擎层 (Workflow Engine)                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    工作流编排器 (Orchestrator)                    │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │   │
│  │  │ 运营总监 │───▶│ 营养师  │───▶│ 研发主厨 │───▶│ 厨师长  │     │   │
│  │  │  Agent  │    │  Agent  │    │  Agent  │    │  Agent  │     │   │
│  │  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │   │
│  │       │              │              │              │           │   │
│  │       ▼              ▼              ▼              ▼           │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              共享状态管理 (Shared State)                  │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          基础设施层 (Infrastructure)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  LLM服务    │  │  向量数据库  │  │  关系数据库  │  │  消息队列   │   │
│  │ (OpenAI等)  │  │ (Pinecone)  │  │ (PostgreSQL)│  │  (Redis)   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | React 18 + TypeScript | 组件化开发，类型安全 |
| 状态管理 | Zustand | 轻量级状态管理 |
| UI组件库 | Ant Design | 企业级UI组件 |
| 实时通信 | Socket.IO | WebSocket双向通信 |
| 后端框架 | FastAPI (Python) | 高性能异步框架 |
| 工作流引擎 | LangGraph / 自研 | Agent编排与状态管理 |
| LLM | GPT-4 / Claude 3.5 | 大语言模型 |
| 数据库 | PostgreSQL + Redis | 持久化 + 缓存 |
| 消息队列 | Redis Pub/Sub | 轻量级消息传递 |
| 部署 | Docker + K8s | 容器化部署 |

---

## 3. Agent角色设计

### 3.1 Agent角色定义

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentRole(Enum):
    """Agent角色枚举"""
    OPERATIONS_DIRECTOR = "operations_director"  # 运营总监
    NUTRITIONIST = "nutritionist"                  # 营养师
    RD_CHEF = "rd_chef"                            # 研发主厨
    HEAD_CHEF = "head_chef"                        # 厨师长


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"                    # 空闲
    PROCESSING = "processing"        # 处理中
    WAITING_REVIEW = "waiting_review" # 等待审批
    COMPLETED = "completed"          # 完成
    REJECTED = "rejected"            # 被驳回


@dataclass
class Agent:
    """Agent基础定义"""
    role: AgentRole
    name: str
    description: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 3.2 运营总监 (Operations Director)

```python
@dataclass
class OperationsDirectorOutput:
    """运营总监输出结构"""
    task_type: str                          # 任务类型: "dish" | "group_meal"
    dish_requirements: Optional[Dict] = None   # 菜品要求
    nutrition_requirements: Optional[Dict] = None # 营养要求
    group_meal_info: Optional[Dict] = None      # 团餐信息
    target_audience: Optional[str] = None       # 目标人群
    budget_range: Optional[str] = None          # 预算范围
    special_requirements: Optional[List] = None # 特殊要求
    extracted_at: datetime = field(default_factory=datetime.now)


class OperationsDirectorAgent:
    """
    运营总监Agent
    - 接收客户原始输入
    - 提取关键信息
    - 结构化需求并下发
    """
    
    SYSTEM_PROMPT = """
    你是HOST轻食运营总监，负责接收客户需求并提取关键信息。
    
    你的职责：
    1. 识别任务类型（单品菜品设计 / 团餐方案设计）
    2. 提取菜品要求：口味偏好、烹饪方式、食材禁忌等
    3. 提取营养要求：热量范围、蛋白质需求、特殊饮食等
    4. 提取团餐信息：人数、餐数、用餐场景等
    5. 识别目标人群：儿童、上班族、健身人群等
    6. 确定预算范围
    
    输出格式必须是结构化的JSON数据。
    """
    
    async def process(self, customer_input: str) -> OperationsDirectorOutput:
        """处理客户输入"""
        # 1. 调用LLM提取关键信息
        # 2. 结构化输出
        # 3. 验证必填字段
        pass
```

### 3.3 营养师 (Nutritionist)

```python
@dataclass
class NutritionPlan:
    """营养方案"""
    calories: float             # 热量 (kcal)
    protein: float              # 蛋白质 (g)
    fat: float                  # 脂肪 (g)
    carbohydrates: float        # 碳水化合物 (g)
    fiber: float                # 膳食纤维 (g)
    sodium: float               # 钠 (mg)
    vitamins: Dict[str, float]  # 维生素
    minerals: Dict[str, float]  # 矿物质


@dataclass
class IngredientStructure:
    """食材结构"""
    ingredient_id: str
    name: str
    category: str          # 蔬菜/水果/谷物/蛋白质/油脂
    quantity: float        # 用量 (g)
    nutrition_contribution: float  # 营养贡献度


@dataclass
class NutritionistOutput:
    """营养师输出结构"""
    nutrition_plan: NutritionPlan
    ingredient_structures: List[IngredientStructure]
    nutrition_notes: List[str]   # 营养说明
    warnings: List[str]          # 营养警告


class NutritionistAgent:
    """
    营养师Agent
    - 接收运营总监下发的需求
    - 设计营养配比方案
    - 将营养结构转化为食材结构
    """
    
    SYSTEM_PROMPT = """
    你是HOST轻食专业营养师，负责设计营养配比方案。
    
    你的职责：
    1. 根据需求设计营养配比（热量、三大营养素、微量元素）
    2. 将营养结构转化为具体食材组合
    3. 确保食材组合满足营养需求
    4. 考虑食材的季节性、可获得性
    5. 标注营养注意事项和禁忌
    
    输出格式必须是结构化的JSON数据。
    """
    
    async def process(self, director_output: OperationsDirectorOutput) -> NutritionistOutput:
        """处理运营总监输出"""
        # 1. 分析营养需求
        # 2. 设计营养配比
        # 3. 匹配食材
        # 4. 生成食材结构
        pass
```

### 3.4 研发主厨 (R&D Chef)

```python
@dataclass
class ConceptCard:
    """概念卡"""
    dish_name: str                      # 菜品名称
    food_combination: List[Dict]        # 食材组合
    flavor_structure: Dict[str, Any]    # 风味结构
    plating_direction: str              # 摆盘方向
    estimated_cost: float               # 预估成本
    nutrition_direction: str            # 营养方向
    cooking_method: str                 # 烹饪方式
    innovation_points: List[str]        # 创新点
    reference_images: List[str]         # 参考图片URL


@dataclass
class GroupMealPlan:
    """团餐方案"""
    menu_items: List[ConceptCard]       # 菜单项
    total_cost: float                   # 总成本
    serving_size: int                   # 服务人数
    meal_count: int                     # 餐数
    preparation_timeline: List[Dict]    # 准备时间线


@dataclass
class RDChefOutput:
    """研发主厨输出结构"""
    concept_card: Optional[ConceptCard] = None
    group_meal_plan: Optional[GroupMealPlan] = None
    design_notes: List[str] = field(default_factory=list)
    alternatives: List[Dict] = field(default_factory=list)


class RDChefAgent:
    """
    研发主厨Agent
    - 接收营养师的食材结构
    - 设计菜品概念卡
    - 设计团餐定制方案
    """
    
    SYSTEM_PROMPT = """
    你是HOST轻食研发主厨，负责创新菜品设计。
    
    你的职责：
    1. 根据食材结构设计创新菜品
    2. 设计风味结构（酸甜苦辣咸鲜平衡）
    3. 确定摆盘方向和视觉呈现
    4. 估算成本
    5. 突出营养方向
    6. 设计团餐方案（如适用）
    
    输出格式必须是结构化的JSON数据。
    """
    
    async def process(self, nutritionist_output: NutritionistOutput) -> RDChefOutput:
        """处理营养师输出"""
        # 1. 分析食材结构
        # 2. 创意菜品设计
        # 3. 风味平衡设计
        # 4. 成本估算
        # 5. 生成概念卡
        pass
```

### 3.5 厨师长 (Head Chef)

```python
@dataclass
class RecipeStep:
    """食谱步骤"""
    step_number: int
    description: str
    duration: int              # 时长 (分钟)
    temperature: Optional[str] # 温度要求
    tips: Optional[str]        # 技巧提示


@dataclass
class StandardRecipeCard:
    """标准食谱卡"""
    recipe_id: str
    dish_name: str
    version: str
    ingredients: List[Dict]        # 食材清单
    seasonings: List[Dict]         # 调料清单
    equipment: List[str]           # 设备需求
    steps: List[RecipeStep]        # 制作步骤
    quality_standards: List[str]   # 质量标准
    plating_specification: str     # 摆盘规格
    shelf_life: str                # 保质期
    cost_breakdown: Dict[str, float] # 成本明细
    nutrition_facts: Dict          # 营养成分
    review_status: str             # 评审状态
    reviewed_by: Optional[str]     # 评审人
    review_comments: Optional[str] # 评审意见
    created_at: datetime = field(default_factory=datetime.now)


class HeadChefAgent:
    """
    厨师长Agent
    - 审评研发主厨的方案
    - 设计标准食谱卡
    - 确保可执行性和标准化
    """
    
    SYSTEM_PROMPT = """
    你是HOST轻食厨师长，负责审评和标准化食谱。
    
    你的职责：
    1. 审评研发主厨的概念卡
    2. 将概念转化为可执行的标准食谱
    3. 制定详细的制作步骤
    4. 确定质量标准和验收标准
    5. 计算精确成本
    6. 确保食品安全和卫生标准
    
    输出格式必须是结构化的JSON数据。
    """
    
    async def process(self, rd_output: RDChefOutput) -> StandardRecipeCard:
        """处理研发主厨输出"""
        # 1. 审评概念卡
        # 2. 标准化食谱
        # 3. 制定步骤
        # 4. 确定质量标准
        # 5. 生成标准食谱卡
        pass
```

---

## 4. 工作流引擎设计

### 4.1 工作流状态机

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class WorkflowStatus(Enum):
    """工作流状态"""
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


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.CREATED
    customer_input: str = ""
    
    # 各阶段输出
    director_output: Optional[Dict] = None
    nutritionist_output: Optional[Dict] = None
    rd_chef_output: Optional[Dict] = None
    head_chef_output: Optional[Dict] = None
    
    # 审批信息
    approval_status: Optional[str] = None
    approval_comments: Optional[str] = None
    approved_by: Optional[str] = None
    
    # 迭代计数
    revision_count: int = 0
    max_revisions: int = 3
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 错误信息
    error_message: Optional[str] = None


class WorkflowEngine:
    """
    工作流引擎
    负责编排各Agent协同工作，管理状态流转
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.state_observers: List[callable] = []
    
    async def create_workflow(self, customer_input: str) -> str:
        """创建工作流实例"""
        context = WorkflowContext(customer_input=customer_input)
        self.active_workflows[context.workflow_id] = context
        
        # 启动工作流
        await self._start_workflow(context.workflow_id)
        return context.workflow_id
    
    async def _start_workflow(self, workflow_id: str):
        """启动工作流"""
        context = self.active_workflows[workflow_id]
        await self._update_status(workflow_id, WorkflowStatus.EXTRACTING)
        
        try:
            # Step 1: 运营总监提取需求
            director_output = await self._run_operations_director(context)
            context.director_output = director_output
            await self._update_status(workflow_id, WorkflowStatus.NUTRITION_DESIGNING)
            
            # Step 2: 营养师设计营养方案
            nutritionist_output = await self._run_nutritionist(context)
            context.nutritionist_output = nutritionist_output
            await self._update_status(workflow_id, WorkflowStatus.CONCEPT_DESIGNING)
            
            # Step 3: 研发主厨设计概念卡
            rd_output = await self._run_rd_chef(context)
            context.rd_chef_output = rd_output
            await self._update_status(workflow_id, WorkflowStatus.RECIPE_REVIEWING)
            
            # Step 4: 厨师长审评并生成标准食谱
            head_chef_output = await self._run_head_chef(context)
            context.head_chef_output = head_chef_output
            await self._update_status(workflow_id, WorkflowStatus.WAITING_APPROVAL)
            
        except Exception as e:
            context.error_message = str(e)
            await self._update_status(workflow_id, WorkflowStatus.FAILED)
    
    async def approve_workflow(self, workflow_id: str, approved: bool, comments: str, reviewer: str):
        """审批工作流"""
        context = self.active_workflows[workflow_id]
        
        if approved:
            context.approval_status = "approved"
            context.approval_comments = comments
            context.approved_by = reviewer
            await self._update_status(workflow_id, WorkflowStatus.APPROVED)
            await self._update_status(workflow_id, WorkflowStatus.COMPLETED)
        else:
            context.approval_status = "rejected"
            context.approval_comments = comments
            context.approved_by = reviewer
            
            if context.revision_count < context.max_revisions:
                context.revision_count += 1
                await self._update_status(workflow_id, WorkflowStatus.REVISING)
                # 打回研发主厨重新设计
                await self._revise_concept(workflow_id, comments)
            else:
                await self._update_status(workflow_id, WorkflowStatus.FAILED)
    
    async def _update_status(self, workflow_id: str, new_status: WorkflowStatus):
        """更新工作流状态并通知观察者"""
        context = self.active_workflows[workflow_id]
        old_status = context.status
        context.status = new_status
        context.updated_at = datetime.now()
        
        # 通知状态变更
        await self._notify_status_change(workflow_id, old_status, new_status)
    
    async def _notify_status_change(self, workflow_id: str, old_status: WorkflowStatus, new_status: WorkflowStatus):
        """通知前端状态变更"""
        # 通过WebSocket推送状态变更
        pass
```

### 4.2 工作流时序图

```
客户          前端          API         运营总监      营养师      研发主厨      厨师长
 │             │             │             │             │             │             │
 │──输入需求──▶│             │             │             │             │             │
 │             │──创建请求──▶│             │             │             │             │
 │             │             │──提取需求──▶│             │             │             │
 │             │             │             │───处理中───▶│             │             │
 │             │◀──状态推送──│◀────────────│             │             │             │
 │             │             │◀──输出──────│             │             │             │
 │             │             │──营养设计──▶│             │             │             │
 │             │             │             │───处理中───▶│             │             │
 │             │◀──状态推送──│◀────────────│◀────────────│             │             │
 │             │             │◀──输出──────│             │             │             │
 │             │             │──概念设计──▶│             │             │             │
 │             │             │             │             │───处理中───▶│             │
 │             │◀──状态推送──│◀────────────│◀────────────│◀────────────│             │
 │             │             │◀──输出──────│             │             │             │
 │             │             │──食谱审评──▶│             │             │             │
 │             │             │             │             │             │───处理中───▶│
 │             │◀──状态推送──│◀────────────│◀────────────│◀────────────│◀────────────│
 │             │             │◀──输出──────│             │             │             │
 │             │◀──展示食谱卡─│             │             │             │             │
 │◀──展示──────│             │             │             │             │             │
 │             │             │             │             │             │             │
 │──审批操作──▶│             │             │             │             │             │
 │             │──提交审批──▶│             │             │             │             │
 │             │             │──审批处理──▶│             │             │             │
 │             │             │             │             │             │             │
 │             │             │  [通过]     │             │             │             │
 │             │◀──完成通知──│◀────────────│             │             │             │
 │◀──完成──────│             │             │             │             │             │
 │             │             │             │             │             │             │
 │             │             │  [驳回]     │             │             │             │
 │             │◀──驳回通知──│◀───────────────────────────────────────│             │
 │             │             │──重新设计──▶│             │             │             │
 │             │             │             │             │───修改中───▶│             │
 │             │             │             │             │             │             │
```

---

## 5. 数据模型设计

### 5.1 数据库ER图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   workflows     │       │  workflow_steps  │       │   agents        │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │    ┌──│ id (PK)         │
│ customer_input  │  └───▶│ workflow_id(FK) │    │  │ role            │
│ status          │       │ agent_role      │    │  │ name            │
│ revision_count  │       │ status          │    │  │ description     │
│ created_at      │       │ input_data      │    │  │ system_prompt   │
│ updated_at      │       │ output_data     │    │  │ created_at      │
│ completed_at    │       │ started_at      │    │  └─────────────────┘
└─────────────────┘       │ completed_at    │    │
                          │ error_message   │    │  ┌─────────────────┐
                          └─────────────────┘    │  │  approvals      │
                                                   │  ├─────────────────┤
┌─────────────────┐                               │  │ id (PK)         │
│  concept_cards  │                               │  │ workflow_id(FK) │
├─────────────────┤                               │  │ step_id (FK)    │
│ id (PK)         │                               │  │ status          │
│ workflow_id(FK) │                               │  │ comments        │
│ dish_name       │                               │  │ reviewer        │
│ food_combination│                               │  │ reviewed_at     │
│ flavor_structure│                               │  └─────────────────┘
│ plating_direction│                              │
│ estimated_cost  │                               │
│ created_at      │                               │
└─────────────────┘                               │
                                                   │
┌─────────────────┐                               │
│ recipe_cards    │                               │
├─────────────────┤                               │
│ id (PK)         │                               │
│ workflow_id(FK) │                               │
│ dish_name       │                               │
│ ingredients     │                               │
│ steps           │                               │
│ quality_standards│                              │
│ cost_breakdown  │                               │
│ nutrition_facts │                               │
│ version         │                               │
│ created_at      │                               │
└─────────────────┘                               │
```

### 5.2 核心数据表结构

```sql
-- 工作流主表
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_input TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    revision_count INT DEFAULT 0,
    max_revisions INT DEFAULT 3,
    director_output JSONB,
    nutritionist_output JSONB,
    rd_chef_output JSONB,
    head_chef_output JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 工作流步骤表
CREATE TABLE workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    agent_role VARCHAR(50) NOT NULL,
    step_order INT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- 概念卡表
CREATE TABLE concept_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    dish_name VARCHAR(200) NOT NULL,
    food_combination JSONB NOT NULL,
    flavor_structure JSONB,
    plating_direction TEXT,
    estimated_cost DECIMAL(10, 2),
    nutrition_direction TEXT,
    cooking_method VARCHAR(100),
    innovation_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 标准食谱卡表
CREATE TABLE recipe_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    dish_name VARCHAR(200) NOT NULL,
    ingredients JSONB NOT NULL,
    seasonings JSONB,
    equipment TEXT[],
    steps JSONB NOT NULL,
    quality_standards TEXT[],
    plating_specification TEXT,
    cost_breakdown JSONB,
    nutrition_facts JSONB,
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 审批记录表
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    step_id UUID REFERENCES workflow_steps(id),
    status VARCHAR(50) NOT NULL,
    comments TEXT,
    reviewer VARCHAR(100),
    reviewed_at TIMESTAMP DEFAULT NOW()
);

-- Agent配置表
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    model_config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 6. API接口设计

### 6.1 RESTful API

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

app = FastAPI(title="HOST轻食多Agent框架 API", version="1.0.0")


# ==================== 请求/响应模型 ====================

class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""
    customer_input: str
    metadata: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    """审批请求"""
    approved: bool
    comments: str
    reviewer: str


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    status: str
    customer_input: str
    created_at: str
    updated_at: str


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    role: str
    name: str
    status: str
    current_task: Optional[str]
    output: Optional[Dict]


class ConceptCardResponse(BaseModel):
    """概念卡响应"""
    dish_name: str
    food_combination: List[Dict]
    flavor_structure: Dict
    plating_direction: str
    estimated_cost: float
    nutrition_direction: str
    cooking_method: str
    innovation_points: List[str]


class RecipeCardResponse(BaseModel):
    """标准食谱卡响应"""
    recipe_id: str
    dish_name: str
    ingredients: List[Dict]
    seasonings: List[Dict]
    equipment: List[str]
    steps: List[Dict]
    quality_standards: List[str]
    cost_breakdown: Dict
    nutrition_facts: Dict
    version: str


# ==================== API端点 ====================

@app.post("/api/v1/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(request: CreateWorkflowRequest):
    """
    创建新的菜品研发工作流
    
    接收客户输入，启动多Agent协同工作流程
    """
    workflow_id = await workflow_engine.create_workflow(request.customer_input)
    context = workflow_engine.active_workflows[workflow_id]
    return WorkflowResponse(
        workflow_id=context.workflow_id,
        status=context.status.value,
        customer_input=context.customer_input,
        created_at=context.created_at.isoformat(),
        updated_at=context.updated_at.isoformat()
    )


@app.get("/api/v1/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """获取工作流状态"""
    context = workflow_engine.active_workflows.get(workflow_id)
    if not context:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return WorkflowResponse(
        workflow_id=context.workflow_id,
        status=context.status.value,
        customer_input=context.customer_input,
        created_at=context.created_at.isoformat(),
        updated_at=context.updated_at.isoformat()
    )


@app.get("/api/v1/workflows/{workflow_id}/agents", response_model=List[AgentStatusResponse])
async def get_agent_statuses(workflow_id: str):
    """获取所有Agent状态"""
    # 返回各Agent当前状态
    pass


@app.get("/api/v1/workflows/{workflow_id}/concept-card", response_model=ConceptCardResponse)
async def get_concept_card(workflow_id: str):
    """获取概念卡"""
    context = workflow_engine.active_workflows.get(workflow_id)
    if not context or not context.rd_chef_output:
        raise HTTPException(status_code=404, detail="概念卡不存在")
    return context.rd_chef_output.get("concept_card")


@app.get("/api/v1/workflows/{workflow_id}/recipe-card", response_model=RecipeCardResponse)
async def get_recipe_card(workflow_id: str):
    """获取标准食谱卡"""
    context = workflow_engine.active_workflows.get(workflow_id)
    if not context or not context.head_chef_output:
        raise HTTPException(status_code=404, detail="食谱卡不存在")
    return context.head_chef_output


@app.post("/api/v1/workflows/{workflow_id}/approve")
async def approve_workflow(workflow_id: str, request: ApprovalRequest):
    """
    审批工作流
    
    - approved=true: 通过，流程完成
    - approved=false: 驳回，打回研发主厨重新设计
    """
    await workflow_engine.approve_workflow(
        workflow_id=workflow_id,
        approved=request.approved,
        comments=request.comments,
        reviewer=request.reviewer
    )
    return {"message": "审批已提交", "workflow_id": workflow_id}


@app.get("/api/v1/workflows/{workflow_id}/history")
async def get_workflow_history(workflow_id: str):
    """获取工作流历史记录（用于追溯和审计）"""
    pass


# ==================== WebSocket实时通信 ====================

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workflow_id: str):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, workflow_id: str):
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
    
    async def broadcast(self, workflow_id: str, message: Dict):
        """向所有连接的客户端广播消息"""
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/workflows/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket实时推送工作流状态
    
    推送内容：
    - Agent状态变更
    - 步骤完成通知
    - 审批请求
    - 错误通知
    """
    await manager.connect(websocket, workflow_id)
    try:
        while True:
            # 接收客户端消息（如心跳）
            data = await websocket.receive_text()
            # 处理客户端消息
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id)
```

### 6.2 WebSocket消息协议

```json
// Agent状态变更消息
{
    "type": "agent_status_change",
    "workflow_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "agent_role": "nutritionist",
        "agent_name": "营养师",
        "old_status": "idle",
        "new_status": "processing",
        "current_task": "设计营养配比方案"
    }
}

// 步骤完成消息
{
    "type": "step_completed",
    "workflow_id": "uuid",
    "timestamp": "2024-01-15T10:35:00Z",
    "data": {
        "agent_role": "nutritionist",
        "output": { /* 营养师输出数据 */ }
    }
}

// 审批请求消息
{
    "type": "approval_required",
    "workflow_id": "uuid",
    "timestamp": "2024-01-15T10:45:00Z",
    "data": {
        "recipe_card": { /* 标准食谱卡数据 */ },
        "message": "请审评标准食谱卡"
    }
}

// 工作流完成消息
{
    "type": "workflow_completed",
    "workflow_id": "uuid",
    "timestamp": "2024-01-15T10:50:00Z",
    "data": {
        "status": "approved",
        "recipe_card": { /* 最终食谱卡 */ }
    }
}

// 错误消息
{
    "type": "error",
    "workflow_id": "uuid",
    "timestamp": "2024-01-15T10:32:00Z",
    "data": {
        "error_code": "AGENT_TIMEOUT",
        "message": "Agent处理超时"
    }
}
```

---

## 7. 前端设计

### 7.1 页面结构

```
┌─────────────────────────────────────────────────────────────────┐
│                        HOST轻食 多Agent框架                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    需求输入区域                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 请输入您的需求...                                    │  │  │
│  │  │ 例如：设计一款适合健身人群的高蛋白低脂菜品            │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                    [ 开始设计 ]                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Agent工作状态面板                        │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │  │
│  │  │ 运营总监 │──▶│ 营养师  │──▶│ 研发主厨 │──▶│ 厨师长  │  │  │
│  │  │  ✓完成  │   │  ●处理中 │   │  ○等待  │   │  ○等待  │  │  │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    概念卡 / 食谱卡展示                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  菜品名称：香煎鸡胸肉配藜麦沙拉                      │  │  │
│  │  │  ─────────────────────────────────────────────────  │  │  │
│  │  │  食材组合：                                          │  │  │
│  │  │    • 鸡胸肉 150g                                    │  │  │
│  │  │    • 藜麦 80g                                       │  │  │
│  │  │    • 混合生菜 100g                                  │  │  │
│  │  │    • 小番茄 50g                                     │  │  │
│  │  │  ─────────────────────────────────────────────────  │  │  │
│  │  │  风味结构：咸鲜为主，微酸，清爽口感                  │  │  │
│  │  │  预估成本：¥12.5                                    │  │  │
│  │  │  营养方向：高蛋白、低脂肪、低碳水                    │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      审批操作面板                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  审批意见：                                          │  │  │
│  │  │  ┌───────────────────────────────────────────────┐  │  │  │
│  │  │  │                                               │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  │                                                     │  │  │
│  │  │      [ 通过 ]            [ 驳回 ]                   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 前端组件设计

```typescript
// 主要组件结构
interface WorkflowPageProps {
  // 页面属性
}

// 需求输入组件
const RequirementInput: React.FC<{
  onSubmit: (input: string) => void;
  loading: boolean;
}> = ({ onSubmit, loading }) => {
  // 实现需求输入表单
};

// Agent状态面板组件
const AgentStatusPanel: React.FC<{
  agents: AgentStatus[];
  currentStep: string;
}> = ({ agents, currentStep }) => {
  // 展示各Agent状态，支持进度条和动画
};

// 概念卡展示组件
const ConceptCardDisplay: React.FC<{
  conceptCard: ConceptCard;
}> = ({ conceptCard }) => {
  // 展示概念卡详情
};

// 标准食谱卡展示组件
const RecipeCardDisplay: React.FC<{
  recipeCard: StandardRecipeCard;
}> = ({ recipeCard }) => {
  // 展示标准食谱卡，包含步骤、成本明细等
};

// 审批面板组件
const ApprovalPanel: React.FC<{
  onApprove: (comments: string) => void;
  onReject: (comments: string) => void;
}> = ({ onApprove, onReject }) => {
  // 审批操作界面
};

// WebSocket Hook
const useWorkflowWebSocket = (workflowId: string) => {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [conceptCard, setConceptCard] = useState<ConceptCard | null>(null);
  const [recipeCard, setRecipeCard] = useState<StandardRecipeCard | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://api.host.com/ws/workflows/${workflowId}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      switch (message.type) {
        case 'agent_status_change':
          // 更新Agent状态
          break;
        case 'step_completed':
          // 更新步骤输出
          break;
        case 'approval_required':
          // 显示审批面板
          break;
        case 'workflow_completed':
          // 工作流完成
          break;
      }
    };
    
    return () => ws.close();
  }, [workflowId]);
  
  return { agents, currentStep, conceptCard, recipeCard };
};
```

---

## 8. LLM集成设计

### 8.1 Prompt工程

```python
# Prompt模板管理
class PromptTemplate:
    """Prompt模板"""
    
    def __init__(self, template: str, variables: List[str]):
        self.template = template
        self.variables = variables
    
    def format(self, **kwargs) -> str:
        """格式化Prompt"""
        return self.template.format(**kwargs)


# 运营总监Prompt
OPERATIONS_DIRECTOR_PROMPT = PromptTemplate(
    template="""
    你是HOST轻食运营总监，负责接收客户需求并提取关键信息。
    
    客户需求：{customer_input}
    
    请分析以上需求，提取以下信息并以JSON格式输出：
    1. task_type: 任务类型 ("dish" 单品菜品 / "group_meal" 团餐方案)
    2. dish_requirements: 菜品要求 (口味、烹饪方式、食材禁忌等)
    3. nutrition_requirements: 营养要求 (热量、蛋白质、特殊饮食等)
    4. group_meal_info: 团餐信息 (人数、餐数、场景等，仅团餐任务)
    5. target_audience: 目标人群
    6. budget_range: 预算范围
    7. special_requirements: 特殊要求列表
    
    输出格式：
    ```json
    {{
        "task_type": "dish",
        "dish_requirements": {{
            "flavor": ["咸鲜", "微酸"],
            "cooking_method": "煎",
            "ingredient_restrictions": ["无麸质"]
        }},
        "nutrition_requirements": {{
            "calories_range": [300, 500],
            "protein_min": 30,
            "fat_max": 15,
            "special_diet": ["高蛋白", "低脂"]
        }},
        "target_audience": "健身人群",
        "budget_range": [10, 20],
        "special_requirements": ["适合减脂期"]
    }}
    ```
    """,
    variables=["customer_input"]
)


# 营养师Prompt
NUTRITIONIST_PROMPT = PromptTemplate(
    template="""
    你是HOST轻食专业营养师，负责设计营养配比方案。
    
    需求信息：{requirements}
    
    请设计营养配比方案，并以JSON格式输出：
    1. nutrition_plan: 营养方案 (热量、三大营养素、微量元素)
    2. ingredient_structures: 食材结构列表
    3. nutrition_notes: 营养说明
    4. warnings: 营养警告
    
    注意：
    - 食材用量精确到克
    - 营养数据精确到小数点后1位
    - 考虑食材的季节性和可获得性
    """,
    variables=["requirements"]
)
```

### 8.2 LLM调用封装

```python
import openai
from typing import Dict, Any, Optional
import json
import backoff


class LLMService:
    """LLM服务封装"""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.client = openai.AsyncOpenAI()
    
    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: str = "json",
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        调用LLM生成内容
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response_format: 响应格式 (json/text)
            temperature: 温度参数
        
        Returns:
            解析后的响应数据
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 如果要求JSON格式，添加JSON格式指令
        if response_format == "json":
            messages.append({
                "role": "assistant",
                "content": "请以JSON格式输出结果，确保JSON格式正确且完整。"
            })
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            response_format={"type": "json_object"} if response_format == "json" else None
        )
        
        content = response.choices[0].message.content
        
        if response_format == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尝试修复JSON
                return await self._fix_json(content, system_prompt)
        
        return {"content": content}
    
    async def _fix_json(self, broken_json: str, system_prompt: str) -> Dict:
        """尝试修复损坏的JSON"""
        fix_prompt = f"""
        以下JSON格式有误，请修复并返回正确的JSON：
        
        {broken_json}
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": fix_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

---

## 9. 部署架构

### 9.1 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - api

  # API服务
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/host_light_food
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=host_light_food
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis缓存/消息队列
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # 向量数据库（可选，用于食材/食谱检索）
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### 9.2 Kubernetes部署

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: host-api
  labels:
    app: host-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: host-api
  template:
    metadata:
      labels:
        app: host-api
    spec:
      containers:
      - name: api
        image: host-light-food/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secret
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: host-api-service
spec:
  selector:
    app: host-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 10. 监控与运维

### 10.1 监控指标

```python
# 监控指标定义
class Metrics:
    """系统监控指标"""
    
    # 工作流指标
    workflow_started_total = Counter('workflow_started_total', '启动的工作流总数')
    workflow_completed_total = Counter('workflow_completed_total', '完成的工作流总数', ['status'])
    workflow_duration_seconds = Histogram('workflow_duration_seconds', '工作流耗时')
    
    # Agent指标
    agent_processing_duration = Histogram('agent_processing_duration_seconds', 'Agent处理耗时', ['agent_role'])
    agent_errors_total = Counter('agent_errors_total', 'Agent错误数', ['agent_role', 'error_type'])
    
    # LLM指标
    llm_requests_total = Counter('llm_requests_total', 'LLM请求总数', ['model'])
    llm_tokens_consumed = Counter('llm_tokens_consumed_total', 'LLM消耗token数', ['model'])
    llm_latency_seconds = Histogram('llm_latency_seconds', 'LLM响应延迟')
    
    # API指标
    http_requests_total = Counter('http_requests_total', 'HTTP请求总数', ['method', 'endpoint', 'status'])
    http_request_duration = Histogram('http_request_duration_seconds', 'HTTP请求耗时', ['method', 'endpoint'])
    
    # WebSocket指标
    websocket_connections = Gauge('websocket_connections', 'WebSocket连接数')
    websocket_messages_total = Counter('websocket_messages_total', 'WebSocket消息数', ['type'])
```

### 10.2 日志规范

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_workflow_event(self, workflow_id: str, event: str, **kwargs):
        """记录工作流事件"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "event": event,
            **kwargs
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_agent_event(self, workflow_id: str, agent_role: str, event: str, **kwargs):
        """记录Agent事件"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "agent_role": agent_role,
            "event": event,
            **kwargs
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_error(self, workflow_id: str, error: Exception, **kwargs):
        """记录错误"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        self.logger.error(json.dumps(log_data, ensure_ascii=False))
```

---

## 11. 安全设计

### 11.1 安全措施

| 安全层面 | 措施 | 说明 |
|----------|------|------|
| API安全 | JWT认证 | 所有API需要有效Token |
| 输入验证 | Pydantic模型 | 严格验证所有输入数据 |
| 输出过滤 | 内容过滤 | 过滤LLM输出中的敏感信息 |
| 数据加密 | TLS/SSL | 所有通信加密 |
| 密钥管理 | Vault/Secret | 集中管理API密钥 |
| 访问控制 | RBAC | 基于角色的访问控制 |
| 审计日志 | 全量记录 | 所有操作可追溯 |

### 11.2 限流策略

```python
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
from collections import defaultdict


class RateLimiter:
    """限流器"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    async def check(self, client_id: str):
        """检查是否超过限流"""
        now = time.time()
        minute_ago = now - 60
        
        # 清理过期请求记录
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        self.requests[client_id].append(now)


# 全局限流器实例
rate_limiter = RateLimiter(requests_per_minute=30)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    client_id = request.client.host
    await rate_limiter.check(client_id)
    response = await call_next(request)
    return response
```

---

## 12. 项目规划

### 12.1 开发阶段

| 阶段 | 时间 | 交付物 | 里程碑 |
|------|------|--------|--------|
| **第一阶段：基础框架** | 2周 | 项目脚手架、基础架构、数据库设计 | 环境搭建完成 |
| **第二阶段：核心Agent** | 3周 | 四个Agent实现、LLM集成、基础工作流 | Agent可独立运行 |
| **第三阶段：工作流引擎** | 2周 | 工作流编排、状态管理、WebSocket通信 | 端到端流程跑通 |
| **第四阶段：前端开发** | 3周 | 前端界面、实时展示、审批交互 | 前端可用 |
| **第五阶段：集成测试** | 2周 | 集成测试、性能优化、Bug修复 | 系统稳定 |
| **第六阶段：部署上线** | 1周 | 生产部署、监控配置、文档完善 | 正式上线 |

### 12.2 团队配置

| 角色 | 人数 | 职责 |
|------|------|------|
| 项目经理 | 1 | 项目协调、进度把控 |
| 后端开发 | 2 | API、工作流引擎、Agent开发 |
| 前端开发 | 1 | 前端界面、交互设计 |
| AI工程师 | 1 | LLM集成、Prompt工程 |
| 测试工程师 | 1 | 测试用例、质量保证 |

---

## 13. 风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| LLM响应不稳定 | 输出格式错误、内容质量波动 | 中 | 增加重试机制、输出校验、人工兜底 |
| 工作流复杂度高 | 状态管理困难、调试复杂 | 中 | 状态机设计、完善日志、可视化调试工具 |
| 实时通信延迟 | 前端状态不同步 | 低 | WebSocket心跳、断线重连、状态补偿机制 |
| 数据安全风险 | 敏感信息泄露 | 低 | 加密存储、访问控制、审计日志 |
| 性能瓶颈 | 并发工作流响应慢 | 中 | 异步处理、水平扩展、缓存优化 |

---

## 14. 附录

### 14.1 术语表

| 术语 | 说明 |
|------|------|
| Agent | 具有特定角色和能力的AI实体 |
| 工作流 | 多Agent协同完成的有序任务序列 |
| 概念卡 | 研发主厨输出的菜品设计方案 |
| 食谱卡 | 厨师长输出的标准化食谱 |
| 审批 | 人工审核食谱卡并决定通过或驳回 |

### 14.2 参考文档

- [OpenAI API文档](https://platform.openai.com/docs)
- [LangChain文档](https://python.langchain.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)

---

**文档版本**: v1.0  
**创建日期**: 2024-01-15  
**维护者**: 技术团队
