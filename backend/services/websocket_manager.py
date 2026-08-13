import json
from typing import Dict, List, Optional
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """
    WebSocket连接管理器
    管理客户端连接，支持按工作流ID分组广播
    """
    
    def __init__(self):
        # workflow_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # 全局连接列表（用于系统级广播）
        self.global_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, workflow_id: str):
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            workflow_id: 关联的工作流ID
        """
        await websocket.accept()
        
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
        
        # 发送连接成功消息
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "连接成功"
            }
        )
    
    def disconnect(self, websocket: WebSocket, workflow_id: str):
        """
        断开WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            workflow_id: 关联的工作流ID
        """
        if workflow_id in self.active_connections:
            if websocket in self.active_connections[workflow_id]:
                self.active_connections[workflow_id].remove(websocket)
            
            # 如果该工作流没有连接了，清理
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict):
        """
        发送个人消息
        
        Args:
            websocket: WebSocket连接对象
            message: 消息内容
        """
        try:
            await websocket.send_json(message)
        except Exception:
            # 连接可能已关闭，忽略错误
            pass
    
    async def broadcast_to_workflow(self, workflow_id: str, message: Dict):
        """
        向特定工作流的所有连接广播消息
        
        Args:
            workflow_id: 工作流ID
            message: 消息内容
        """
        if workflow_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.disconnect(conn, workflow_id)
    
    async def broadcast_agent_status(
        self,
        workflow_id: str,
        agent_role: str,
        agent_name: str,
        old_status: str,
        new_status: str,
        current_task: Optional[str] = None
    ):
        """
        广播Agent状态变更
        
        Args:
            workflow_id: 工作流ID
            agent_role: Agent角色
            agent_name: Agent名称
            old_status: 旧状态
            new_status: 新状态
            current_task: 当前任务描述（失败时可包含错误信息）
        """
        message = {
            "type": "agent_status_change",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "agent_role": agent_role,
                "agent_name": agent_name,
                "old_status": old_status,
                "new_status": new_status,
                "current_task": current_task
            }
        }
        await self.broadcast_to_workflow(workflow_id, message)
    
    async def broadcast_step_completed(
        self,
        workflow_id: str,
        agent_role: str,
        output: Dict
    ):
        """
        广播步骤完成消息
        
        Args:
            workflow_id: 工作流ID
            agent_role: Agent角色
            output: 步骤输出数据
        """
        message = {
            "type": "step_completed",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "agent_role": agent_role,
                "output": output
            }
        }
        await self.broadcast_to_workflow(workflow_id, message)
    
    async def broadcast_approval_required(
        self,
        workflow_id: str,
        recipe_card: Dict
    ):
        """
        广播审批请求消息
        
        Args:
            workflow_id: 工作流ID
            recipe_card: 标准食谱卡数据
        """
        message = {
            "type": "approval_required",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "recipe_card": recipe_card,
                "message": "请审评标准食谱卡"
            }
        }
        await self.broadcast_to_workflow(workflow_id, message)
    
    async def broadcast_workflow_completed(
        self,
        workflow_id: str,
        status: str,
        recipe_card: Optional[Dict] = None
    ):
        """
        广播工作流完成消息
        
        Args:
            workflow_id: 工作流ID
            status: 完成状态 (approved/rejected)
            recipe_card: 最终食谱卡
        """
        message = {
            "type": "workflow_completed",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": status,
                "recipe_card": recipe_card
            }
        }
        await self.broadcast_to_workflow(workflow_id, message)
    
    async def broadcast_error(
        self,
        workflow_id: str,
        error_code: str,
        error_message: str
    ):
        """
        广播错误消息
        
        Args:
            workflow_id: 工作流ID
            error_code: 错误代码
            error_message: 错误信息
        """
        message = {
            "type": "error",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "error_code": error_code,
                "message": error_message
            }
        }
        await self.broadcast_to_workflow(workflow_id, message)
    
    def get_connection_count(self, workflow_id: str) -> int:
        """获取工作流的连接数"""
        return len(self.active_connections.get(workflow_id, []))
    
    def get_total_connections(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())


# 全局WebSocket管理器实例
ws_manager = ConnectionManager()