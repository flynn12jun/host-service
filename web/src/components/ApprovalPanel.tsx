import { useState } from 'react'
import { Card, Typography, Input, Button, Space, message, Modal } from 'antd'
import {
  CheckOutlined,
  CloseOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useWorkflowStore } from '../store/workflowStore'

const { Title, Text } = Typography
const { TextArea } = Input

const ApprovalPanel = () => {
  const [comments, setComments] = useState('')
  const [loading, setLoading] = useState(false)
  const { currentWorkflow, approveWorkflow } = useWorkflowStore()

  const handleApprove = () => {
    if (!currentWorkflow) return
    Modal.confirm({
      title: '确认通过',
      icon: <ExclamationCircleOutlined />,
      content: '确认通过此食谱方案？通过后工作流将完成。',
      onOk: async () => {
        setLoading(true)
        try {
          await approveWorkflow(currentWorkflow.workflow_id, true, comments || '通过')
          message.success('审批通过，工作流已完成')
        } catch {
          message.error('审批失败')
        } finally {
          setLoading(false)
        }
      },
    })
  }

  const handleReject = () => {
    if (!currentWorkflow) return
    if (!comments.trim()) {
      message.warning('驳回时请填写审批意见')
      return
    }
    Modal.confirm({
      title: '确认驳回',
      icon: <ExclamationCircleOutlined />,
      content: '确认驳回此食谱方案？方案将打回研发主厨重新设计。',
      onOk: async () => {
        setLoading(true)
        try {
          await approveWorkflow(currentWorkflow.workflow_id, false, comments)
          message.success('已驳回，研发主厨将重新设计')
          setComments('')
        } catch {
          message.error('审批失败')
        } finally {
          setLoading(false)
        }
      },
    })
  }

  if (!currentWorkflow) return null

  return (
    <Card
      style={{
        marginBottom: 24,
        borderRadius: 12,
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.06)',
        border: '2px solid #faad14',
      }}
      bodyStyle={{ padding: 24 }}
    >
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
          ⚖️ 审批操作
        </Title>
        <Text type="secondary">
          请审评标准食谱卡，选择通过或驳回
        </Text>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>
          审批意见 {!comments.trim() && <Text type="warning">（驳回时必填）</Text>}
        </Text>
        <TextArea
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          placeholder="请输入审批意见..."
          autoSize={{ minRows: 3, maxRows: 6 }}
          style={{ borderRadius: 8 }}
        />
      </div>

      <Space size={16}>
        <Button
          type="primary"
          size="large"
          icon={<CheckOutlined />}
          onClick={handleApprove}
          loading={loading}
          style={{
            minWidth: 120,
            height: 48,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
            border: 'none',
          }}
        >
          通 过
        </Button>
        <Button
          danger
          size="large"
          icon={<CloseOutlined />}
          onClick={handleReject}
          loading={loading}
          style={{
            minWidth: 120,
            height: 48,
            borderRadius: 8,
          }}
        >
          驳 回
        </Button>
      </Space>

      {currentWorkflow.revision_count > 0 && (
        <div style={{ marginTop: 16 }}>
          <Text type="warning">
            ⚠️ 当前为第 {currentWorkflow.revision_count} 次修改（最多 {currentWorkflow.max_revisions} 次）
          </Text>
        </div>
      )}
    </Card>
  )
}

export default ApprovalPanel
