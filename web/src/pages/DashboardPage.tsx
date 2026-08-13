import { useEffect } from 'react'
import { Layout, Button, Badge, Dropdown, message } from 'antd'
import {
  LogoutOutlined,
  UserOutlined,
  WifiOutlined,
  WifiOutlined as WifiOffOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useWorkflowStore } from '../store/workflowStore'
import RequirementInput from '../components/RequirementInput'
import AgentStatusPanel from '../components/AgentStatusPanel'
import ConceptCardDisplay from '../components/ConceptCardDisplay'
import RecipeCardDisplay from '../components/RecipeCardDisplay'
import ApprovalPanel from '../components/ApprovalPanel'

const { Header, Content } = Layout

const DashboardPage = () => {
  const navigate = useNavigate()
  const { username, logout } = useAuthStore()
  const {
    currentWorkflow,
    wsConnected,
    loadWorkflow,
    connectWebSocket,
    disconnectWebSocket,
    reset,
  } = useWorkflowStore()

  // 页面加载时恢复工作流并连接 WebSocket
  useEffect(() => {
    const savedWorkflowId = localStorage.getItem('current_workflow_id')
    if (savedWorkflowId) {
      loadWorkflow(savedWorkflowId)
      connectWebSocket(savedWorkflowId)
    }
    return () => {
      disconnectWebSocket()
    }
  }, [])

  const handleLogout = async () => {
    disconnectWebSocket()
    reset()
    await logout()
    navigate('/login')
  }

  const handleRefresh = () => {
    if (currentWorkflow) {
      loadWorkflow(currentWorkflow.workflow_id)
      message.success('已刷新')
    }
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 24 }}>🥗</span>
          <h1
            style={{
              margin: 0,
              fontSize: 18,
              fontWeight: 600,
              color: '#1f1f1f',
            }}
          >
            HOST轻食 多Agent框架
          </h1>
          <Badge
            status={wsConnected ? 'success' : 'error'}
            text={
              <span style={{ fontSize: 12, color: '#8c8c8c' }}>
                {wsConnected ? '实时连接已建立' : '连接已断开'}
              </span>
            }
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {currentWorkflow && (
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              size="middle"
            >
              刷新
            </Button>
          )}
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button icon={<UserOutlined />} size="middle">
              {username || '管理员'}
            </Button>
          </Dropdown>
        </div>
      </Header>

      <Content style={{ padding: 24, maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        {/* 需求输入区域 */}
        <RequirementInput />

        {/* Agent 工作状态面板 */}
        {currentWorkflow && <AgentStatusPanel />}

        {/* 概念卡展示 */}
        {currentWorkflow?.rd_chef_output?.concept_card && (
          <ConceptCardDisplay conceptCard={currentWorkflow.rd_chef_output.concept_card} />
        )}

        {/* 标准食谱卡展示 */}
        {currentWorkflow?.head_chef_output?.recipe_card && (
          <RecipeCardDisplay recipeCard={currentWorkflow.head_chef_output.recipe_card} />
        )}

        {/* 审批面板 */}
        {currentWorkflow?.status === 'waiting_approval' && <ApprovalPanel />}
      </Content>
    </Layout>
  )
}

export default DashboardPage
