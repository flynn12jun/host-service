import { create } from 'zustand'
import { Modal } from 'antd'
import type {
  WorkflowContext,
  AgentStatusInfo,
  ConceptCard,
  StandardRecipeCard,
  WSMessage,
  AvailableModel,
} from '../types'
import { workflowApi, modelsApi } from '../services/api'
import { wsService } from '../services/websocket'

const ERROR_MESSAGES: Record<string, { title: string; content: string }> = {
  API_KEY_INVALID: {
    title: 'API Key 无效',
    content: '当前模型的 API Key 无效或已过期，请检查 .env 配置或更换模型。',
  },
  FORBIDDEN: {
    title: '无权限访问',
    content: '当前 API Key 无权限访问所选模型，请检查权限配置。',
  },
  RATE_LIMIT: {
    title: '额度已用完',
    content: 'API 调用频率超限或额度已用完，请稍后重试或更换 API Key/模型。',
  },
  SERVER_ERROR: {
    title: 'LLM 服务错误',
    content: 'LLM 服务内部错误，请稍后重试。',
  },
  BAD_GATEWAY: {
    title: '服务不可用',
    content: 'LLM 服务暂时不可用，请稍后重试。',
  },
  SERVICE_UNAVAILABLE: {
    title: '服务过载',
    content: 'LLM 服务过载或维护中，请稍后重试。',
  },
  MODEL_NOT_FOUND: {
    title: '模型不存在',
    content: '请求的模型不存在或不可用，请选择其他模型。',
  },
  LLM_ERROR: {
    title: 'LLM 调用失败',
    content: '调用 LLM 时发生未知错误，请检查配置或稍后重试。',
  },
  NETWORK_ERROR: {
    title: '网络连接失败',
    content: '无法连接到 LLM 服务，请检查网络设置。',
  },
}

function showErrorModal(errorCode: string, errorMessage: string) {
  const errorInfo = ERROR_MESSAGES[errorCode] || {
    title: '工作流执行失败',
    content: errorMessage || '发生未知错误，请稍后重试。',
  }
  const content = errorMessage && errorMessage !== errorInfo.content
    ? `${errorInfo.content}\n\n详细信息: ${errorMessage}`
    : errorInfo.content
  Modal.error({
    title: errorInfo.title,
    content,
    width: 480,
  })
}

interface WorkflowState {
  currentWorkflow: WorkflowContext | null
  agentStatuses: AgentStatusInfo[]
  conceptCard: ConceptCard | null
  recipeCard: StandardRecipeCard | null
  loading: boolean
  wsConnected: boolean
  error: string | null
  selectedModel: string | null
  availableModels: AvailableModel[]
  createWorkflow: (customerInput: string) => Promise<string | null>
  loadWorkflow: (workflowId: string) => Promise<void>
  approveWorkflow: (workflowId: string, approved: boolean, comments: string) => Promise<void>
  connectWebSocket: (workflowId: string) => void
  disconnectWebSocket: () => void
  handleWebSocketMessage: (message: WSMessage) => void
  loadAvailableModels: () => Promise<void>
  setSelectedModel: (model: string | null) => void
  reset: () => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  currentWorkflow: null,
  agentStatuses: [],
  conceptCard: null,
  recipeCard: null,
  loading: false,
  wsConnected: false,
  error: null,
  selectedModel: null,
  availableModels: [],

  createWorkflow: async (customerInput: string) => {
    set({ loading: true, error: null })
    try {
      const { selectedModel } = get()
      const response = await workflowApi.createWorkflow({
        customer_input: customerInput,
        model: selectedModel || undefined,
      })
      await get().loadWorkflow(response.workflow_id)
      set({ loading: false })
      return response.workflow_id
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '创建工作流失败'
      set({ loading: false, error: errorMessage })
      return null
    }
  },

  loadWorkflow: async (workflowId: string) => {
    try {
      const workflow = await workflowApi.getWorkflow(workflowId)
      set({ currentWorkflow: workflow })
      if (workflow.rd_chef_output) {
        set({ conceptCard: workflow.rd_chef_output.concept_card || null })
      }
      if (workflow.head_chef_output) {
        set({ recipeCard: workflow.head_chef_output.recipe_card || null })
      }
      // 根据工作流状态更新 Agent 状态
      const status = workflow.status
      const agentStatuses = [
        { 
          role: 'operations_director', 
          name: '运营总监', 
          status: ['nutrition_designing', 'concept_designing', 'recipe_reviewing', 'waiting_approval', 'approved', 'completed'].includes(status) ? 'completed' : 
                  status === 'extracting' ? 'processing' :
                  status === 'failed' ? 'rejected' : 'idle',
          current_task: status === 'extracting' ? '正在提取需求...' : undefined
        },
        { 
          role: 'nutritionist', 
          name: '营养师', 
          status: ['concept_designing', 'recipe_reviewing', 'waiting_approval', 'approved', 'completed'].includes(status) ? 'completed' : 
                  status === 'nutrition_designing' ? 'processing' :
                  status === 'failed' ? 'rejected' : 'idle',
          current_task: status === 'nutrition_designing' ? '正在设计营养方案...' : undefined
        },
        { 
          role: 'rd_chef', 
          name: '研发主厨', 
          status: ['recipe_reviewing', 'waiting_approval', 'approved', 'completed'].includes(status) ? 'completed' : 
                  status === 'concept_designing' ? 'processing' :
                  status === 'failed' ? 'rejected' : 'idle',
          current_task: status === 'concept_designing' ? '正在设计概念卡...' : undefined
        },
        { 
          role: 'head_chef', 
          name: '厨师长', 
          status: ['waiting_approval', 'approved', 'completed'].includes(status) ? 'completed' : 
                  status === 'recipe_reviewing' ? 'processing' :
                  status === 'failed' ? 'rejected' : 'idle',
          current_task: status === 'recipe_reviewing' ? '正在审评食谱...' : undefined
        },
      ]
      set({ agentStatuses })
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '加载工作流失败'
      set({ error: errorMessage })
    }
  },

  approveWorkflow: async (workflowId: string, approved: boolean, comments: string) => {
    set({ loading: true, error: null })
    try {
      await workflowApi.approveWorkflow(workflowId, {
        approved,
        comments,
        reviewer: '管理员',
      })
      await get().loadWorkflow(workflowId)
      set({ loading: false })
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '审批失败'
      set({ loading: false, error: errorMessage })
    }
  },

  connectWebSocket: (workflowId: string) => {
    wsService.connect(workflowId)
    wsService.onConnect(() => set({ wsConnected: true }))
    wsService.onDisconnect(() => set({ wsConnected: false }))
    wsService.onMessage((message: WSMessage) => get().handleWebSocketMessage(message))
  },

  disconnectWebSocket: () => {
    wsService.disconnect()
    set({ wsConnected: false })
  },

  handleWebSocketMessage: (message: WSMessage) => {
    const { currentWorkflow } = get()
    if (!currentWorkflow) return
    switch (message.type) {
      case 'agent_status_change': {
        const data = message.data as {
          agent_role: string
          agent_name: string
          new_status: string
          current_task?: string
        }
        set((state) => {
          // 如果 agentStatuses 为空，先初始化所有 Agent
          let agentStatuses = state.agentStatuses
          if (agentStatuses.length === 0) {
            agentStatuses = [
              { role: 'operations_director', name: '运营总监', status: 'idle' },
              { role: 'nutritionist', name: '营养师', status: 'idle' },
              { role: 'rd_chef', name: '研发主厨', status: 'idle' },
              { role: 'head_chef', name: '厨师长', status: 'idle' },
            ]
          }
          return {
            agentStatuses: agentStatuses.map((agent) =>
              agent.role === data.agent_role
                ? { ...agent, status: data.new_status, current_task: data.current_task }
                : agent
            ),
          }
        })
        // 如果Agent失败，立即弹出错误提示
        if (data.new_status === 'failed') {
          const errorMsg = data.current_task || `${data.agent_name}执行失败`
          set({ error: errorMsg })
          showErrorModal('AGENT_ERROR', errorMsg)
        }
        break
      }
      case 'step_completed':
      case 'approval_required':
      case 'workflow_completed':
      case 'workflow_failed':
        get().loadWorkflow(currentWorkflow.workflow_id)
        break
      case 'error': {
        const data = message.data as { error_code?: string; message: string }
        const errorCode = data.error_code || 'WORKFLOW_ERROR'
        set({ error: data.message })
        showErrorModal(errorCode, data.message)
        // 错误时也要刷新工作流状态，确保UI显示最新状态
        get().loadWorkflow(currentWorkflow.workflow_id)
        break
      }
    }
  },

  reset: () => {
    set({
      currentWorkflow: null,
      agentStatuses: [],
      conceptCard: null,
      recipeCard: null,
      loading: false,
      error: null,
    })
  },

  loadAvailableModels: async () => {
    try {
      const models = await modelsApi.getAvailableModels()
      set({ availableModels: models })
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '获取模型列表失败'
      set({ error: errorMessage })
    }
  },

  setSelectedModel: (model: string | null) => {
    set({ selectedModel: model })
  },
}))
