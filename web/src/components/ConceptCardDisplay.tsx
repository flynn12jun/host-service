import { Card, Typography, Tag, Space, Divider, Row, Col, Statistic } from 'antd'
import {
  ExperimentOutlined,
  DollarOutlined,
  FireOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import type { ConceptCard } from '../types'

const { Title, Text, Paragraph } = Typography

interface ConceptCardDisplayProps {
  conceptCard: ConceptCard
}

const ConceptCardDisplay = ({ conceptCard }: ConceptCardDisplayProps) => {
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
          <ExperimentOutlined style={{ marginRight: 8 }} />
          概念卡
        </Title>
        <Text type="secondary">研发主厨设计的菜品概念方案</Text>
      </div>

      {/* 菜品名称 */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%)',
          padding: '16px 20px',
          borderRadius: 8,
          marginBottom: 20,
        }}
      >
        <Title level={3} style={{ margin: 0, color: '#389e0d' }}>
          {conceptCard.dish_name}
        </Title>
      </div>

      {/* 关键指标 */}
      <Row gutter={16} style={{ marginBottom: 20 }}>
        <Col span={6}>
          <Statistic
            title="预估成本"
            value={conceptCard.estimated_cost}
            prefix={<DollarOutlined />}
            suffix="元"
            valueStyle={{ color: '#cf1322', fontSize: 20 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="营养方向"
            value={conceptCard.nutrition_direction}
            prefix={<FireOutlined />}
            valueStyle={{ color: '#389e0d', fontSize: 16 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="烹饪方式"
            value={conceptCard.cooking_method}
            prefix={<ExperimentOutlined />}
            valueStyle={{ color: '#1677ff', fontSize: 16 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="创新点数量"
            value={conceptCard.innovation_points?.length || 0}
            prefix={<BulbOutlined />}
            suffix="个"
            valueStyle={{ color: '#722ed1', fontSize: 20 }}
          />
        </Col>
      </Row>

      <Divider />

      {/* 食材组合 */}
      <div style={{ marginBottom: 20 }}>
        <Title level={5}>🥬 食材组合</Title>
        <div>
          {conceptCard.food_combination?.map((item, index) => (
            <Tag
              key={index}
              color="green"
              style={{ marginBottom: 8, fontSize: 13, padding: '4px 12px' }}
            >
              {item.name} {item.quantity}
              {item.unit}
            </Tag>
          ))}
        </div>
      </div>

      {/* 风味结构 */}
      {conceptCard.flavor_structure && (
        <div style={{ marginBottom: 20 }}>
          <Title level={5}>👅 风味结构</Title>
          <Row gutter={[8, 8]}>
            {Object.entries(conceptCard.flavor_structure).map(([key, value]) => (
              <Col key={key}>
                <Tag color="orange" style={{ fontSize: 13 }}>
                  {key}: {String(value)}
                </Tag>
              </Col>
            ))}
          </Row>
        </div>
      )}

      {/* 摆盘方向 */}
      {conceptCard.plating_direction && (
        <div style={{ marginBottom: 20 }}>
          <Title level={5}>🎨 摆盘方向</Title>
          <Paragraph style={{ background: '#f5f5f5', padding: 12, borderRadius: 8 }}>
            {conceptCard.plating_direction}
          </Paragraph>
        </div>
      )}

      {/* 创新点 */}
      {conceptCard.innovation_points && conceptCard.innovation_points.length > 0 && (
        <div>
          <Title level={5}>💡 创新点</Title>
          <Space direction="vertical" size={4}>
            {conceptCard.innovation_points.map((point, index) => (
              <div key={index}>
                <Text type="secondary" style={{ marginRight: 8 }}>
                  {index + 1}.
                </Text>
                <Text>{point}</Text>
              </div>
            ))}
          </Space>
        </div>
      )}
    </Card>
  )
}

export default ConceptCardDisplay
