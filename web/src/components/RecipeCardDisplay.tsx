import { Card, Typography, Tag, Space, Divider, Steps, Collapse, Row, Col, Statistic } from 'antd'
import {
  FileTextOutlined,
  ShoppingOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  DollarOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import type { StandardRecipeCard } from '../types'

const { Title, Text, Paragraph } = Typography

interface RecipeCardDisplayProps {
  recipeCard: StandardRecipeCard
}

const RecipeCardDisplay = ({ recipeCard }: RecipeCardDisplayProps) => {
  const {
    dish_name,
    version,
    ingredients,
    seasonings,
    equipment,
    steps,
    quality_standards,
    plating_specification,
    cost_breakdown,
    nutrition_facts,
    review_status,
  } = recipeCard

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
          <FileTextOutlined style={{ marginRight: 8 }} />
          标准食谱卡
        </Title>
        <Space>
          <Text type="secondary">版本：{version}</Text>
          <Tag
            color={review_status === 'approved' ? 'success' : review_status === 'rejected' ? 'error' : 'processing'}
          >
            {review_status === 'approved' ? '已通过' : review_status === 'rejected' ? '已驳回' : '待审批'}
          </Tag>
        </Space>
      </div>

      {/* 菜品名称 */}
      <div
        style={{
          background: 'linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%)',
          padding: '16px 20px',
          borderRadius: 8,
          marginBottom: 20,
        }}
      >
        <Title level={3} style={{ margin: 0, color: '#096dd9' }}>
          {dish_name}
        </Title>
      </div>

      {/* 成本与营养概览 */}
      <Row gutter={16} style={{ marginBottom: 20 }}>
        <Col span={6}>
          <Statistic
            title="总成本"
            value={Object.values(cost_breakdown || {}).reduce((a, b) => a + b, 0)}
            precision={2}
            prefix={<DollarOutlined />}
            suffix="元"
            valueStyle={{ color: '#cf1322' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="热量"
            value={nutrition_facts?.calories || 0}
            prefix={<ThunderboltOutlined />}
            suffix="kcal"
            valueStyle={{ color: '#389e0d' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="蛋白质"
            value={nutrition_facts?.protein || 0}
            suffix="g"
            valueStyle={{ color: '#1677ff' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="步骤数"
            value={steps?.length || 0}
            prefix={<CheckCircleOutlined />}
            suffix="步"
            valueStyle={{ color: '#722ed1' }}
          />
        </Col>
      </Row>

      <Divider />

      {/* 食材清单 */}
      <div style={{ marginBottom: 20 }}>
        <Title level={5}>
          <ShoppingOutlined style={{ marginRight: 8 }} />
          食材清单
        </Title>
        <div>
          {ingredients?.map((item, index) => (
            <Tag
              key={index}
              color="cyan"
              style={{ marginBottom: 8, fontSize: 13, padding: '4px 12px' }}
            >
              {item.name} {item.quantity}
              {item.unit}
            </Tag>
          ))}
        </div>
      </div>

      {/* 调料清单 */}
      {seasonings && seasonings.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <Title level={5}>🧂 调料清单</Title>
          <div>
            {seasonings.map((item, index) => (
              <Tag
                key={index}
                color="gold"
                style={{ marginBottom: 8, fontSize: 13, padding: '4px 12px' }}
              >
                {item.name} {item.quantity}
                {item.unit}
              </Tag>
            ))}
          </div>
        </div>
      )}

      {/* 设备需求 */}
      {equipment && equipment.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <Title level={5}>
            <ToolOutlined style={{ marginRight: 8 }} />
            设备需求
          </Title>
          <div>
            {equipment.map((item, index) => (
              <Tag key={index} color="blue" style={{ marginBottom: 8, fontSize: 13 }}>
                {item}
              </Tag>
            ))}
          </div>
        </div>
      )}

      <Divider />

      {/* 制作步骤 */}
      {steps && steps.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <Title level={5}>👨‍🍳 制作步骤</Title>
          <Steps
            direction="vertical"
            size="small"
            current={steps.length}
            style={{ marginTop: 16 }}
          >
            {steps.map((step) => (
              <Steps.Step
                key={step.step_number}
                title={
                  <Space>
                    <Tag color="blue">步骤 {step.step_number}</Tag>
                    <Text strong>{step.description}</Text>
                  </Space>
                }
                description={
                  <Space size={16} wrap>
                    {step.duration > 0 && (
                      <Text type="secondary">⏱ {step.duration} 分钟</Text>
                    )}
                    {step.temperature && (
                      <Text type="secondary">🌡 {step.temperature}</Text>
                    )}
                    {step.tips && <Text type="warning">💡 {step.tips}</Text>}
                  </Space>
                }
              />
            ))}
          </Steps>
        </div>
      )}

      <Divider />

      {/* 可折叠区域 */}
      <Collapse
        items={[
          {
            key: 'quality',
            label: <><CheckCircleOutlined style={{ marginRight: 8 }} />质量标准</>,
            children: (
              <Space direction="vertical" size={4}>
                {quality_standards?.map((standard, index) => (
                  <div key={index}>
                    <Text type="secondary" style={{ marginRight: 8 }}>
                      {index + 1}.
                    </Text>
                    <Text>{standard}</Text>
                  </div>
                ))}
              </Space>
            ),
          },
          {
            key: 'plating',
            label: <><FileTextOutlined style={{ marginRight: 8 }} />摆盘规格</>,
            children: <Paragraph>{plating_specification}</Paragraph>,
          },
          {
            key: 'cost',
            label: <><DollarOutlined style={{ marginRight: 8 }} />成本明细</>,
            children: (
              <Row gutter={[16, 16]}>
                {Object.entries(cost_breakdown || {}).map(([key, value]) => (
                  <Col key={key} span={8}>
                    <Statistic title={key} value={value} precision={2} suffix="元" />
                  </Col>
                ))}
              </Row>
            ),
          },
          {
            key: 'nutrition',
            label: <><ThunderboltOutlined style={{ marginRight: 8 }} />营养成分</>,
            children: (
              <Row gutter={[16, 16]}>
                {Object.entries(nutrition_facts || {}).map(([key, value]) => (
                  <Col key={key} span={8}>
                    <Statistic title={key} value={value} />
                  </Col>
                ))}
              </Row>
            ),
          },
        ]}
        style={{ background: '#fafafa' }}
      />
    </Card>
  )
}

export default RecipeCardDisplay
