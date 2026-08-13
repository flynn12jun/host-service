import { Card, Steps, Typography, Space, Tag, Spin } from 'antd'
import {
  CheckCircleFilled,
  LoadingOutlined,
  ClockCircleFilled,
  CloseCircleFilled,
} from '@ant-design/icons'
import { useWorkflowStore } from '../store/workflowStore'
import { AgentRole, AgentStatus, WorkflowStatus } from '../types'

const { Title, Text } = Typography

const AGENT_INFO: Record<AgentRole, { name: string; icon: string; description: string }> = {
  [AgentRole.OPERATIONS_DIRECTOR]: {
    name: '运营总监',
    icon: '📋',
    description: '需求提取',
  },
  [AgentRole.NUTRITIONIST]: {
    name: '营养师',
    icon: '🥗',
    description: '营养设计',
  },
  [AgentRole.RD_CHEF]: {
    name: '研发主厨',
    icon: '👨‍🍳',
    description: '概念设计',
  },
  [AgentRole.HEAD_CHEF]: {
    name: '厨师长',
    icon: '🍳',
    description: '食谱审评',
  },
}

const STATUS_CONFIG: Record<
  AgentStatus,
  { color: string; icon: React.ReactNode; text: string }
> = {
  [AgentStatus.IDLE]: {
    color: 'default',
    icon: <ClockCircleFilled />,
    text: '等待中',
  },
  [AgentStatus.PROCESSING]: {
    color: 'processing',
    icon: <LoadingOutlined />,
    text: '处理中',
  },
  [AgentStatus.WAITING_REVIEW]: {
    color: 'warning',
    icon: <ClockCircleFilled />,
    text: '等待审批',
  },
  [AgentStatus.COMPLETED]: {
    color: 'success',
    icon: <CheckCircleFilled />,
    text: '已完成',
  },
  [AgentStatus.REJECTED]: {
    color: 'error',
    icon: <CloseCircleFilled />,
    text: '已驳回',
  },
}

const WORKFLOW_STATUS_TEXT: Record<WorkflowStatus, string> = {
  created: '已创建',
  extracting: '需求提取中',
  nutrition_designing: '营养设计中',
  concept_designing: '概念设计中',
  recipe_reviewing: '食谱审评中',
  waiting_approval: '等待审批',
  approved: '已通过',
  rejected: '已驳回',
  revising: '修改中',
  completed: '已完成',
  failed: '失败',
}

const AgentStatusPanel = () => {
  const { currentWorkflow, agentStatuses } = useWorkflowStore()

  if (!currentWorkflow) return null

  // 根据工作流状态计算各 Agent 状态
  const getAgentStatus = (role: AgentRole): AgentStatus => {
    const agentFromList = agentStatuses.find((a) => a.role === role)
    if (agentFromList) {
      return agentFromList.status as AgentStatus
    }

    const status = currentWorkflow.status
    const roleOrder = [
      AgentRole.OPERATIONS_DIRECTOR,
      AgentRole.NUTRITIONIST,
      AgentRole.RD_CHEF,
      AgentRole.HEAD_CHEF,
    ]
    const currentIndex = roleOrder.indexOf(role)

    // 根据工作流状态推断当前活跃的 Agent
    const statusMap: Record<WorkflowStatus, number> = {
      created: -1,
      extracting: 0,
      nutrition_designing: 1,
      concept_designing: 2,
      recipe_reviewing: 3,
      waiting_approval: 3,
      approved: 3,
      rejected: 3,
      revising: 2,
      completed: 3,
      failed: -1,
    }

    const activeIndex = statusMap[status]

    if (currentIndex < activeIndex) return AgentStatus.COMPLETED
    if (currentIndex === activeIndex) {
      if (status === WorkflowStatus.WAITING_APPROVAL) return AgentStatus.WAITING_REVIEW
      if (status === WorkflowStatus.COMPLETED) return AgentStatus.COMPLETED
      if (status === WorkflowStatus.FAILED) return AgentStatus.REJECTED
      return AgentStatus.PROCESSING
    }
    return AgentStatus.IDLE
  }

  const steps = Object.values(AgentRole).map((role) => {
    const info = AGENT_INFO[role]
    const status = getAgentStatus(role)
    const config = STATUS_CONFIG[status]

    return {
      title: (
        <Space>
          <span style={{ fontSize: 16 }}>{info.icon}</span>
          <Text strong>{info.name}</Text>
        </Space>
      ),
      description: (
        <Space direction="vertical" size={0}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {info.description}
          </Text>
          <Tag color={config.color} icon={config.icon} style={{ marginTop: 4 }}>
            {config.text}
          </Tag>
        </Space>
      ),
      status:
        status === AgentStatus.COMPLETED
          ? 'finish'
          : status === AgentStatus.PROCESSING
            ? 'process'
            : status === AgentStatus.REJECTED
              ? 'error'
              : 'wait',
    }
  })

  return (
    <Card
      style={{
        marginBottom: 24,
        borderRadius: 12,
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.06)',
      }}
      bodyStyle={{ padding: 24 }}
    >
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
          🤖 Agent 工作状态
        </Title>
        <Space>
          <Text type="secondary">当前状态：</Text>
          <Tag color="blue">{WORKFLOW_STATUS_TEXT[currentWorkflow.status]}</Tag>
        </Space>
      </div>

      <Steps
        current={steps.findIndex((s) => s.status === 'process')}
        status="process"
        size="small"
        style={{ overflowX: 'auto' }}
      >
        {steps.map((step, index) => (
          <Steps.Step
            key={index}
            title={step.title}
            description={step.description}
            status={step.status as 'wait' | 'process' | 'finish' | 'error'}
            icon={
              step.status === 'process' ? (
                <Spin size="small" />
              ) : undefined
            }
          />
        ))}
      </Steps>
    </Card>
  )
}

export default AgentStatusPanel
