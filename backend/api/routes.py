from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import secrets

from core.database import get_db
from core.config import settings
from models.workflow import Workflow, WorkflowStep, WorkflowStatus
from models.agent import Agent, AgentRole, AgentStatus
from models.concept_card import ConceptCard
from models.recipe_card import RecipeCard
from models.approval import Approval
from services.workflow_engine import get_workflow_engine, WorkflowEngine
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/api/v1", tags=["HOST轻食多Agent框架"])


# ==================== 认证相关 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    password: str = Field(..., description="登录密码")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    username: str


# 简单的 token 存储（生产环境应使用 Redis 或数据库）
_active_tokens: Dict[str, str] = {}


def _hash_password(password: str) -> str:
    """对密码进行哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


# 默认密码: admin123
DEFAULT_PASSWORD_HASH = _hash_password("admin123")


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    使用预设密码登录管理后台
    """
    if _hash_password(request.password) != DEFAULT_PASSWORD_HASH:
        raise HTTPException(status_code=401, detail="密码错误")
    
    # 生成 token
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = "admin"
    
    return LoginResponse(token=token, username="admin")


@router.get("/auth/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """
    验证 token 是否有效
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    # 支持 "Bearer <token>" 格式
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    if token not in _active_tokens:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    
    return {"valid": True, "username": _active_tokens[token]}


@router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    用户登出
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        _active_tokens.pop(token, None)
    
    return {"message": "已登出"}


# ==================== 请求/响应模型 ====================

class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""
    customer_input: str = Field(..., description="客户输入", min_length=1)
    model: Optional[str] = Field(None, description="指定LLM模型名称")
    metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")


class ApprovalRequest(BaseModel):
    """审批请求"""
    approved: bool = Field(..., description="是否通过")
    comments: str = Field(..., description="审批意见", min_length=1)
    reviewer: str = Field(..., description="审批人")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    status: str
    customer_input: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    role: str
    name: str
    status: str
    current_task: Optional[str] = None


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
    
    class Config:
        from_attributes = True


class RecipeCardResponse(BaseModel):
    """标准食谱卡响应"""
    dish_name: str
    ingredients: List[Dict]
    seasonings: List[Dict]
    equipment: List[str]
    steps: List[Dict]
    quality_standards: List[str]
    cost_breakdown: Dict
    nutrition_facts: Dict
    version: str
    review_status: str
    
    class Config:
        from_attributes = True


class WorkflowDetailResponse(BaseModel):
    """工作流详情响应"""
    workflow_id: str
    status: str
    customer_input: str
    revision_count: int
    director_output: Optional[Dict] = None
    nutritionist_output: Optional[Dict] = None
    rd_chef_output: Optional[Dict] = None
    head_chef_output: Optional[Dict] = None
    approval_status: Optional[str] = None
    approval_comments: Optional[str] = None
    approved_by: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


# ==================== API端点 ====================

@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    request: CreateWorkflowRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """
    创建新的菜品研发工作流
    
    接收客户输入，启动多Agent协同工作流程
    """
    workflow_id = await engine.create_workflow(
        customer_input=request.customer_input,
        model=request.model
    )
    context = engine.get_workflow(workflow_id)
    
    return WorkflowResponse(
        workflow_id=context.workflow_id,
        status=context.status.value,
        customer_input=context.customer_input,
        created_at=context.created_at.isoformat(),
        updated_at=context.updated_at.isoformat()
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow(
    workflow_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """获取工作流详情"""
    # 先从内存获取
    context = engine.get_workflow(workflow_id)
    
    if context:
        return WorkflowDetailResponse(
            workflow_id=context.workflow_id,
            status=context.status.value,
            customer_input=context.customer_input,
            revision_count=context.revision_count,
            director_output=context.director_output,
            nutritionist_output=context.nutritionist_output,
            rd_chef_output=context.rd_chef_output,
            head_chef_output=context.head_chef_output,
            approval_status=context.approval_status,
            approval_comments=context.approval_comments,
            approved_by=context.approved_by,
            error_message=context.error_message,
            created_at=context.created_at.isoformat(),
            updated_at=context.updated_at.isoformat(),
        )
    
    # 从数据库获取
    async with AsyncSessionLocal() as session:
        workflow = await session.get(Workflow, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        return WorkflowDetailResponse(
            workflow_id=str(workflow.id),
            status=workflow.status,
            customer_input=workflow.customer_input,
            revision_count=workflow.revision_count,
            director_output=workflow.director_output,
            nutritionist_output=workflow.nutritionist_output,
            rd_chef_output=workflow.rd_chef_output,
            head_chef_output=workflow.head_chef_output,
            error_message=workflow.error_message,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat(),
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        )


@router.get("/workflows/{workflow_id}/agents", response_model=List[AgentStatusResponse])
async def get_agent_statuses(
    workflow_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """获取所有Agent状态"""
    return engine.get_agent_statuses(workflow_id)


@router.get("/workflows/{workflow_id}/concept-card")
async def get_concept_card(
    workflow_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """获取概念卡"""
    context = engine.get_workflow(workflow_id)
    if not context or not context.rd_chef_output:
        raise HTTPException(status_code=404, detail="概念卡不存在")
    
    concept_card = context.rd_chef_output.get("concept_card", {})
    return concept_card


@router.get("/workflows/{workflow_id}/recipe-card")
async def get_recipe_card(
    workflow_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """获取标准食谱卡"""
    context = engine.get_workflow(workflow_id)
    if not context or not context.head_chef_output:
        raise HTTPException(status_code=404, detail="食谱卡不存在")
    
    recipe_card = context.head_chef_output.get("recipe_card", {})
    return recipe_card


@router.post("/workflows/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: str,
    request: ApprovalRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """
    审批工作流
    
    - approved=true: 通过，流程完成
    - approved=false: 驳回，打回研发主厨重新设计
    """
    try:
        await engine.approve_workflow(
            workflow_id=workflow_id,
            approved=request.approved,
            comments=request.comments,
            reviewer=request.reviewer
        )
        return {
            "message": "审批已提交",
            "workflow_id": workflow_id,
            "approved": request.approved
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取工作流历史记录（步骤和审批）"""
    # 获取步骤历史
    steps_result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.workflow_id == workflow_id
        ).order_by(WorkflowStep.step_order)
    )
    steps = steps_result.scalars().all()
    
    # 获取审批历史
    approvals_result = await db.execute(
        select(Approval).where(
            Approval.workflow_id == workflow_id
        ).order_by(Approval.reviewed_at)
    )
    approvals = approvals_result.scalars().all()
    
    return {
        "steps": [
            {
                "id": str(step.id),
                "agent_role": step.agent_role,
                "step_order": step.step_order,
                "status": step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "error_message": step.error_message,
            }
            for step in steps
        ],
        "approvals": [
            {
                "id": str(approval.id),
                "status": approval.status,
                "comments": approval.comments,
                "reviewer": approval.reviewer,
                "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
            }
            for approval in approvals
        ]
    }


@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取工作流列表"""
    query = select(Workflow).order_by(Workflow.created_at.desc())
    
    if status:
        query = query.where(Workflow.status == status)
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return {
        "total": len(workflows),
        "limit": limit,
        "offset": offset,
        "workflows": [
            {
                "workflow_id": str(w.id),
                "status": w.status,
                "customer_input": w.customer_input[:100] + "..." if len(w.customer_input) > 100 else w.customer_input,
                "revision_count": w.revision_count,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            }
            for w in workflows
        ]
    }


# ==================== 模型管理 ====================

class ModelInfo(BaseModel):
    """模型信息"""
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="模型提供商")
    available: bool = Field(..., description="是否可用（API Key 是否已配置）")


@router.get("/models", response_model=List[ModelInfo])
async def list_available_models():
    """
    获取当前可用的 LLM 模型列表
    
    根据后端配置中已配置的 API Key，返回可用的模型列表
    """
    from services.llm_service import MODEL_ROUTERS
    from core.config import settings
    
    models = []
    
    for model_name, config in MODEL_ROUTERS.items():
        # 检查该模型是否已配置 API Key
        api_key = config.get("api_key", "")
        available = bool(api_key)
        
        # 根据模型名称判断提供商
        if "longcat" in model_name.lower():
            provider = "LongCat"
        elif "glm" in model_name.lower():
            provider = "智谱 GLM"
        else:
            provider = config.get("provider", "unknown")
        
        models.append(ModelInfo(
            name=model_name,
            provider=provider,
            available=available
        ))
    
    return models


# ==================== WebSocket端点 ====================

@router.websocket("/ws/workflows/{workflow_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    workflow_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket实时推送工作流状态
    
    推送内容：
    - Agent状态变更
    - 步骤完成通知
    - 审批请求
    - 错误通知
    """
    await ws_manager.connect(websocket, workflow_id)
    
    try:
        # 发送当前工作流状态
        engine = get_workflow_engine()
        context = engine.get_workflow(workflow_id)
        
        if context:
            await ws_manager.send_personal_message(
                websocket,
                {
                    "type": "workflow_status",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "status": context.status.value,
                        "revision_count": context.revision_count,
                    }
                }
            )
        
        # 保持连接并处理客户端消息
        while True:
            try:
                data = await websocket.receive_text()
                # 可以处理客户端发送的消息（如心跳）
                import json
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await ws_manager.send_personal_message(
                        websocket,
                        {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, workflow_id)
    except Exception:
        ws_manager.disconnect(websocket, workflow_id)


# 导入AsyncSessionLocal
from core.database import AsyncSessionLocal