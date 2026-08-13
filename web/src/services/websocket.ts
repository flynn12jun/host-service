import type { WSMessage } from '../types'

type MessageHandler = (message: WSMessage) => void
type ConnectionHandler = () => void

class WebSocketService {
  private ws: WebSocket | null = null
  private workflowId: string | null = null
  private messageHandlers: Set<MessageHandler> = new Set()
  private connectionHandlers: Set<ConnectionHandler> = new Set()
  private disconnectionHandlers: Set<ConnectionHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isManualClose = false

  /**
   * 连接 WebSocket
   */
  connect(workflowId: string): void {
    this.workflowId = workflowId
    this.isManualClose = false

    // 如果已有连接，先关闭
    if (this.ws) {
      this.ws.close()
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/workflows/${workflowId}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket 连接成功')
      this.reconnectAttempts = 0
      this.connectionHandlers.forEach((handler) => handler())
    }

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        this.messageHandlers.forEach((handler) => handler(message))
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error)
      }
    }

    this.ws.onclose = (event: CloseEvent) => {
      console.log('WebSocket 连接关闭:', event.code, event.reason)
      this.disconnectionHandlers.forEach((handler) => handler())

      // 非手动关闭时尝试重连
      if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
        console.log(`WebSocket ${this.reconnectAttempts} 秒后尝试重连...`)
        this.reconnectTimer = setTimeout(() => {
          if (this.workflowId) {
            this.connect(this.workflowId)
          }
        }, delay)
      }
    }

    this.ws.onerror = (error: Event) => {
      console.error('WebSocket 错误:', error)
    }
  }

  /**
   * 断开 WebSocket 连接
   */
  disconnect(): void {
    this.isManualClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.workflowId = null
  }

  /**
   * 发送消息
   */
  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket 未连接，无法发送消息')
    }
  }

  /**
   * 订阅消息
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => {
      this.messageHandlers.delete(handler)
    }
  }

  /**
   * 订阅连接事件
   */
  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler)
    return () => {
      this.connectionHandlers.delete(handler)
    }
  }

  /**
   * 订阅断开事件
   */
  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectionHandlers.add(handler)
    return () => {
      this.disconnectionHandlers.delete(handler)
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 导出单例
export const wsService = new WebSocketService()
export default wsService
