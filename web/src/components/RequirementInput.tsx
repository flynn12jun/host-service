import { useState, useEffect } from 'react'
import { Card, Input, Button, Space, Typography, message, Select, Tag } from 'antd'
import { SendOutlined, LoadingOutlined, RobotOutlined } from '@ant-design/icons'
import { useWorkflowStore } from '../store/workflowStore'

const { TextArea } = Input
const { Text, Title } = Typography

const EXAMPLE_REQUIREMENTS = [
  '设计一款适合健身人群的高蛋白低脂菜品，口味偏咸鲜，预算15元以内',
  '为上班族设计一款营养均衡的午餐，热量控制在500kcal左右，包含优质碳水',
  '设计一款适合儿童的轻食餐，口味清淡，营养全面，色彩丰富',
]

const RequirementInput = () => {
  const [input, setInput] = useState('')
  const { createWorkflow, connectWebSocket, loading, currentWorkflow, availableModels, selectedModel, loadAvailableModels, setSelectedModel } = useWorkflowStore()

  useEffect(() => {
    loadAvailableModels()
  }, [])

  const handleSubmit = async () => {
    if (!input.trim()) {
      message.warning('请输入您的需求')
      return
    }

    const workflowId = await createWorkflow(input.trim())
    if (workflowId) {
      message.success('工作流已创建，Agent 开始协同工作')
      localStorage.setItem('current_workflow_id', workflowId)
      connectWebSocket(workflowId)
      setInput('')
    }
  }

  const handleExampleClick = (example: string) => {
    setInput(example)
  }

  const modelOptions = availableModels.map((model) => ({
    value: model.name,
    label: (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>{model.name}</span>
        <Tag color={model.available ? 'success' : 'error'} style={{ margin: 0 }}>
          {model.provider}
        </Tag>
        {!model.available && <span style={{ color: '#ff4d4f', fontSize: 12 }}>未配置</span>}
      </div>
    ),
    disabled: !model.available,
  }))

  return (
    <Card
      style={{
        marginBottom: 24,
        borderRadius: 12,
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.06)',
      }}
      bodyStyle={{ padding: 24 }}
    >
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
          📝 需求输入
        </Title>
        <Text type="secondary">
          请描述您的菜品研发需求，系统将自动启动多Agent协同工作流程
        </Text>
      </div>

      <TextArea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="请输入您的需求...&#10;例如：设计一款适合健身人群的高蛋白低脂菜品，口味偏咸鲜，预算15元以内"
        autoSize={{ minRows: 3, maxRows: 6 }}
        style={{
          fontSize: 15,
          borderRadius: 8,
          marginBottom: 16,
        }}
        disabled={loading}
      />

      <div style={{ marginBottom: 16 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
          🤖 选择模型（可选，默认使用系统配置）：
        </Text>
        <Select
          placeholder="选择 LLM 模型"
          value={selectedModel}
          onChange={setSelectedModel}
          options={modelOptions}
          style={{ width: '100%' }}
          allowClear
          showSearch
          filterOption={(input, option) =>
            (option?.value as string)?.toLowerCase().includes(input.toLowerCase())
          }
          suffixIcon={<RobotOutlined />}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
          💡 快速示例（点击填入）：
        </Text>
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          {EXAMPLE_REQUIREMENTS.map((example, index) => (
            <Button
              key={index}
              type="text"
              size="small"
              onClick={() => handleExampleClick(example)}
              style={{
                textAlign: 'left',
                height: 'auto',
                whiteSpace: 'normal',
                color: '#595959',
                padding: '4px 8px',
              }}
            >
              {index + 1}. {example}
            </Button>
          ))}
        </Space>
      </div>

      <Button
        type="primary"
        size="large"
        icon={loading ? <LoadingOutlined /> : <SendOutlined />}
        onClick={handleSubmit}
        loading={loading}
        block
        style={{
          height: 48,
          borderRadius: 8,
          background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
          border: 'none',
        }}
      >
        {loading ? '正在启动工作流...' : '开始设计'}
      </Button>
    </Card>
  )
}

export default RequirementInput
