import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import structlog

from models.workflow import Workflow, WorkflowStep, WorkflowStatus
from models.agent import AgentRole, AgentStatus
from models.concept_card import ConceptCard
from models.recipe_card import RecipeCard
from models.approval import Approval
from core.database import AsyncSessionLocal
from core.config import settings
from agents import (
    OperationsDirectorAgent,
    NutritionistAgent,
    RDChefAgent,
    HeadChefAgent,
    AgentResult,
    AgentResultStatus
)
from services.llm_service import get_llm_service, LLMAPIError
from services.websocket_manager import ws_manager

logger = structlog.get_logger()


@dataclass
class WorkflowContext:
    """工作流上下文（内存中）"""
    workflow_id: str
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
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # 错误信息
    error_message: Optional[str] = None
    
    # 当前步骤ID
    current_step_id: Optional[str] = None
    
    # Agent实例（支持按模型隔离）
    agents: Optional[Dict] = field(default_factory=dict)


class WorkflowEngine:
    """
    工作流引擎
    负责编排各Agent协同工作，管理状态流转
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.llm_service = get_llm_service()
        
        # 初始化Agent
        self.agents = {
            AgentRole.OPERATIONS_DIRECTOR: OperationsDirectorAgent(self.llm_service),
            AgentRole.NUTRITIONIST: NutritionistAgent(self.llm_service),
            AgentRole.RD_CHEF: RDChefAgent(self.llm_service),
            AgentRole.HEAD_CHEF: HeadChefAgent(self.llm_service),
        }
    
    async def create_workflow(self, customer_input: str, model: Optional[str] = None) -> str:
        """
        创建新的菜品研发工作流
        
        Args:
            customer_input: 客户输入
            model: 指定LLM模型名称（可选）
            
        Returns:
            workflow_id: 工作流ID
        """
        workflow_id = str(uuid.uuid4())
        
        # 创建指定模型的LLM服务
        llm_service = get_llm_service(model=model) if model else self.llm_service
        
        # 初始化Agent（使用指定模型的LLM服务）
        agents = {
            AgentRole.OPERATIONS_DIRECTOR: OperationsDirectorAgent(llm_service),
            AgentRole.NUTRITIONIST: NutritionistAgent(llm_service),
            AgentRole.RD_CHEF: RDChefAgent(llm_service),
            AgentRole.HEAD_CHEF: HeadChefAgent(llm_service),
        }
        
        # 创建内存上下文
        context = WorkflowContext(
            workflow_id=workflow_id,
            customer_input=customer_input,
            max_revisions=settings.MAX_REVISION_COUNT,
            agents=agents
        )
        self.active_workflows[workflow_id] = context
        
        # 创建数据库记录
        async with AsyncSessionLocal() as session:
            workflow = Workflow(
                id=workflow_id,
                customer_input=customer_input,
                status=WorkflowStatus.CREATED.value,
                max_revisions=settings.MAX_REVISION_COUNT
            )
            session.add(workflow)
            await session.commit()
        
        # 启动工作流（异步）
        asyncio.create_task(self._run_workflow(workflow_id))
        
        return workflow_id
    
    async def _run_workflow(self, workflow_id: str):
        """运行工作流主流程"""
        context = self.active_workflows[workflow_id]
        
        try:
            # Step 1: 运营总监提取需求
            await self._update_status(workflow_id, WorkflowStatus.EXTRACTING)
            director_result = await self._run_agent(
                workflow_id,
                AgentRole.OPERATIONS_DIRECTOR,
                {"customer_input": context.customer_input}
            )
            
            if director_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"运营总监处理失败: {director_result.error_message}")
            
            context.director_output = director_result.data
            await self._save_agent_output(workflow_id, "operations_director", director_result.data)
            await self._broadcast_step_completed(workflow_id, "operations_director", director_result.data)
            
            # Step 2: 营养师设计营养方案
            await self._update_status(workflow_id, WorkflowStatus.NUTRITION_DESIGNING)
            nutritionist_result = await self._run_agent(
                workflow_id,
                AgentRole.NUTRITIONIST,
                {"director_output": context.director_output}
            )
            
            if nutritionist_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"营养师处理失败: {nutritionist_result.error_message}")
            
            context.nutritionist_output = nutritionist_result.data
            await self._save_agent_output(workflow_id, "nutritionist", nutritionist_result.data)
            await self._broadcast_step_completed(workflow_id, "nutritionist", nutritionist_result.data)
            
            # Step 3: 研发主厨设计概念卡
            await self._update_status(workflow_id, WorkflowStatus.CONCEPT_DESIGNING)
            rd_result = await self._run_agent(
                workflow_id,
                AgentRole.RD_CHEF,
                {
                    "nutritionist_output": context.nutritionist_output,
                    "director_output": context.director_output
                }
            )
            
            if rd_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"研发主厨处理失败: {rd_result.error_message}")
            
            context.rd_chef_output = rd_result.data
            await self._save_agent_output(workflow_id, "rd_chef", rd_result.data)
            await self._broadcast_step_completed(workflow_id, "rd_chef", rd_result.data)
            
            # 保存概念卡到数据库
            await self._save_concept_card(workflow_id, rd_result.data.get("concept_card", {}))
            
            # Step 4: 厨师长审评并生成标准食谱
            await self._update_status(workflow_id, WorkflowStatus.RECIPE_REVIEWING)
            head_chef_result = await self._run_agent(
                workflow_id,
                AgentRole.HEAD_CHEF,
                {
                    "rd_chef_output": context.rd_chef_output,
                    "nutritionist_output": context.nutritionist_output,
                    "director_output": context.director_output
                }
            )
            
            if head_chef_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"厨师长处理失败: {head_chef_result.error_message}")
            
            context.head_chef_output = head_chef_result.data
            await self._save_agent_output(workflow_id, "head_chef", head_chef_result.data)
            await self._broadcast_step_completed(workflow_id, "head_chef", head_chef_result.data)
            
            # 保存食谱卡到数据库
            await self._save_recipe_card(workflow_id, head_chef_result.data.get("recipe_card", {}))
            
            # 等待审批
            await self._update_status(workflow_id, WorkflowStatus.WAITING_APPROVAL)
            await ws_manager.broadcast_approval_required(
                workflow_id,
                head_chef_result.data.get("recipe_card", {})
            )
            
        except LLMAPIError as e:
            context.error_message = str(e)
            logger.error(
                "工作流 LLM 错误",
                workflow_id=workflow_id,
                error_code=e.error_code,
                error_message=e.message
            )
            await self._update_status(workflow_id, WorkflowStatus.FAILED)
            await ws_manager.broadcast_error(
                workflow_id,
                e.error_code,
                e.message
            )
        except Exception as e:
            context.error_message = str(e)
            logger.error(
                "工作流执行异常",
                workflow_id=workflow_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            await self._update_status(workflow_id, WorkflowStatus.FAILED)
            await ws_manager.broadcast_error(
                workflow_id,
                "WORKFLOW_ERROR",
                str(e)
            )
        finally:
            # 确保工作流状态及时更新到数据库
            await self._update_status(workflow_id, context.status)
    
    async def approve_workflow(
        self,
        workflow_id: str,
        approved: bool,
        comments: str,
        reviewer: str
    ):
        """
        审批工作流
        
        Args:
            workflow_id: 工作流ID
            approved: 是否通过
            comments: 审批意见
            reviewer: 审批人
        """
        context = self.active_workflows.get(workflow_id)
        if not context:
            raise ValueError("工作流不存在")
        
        # 保存审批记录
        await self._save_approval(workflow_id, approved, comments, reviewer)
        
        if approved:
            context.approval_status = "approved"
            context.approval_comments = comments
            context.approved_by = reviewer
            await self._update_status(workflow_id, WorkflowStatus.APPROVED)
            await self._update_status(workflow_id, WorkflowStatus.COMPLETED)
            await ws_manager.broadcast_workflow_completed(
                workflow_id,
                "approved",
                context.head_chef_output.get("recipe_card") if context.head_chef_output else None
            )
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
                await ws_manager.broadcast_error(
                    workflow_id,
                    "MAX_REVISIONS_EXCEEDED",
                    "已达到最大修订次数"
                )
    
    async def _revise_concept(self, workflow_id: str, feedback: str):
        """重新设计概念卡"""
        context = self.active_workflows[workflow_id]
        
        try:
            # 更新状态
            await self._update_status(workflow_id, WorkflowStatus.CONCEPT_DESIGNING)
            
            # 添加反馈到输入
            revise_input = {
                "nutritionist_output": context.nutritionist_output,
                "director_output": context.director_output,
                "previous_concept": context.rd_chef_output,
                "revision_feedback": feedback,
                "revision_count": context.revision_count
            }
            
            # 重新运行研发主厨
            rd_result = await self._run_agent(
                workflow_id,
                AgentRole.RD_CHEF,
                revise_input
            )
            
            if rd_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"研发主厨修改失败: {rd_result.error_message}")
            
            context.rd_chef_output = rd_result.data
            await self._save_agent_output(workflow_id, "rd_chef", rd_result.data)
            await self._broadcast_step_completed(workflow_id, "rd_chef", rd_result.data)
            
            # 更新概念卡
            await self._save_concept_card(workflow_id, rd_result.data.get("concept_card", {}))
            
            # 重新运行厨师长
            await self._update_status(workflow_id, WorkflowStatus.RECIPE_REVIEWING)
            head_chef_result = await self._run_agent(
                workflow_id,
                AgentRole.HEAD_CHEF,
                {
                    "rd_chef_output": context.rd_chef_output,
                    "nutritionist_output": context.nutritionist_output,
                    "director_output": context.director_output,
                    "revision_feedback": feedback
                }
            )
            
            if head_chef_result.status != AgentResultStatus.SUCCESS:
                raise Exception(f"厨师长处理失败: {head_chef_result.error_message}")
            
            context.head_chef_output = head_chef_result.data
            await self._save_agent_output(workflow_id, "head_chef", head_chef_result.data)
            await self._broadcast_step_completed(workflow_id, "head_chef", head_chef_result.data)
            
            # 更新食谱卡
            await self._save_recipe_card(workflow_id, head_chef_result.data.get("recipe_card", {}))
            
            # 再次等待审批
            await self._update_status(workflow_id, WorkflowStatus.WAITING_APPROVAL)
            await ws_manager.broadcast_approval_required(
                workflow_id,
                head_chef_result.data.get("recipe_card", {})
            )
            
        except LLMAPIError as e:
            context.error_message = str(e)
            await self._update_status(workflow_id, WorkflowStatus.FAILED)
            await ws_manager.broadcast_error(
                workflow_id,
                e.error_code,
                e.message
            )
        except Exception as e:
            context.error_message = str(e)
            await self._update_status(workflow_id, WorkflowStatus.FAILED)
            await ws_manager.broadcast_error(
                workflow_id,
                "REVISION_ERROR",
                str(e)
            )
    
    async def _run_agent(
        self,
        workflow_id: str,
        agent_role: AgentRole,
        input_data: Dict[str, Any]
    ) -> AgentResult:
        """
        运行指定Agent
        
        Args:
            workflow_id: 工作流ID
            agent_role: Agent角色
            input_data: 输入数据
            
        Returns:
            AgentResult: 执行结果
        """
        context = self.active_workflows[workflow_id]
        agent = context.agents[agent_role]
        
        # 创建步骤记录
        step_id = await self._create_step(workflow_id, agent_role)
        context.current_step_id = step_id
        
        # 广播状态变更
        await ws_manager.broadcast_agent_status(
            workflow_id,
            agent_role.value,
            agent.name,
            AgentStatus.IDLE.value,
            AgentStatus.PROCESSING.value,
            current_task=f"正在处理..."
        )
        
        # 执行Agent
        try:
            result = await agent.execute(input_data)
        except Exception as e:
            # Agent执行失败，立即广播错误
            error_msg = str(e)
            error_code = 'AGENT_ERROR'
            if isinstance(e, LLMAPIError):
                error_code = e.error_code
                error_msg = e.message
            
            # 更新步骤状态为失败
            await self._complete_step(step_id, AgentResult(
                status=AgentResultStatus.FAILURE,
                error_message=error_msg,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            ))
            
            # 广播Agent失败状态
            await ws_manager.broadcast_agent_status(
                workflow_id,
                agent_role.value,
                agent.name,
                AgentStatus.PROCESSING.value,
                AgentStatus.FAILED.value,
                current_task=error_msg
            )
            
            # 广播错误消息
            await ws_manager.broadcast_error(
                workflow_id,
                error_code,
                f"{agent.name}执行失败: {error_msg}"
            )
            
            # 重新抛出异常，让工作流引擎处理
            raise
        
        # 更新步骤状态
        await self._complete_step(step_id, result)
        
        # 广播状态变更
        new_status = AgentStatus.COMPLETED if result.status == AgentResultStatus.SUCCESS else AgentStatus.FAILED
        await ws_manager.broadcast_agent_status(
            workflow_id,
            agent_role.value,
            agent.name,
            AgentStatus.PROCESSING.value,
            new_status.value
        )
        
        return result
    
    async def _update_status(self, workflow_id: str, new_status: WorkflowStatus):
        """更新工作流状态"""
        context = self.active_workflows[workflow_id]
        old_status = context.status
        context.status = new_status
        context.updated_at = datetime.utcnow()
        
        # 更新数据库
        async with AsyncSessionLocal() as session:
            workflow = await session.get(Workflow, workflow_id)
            if workflow:
                workflow.status = new_status.value
                workflow.updated_at = datetime.utcnow()
                if context.error_message:
                    workflow.error_message = context.error_message
                if new_status == WorkflowStatus.COMPLETED:
                    workflow.completed_at = datetime.utcnow()
                await session.commit()
    
    async def _create_step(self, workflow_id: str, agent_role: AgentRole) -> str:
        """创建步骤记录"""
        step_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            # 获取当前步骤数
            from sqlalchemy import select, func
            result = await session.execute(
                select(func.count(WorkflowStep.id)).where(
                    WorkflowStep.workflow_id == workflow_id
                )
            )
            step_count = result.scalar() or 0
            
            step = WorkflowStep(
                id=step_id,
                workflow_id=workflow_id,
                agent_role=agent_role.value,
                step_order=step_count + 1,
                status="processing",
                started_at=datetime.utcnow()
            )
            session.add(step)
            await session.commit()
        
        return step_id
    
    async def _complete_step(self, step_id: str, result: AgentResult):
        """完成步骤记录"""
        async with AsyncSessionLocal() as session:
            step = await session.get(WorkflowStep, step_id)
            if step:
                step.status = "completed" if result.status == AgentResultStatus.SUCCESS else "failed"
                step.output_data = result.data
                step.error_message = result.error_message
                step.completed_at = datetime.utcnow()
                await session.commit()
    
    async def _save_agent_output(self, workflow_id: str, agent_role: str, output: Dict):
        """保存Agent输出到工作流记录"""
        async with AsyncSessionLocal() as session:
            workflow = await session.get(Workflow, workflow_id)
            if workflow:
                if agent_role == "operations_director":
                    workflow.director_output = output
                elif agent_role == "nutritionist":
                    workflow.nutritionist_output = output
                elif agent_role == "rd_chef":
                    workflow.rd_chef_output = output
                elif agent_role == "head_chef":
                    workflow.head_chef_output = output
                await session.commit()
    
    async def _save_concept_card(self, workflow_id: str, concept_data: Dict):
        """保存概念卡"""
        async with AsyncSessionLocal() as session:
            card = ConceptCard(
                workflow_id=workflow_id,
                dish_name=concept_data.get("dish_name", "未命名"),
                food_combination=concept_data.get("food_combination", []),
                flavor_structure=concept_data.get("flavor_structure", {}),
                plating_direction=concept_data.get("plating_direction", ""),
                estimated_cost=concept_data.get("estimated_cost", 0),
                nutrition_direction=concept_data.get("nutrition_direction", ""),
                cooking_method=concept_data.get("cooking_method", ""),
                innovation_points=concept_data.get("innovation_points", []),
            )
            session.add(card)
            await session.commit()
    
    async def _save_recipe_card(self, workflow_id: str, recipe_data: Dict):
        """保存标准食谱卡"""
        async with AsyncSessionLocal() as session:
            card = RecipeCard(
                workflow_id=workflow_id,
                dish_name=recipe_data.get("dish_name", "未命名"),
                ingredients=recipe_data.get("ingredients", []),
                seasonings=recipe_data.get("seasonings", []),
                equipment=recipe_data.get("equipment", []),
                steps=recipe_data.get("steps", []),
                quality_standards=recipe_data.get("quality_standards", []),
                plating_specification=recipe_data.get("plating_specification", ""),
                shelf_life=recipe_data.get("shelf_life", ""),
                cost_breakdown=recipe_data.get("cost_breakdown", {}),
                nutrition_facts=recipe_data.get("nutrition_facts", {}),
            )
            session.add(card)
            await session.commit()
    
    async def _save_approval(
        self,
        workflow_id: str,
        approved: bool,
        comments: str,
        reviewer: str
    ):
        """保存审批记录"""
        async with AsyncSessionLocal() as session:
            approval = Approval(
                workflow_id=workflow_id,
                step_id=self.active_workflows[workflow_id].current_step_id,
                status="approved" if approved else "rejected",
                comments=comments,
                reviewer=reviewer,
                reviewed_at=datetime.utcnow()
            )
            session.add(approval)
            
            # 更新食谱卡审批状态
            if approved:
                from sqlalchemy import select
                result = await session.execute(
                    select(RecipeCard).where(
                        RecipeCard.workflow_id == workflow_id
                    ).order_by(RecipeCard.created_at.desc())
                )
                latest_card = result.scalars().first()
                if latest_card:
                    latest_card.review_status = "approved"
                    latest_card.reviewed_by = reviewer
                    latest_card.review_comments = comments
            
            await session.commit()
    
    async def _broadcast_step_completed(self, workflow_id: str, agent_role: str, output: Dict):
        """广播步骤完成"""
        await ws_manager.broadcast_step_completed(workflow_id, agent_role, output)
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowContext]:
        """获取工作流上下文"""
        return self.active_workflows.get(workflow_id)
    
    def get_agent_statuses(self, workflow_id: str) -> List[Dict]:
        """获取所有Agent状态"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def get_active_workflows(self) -> List[str]:
        """获取所有活跃工作流ID"""
        return list(self.active_workflows.keys())


# 全局工作流引擎实例
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎单例"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine