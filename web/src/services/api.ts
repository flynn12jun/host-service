import axios, { AxiosInstance, AxiosError } from 'axios'
import { message } from 'antd'
import type {
  CreateWorkflowRequest,
  ApprovalRequest,
  WorkflowResponse,
  WorkflowContext,
  AgentStatusInfo,
  ConceptCard,
  StandardRecipeCard,
  AvailableModel,
} from '../types'

const API_BASE_URL = '/api/v1'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加认证 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    if (error.response) {
      const { status, data } = error.response
      const errorMsg = data?.detail || data?.message || '请求失败'

      if (status === 401) {
        message.error('认证已过期，请重新登录')
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      } else if (status === 403) {
        message.error('没有权限执行此操作')
      } else if (status === 404) {
        message.error('请求的资源不存在')
      } else if (status >= 500) {
        message.error('服务器内部错误，请稍后重试')
      } else {
        message.error(errorMsg)
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络设置')
    } else {
      message.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

// ==================== API 方法 ====================

export const authApi = {
  /**
   * 用户登录
   */
  login: async (password: string): Promise<{ token: string; username: string }> => {
    const response = await apiClient.post('/auth/login', { password })
    return response.data
  },

  /**
   * 验证 token 是否有效
   */
  verifyToken: async (): Promise<boolean> => {
    try {
      await apiClient.get('/auth/verify')
      return true
    } catch {
      return false
    }
  },

  /**
   * 用户登出
   */
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout')
    } catch {
      // 忽略登出错误
    }
  },
}

export const workflowApi = {
  /**
   * 创建新的工作流
   */
  createWorkflow: async (data: CreateWorkflowRequest): Promise<WorkflowResponse> => {
    const response = await apiClient.post('/workflows', data)
    return response.data
  },

  /**
   * 获取工作流详情
   */
  getWorkflow: async (workflowId: string): Promise<WorkflowContext> => {
    const response = await apiClient.get(`/workflows/${workflowId}`)
    return response.data
  },

  /**
   * 获取所有 Agent 状态
   */
  getAgentStatuses: async (workflowId: string): Promise<AgentStatusInfo[]> => {
    const response = await apiClient.get(`/workflows/${workflowId}/agents`)
    return response.data
  },

  /**
   * 获取概念卡
   */
  getConceptCard: async (workflowId: string): Promise<ConceptCard> => {
    const response = await apiClient.get(`/workflows/${workflowId}/concept-card`)
    return response.data
  },

  /**
   * 获取标准食谱卡
   */
  getRecipeCard: async (workflowId: string): Promise<StandardRecipeCard> => {
    const response = await apiClient.get(`/workflows/${workflowId}/recipe-card`)
    return response.data
  },

  /**
   * 审批工作流
   */
  approveWorkflow: async (
    workflowId: string,
    data: ApprovalRequest
  ): Promise<{ message: string; workflow_id: string; approved: boolean }> => {
    const response = await apiClient.post(`/workflows/${workflowId}/approve`, data)
    return response.data
  },

  /**
   * 获取工作流历史记录
   */
  getWorkflowHistory: async (workflowId: string): Promise<unknown[]> => {
    const response = await apiClient.get(`/workflows/${workflowId}/history`)
    return response.data
  },

  /**
   * 获取所有工作流列表
   */
  listWorkflows: async (): Promise<WorkflowResponse[]> => {
    const response = await apiClient.get('/workflows')
    return response.data
  },
}

export const modelsApi = {
  /**
   * 获取可用模型列表
   */
  getAvailableModels: async (): Promise<AvailableModel[]> => {
    const response = await apiClient.get('/models')
    return response.data
  },
}

export default apiClient
