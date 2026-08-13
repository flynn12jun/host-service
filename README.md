# HOST轻食多Agent框架

基于多Agent协同工作的智能菜品研发工作流系统。

## 项目结构

```
host-service/
├── backend/                    # 后端代码
│   ├── agents/                 # Agent角色实现
│   │   ├── __init__.py
│   │   ├── base.py             # Agent基类
│   │   ├── operations_director.py  # 运营总监
│   │   ├── nutritionist.py     # 营养师
│   │   ├── rd_chef.py          # 研发主厨
│   │   └── head_chef.py        # 厨师长
│   ├── api/                    # API接口
│   │   ├── __init__.py
│   │   └── routes.py           # 路由定义
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py           # 应用配置
│   │   └── database.py         # 数据库配置
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── agent.py            # Agent模型
│   │   ├── workflow.py         # 工作流模型
│   │   ├── concept_card.py     # 概念卡模型
│   │   ├── recipe_card.py      # 食谱卡模型
│   │   └── approval.py         # 审批模型
│   ├── services/               # 业务服务
│   │   ├── __init__.py
│   │   ├── llm_service.py      # LLM服务
│   │   ├── workflow_engine.py  # 工作流引擎
│   │   └── websocket_manager.py # WebSocket管理
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   └── logger.py           # 日志工具
│   ├── main.py                 # 应用入口
│   ├── requirements.txt        # Python依赖
│   ├── .env.example            # 环境变量示例
│   └── Dockerfile              # Docker配置
├── HOST轻食多Agent框架技术方案.md  # 技术方案文档
├── docker-compose.yml          # Docker Compose配置
└── README.md                   # 项目说明
```

## 快速开始

### 1. 环境准备

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- LongCat API Key（美团龙猫）

### 2. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际的API Key和数据库配置
```

### 4. 启动服务

```bash
# 使用Docker Compose（推荐）
docker-compose up -d

# 或直接运行
cd backend
python main.py
```

### 5. 访问API文档

启动后访问：http://localhost:8000/docs

## API接口

### 创建工作流
```http
POST /api/v1/workflows
Content-Type: application/json

{
    "customer_input": "设计一款适合健身人群的高蛋白低脂菜品"
}
```

### 获取工作流状态
```http
GET /api/v1/workflows/{workflow_id}
```

### 审批工作流
```http
POST /api/v1/workflows/{workflow_id}/approve
Content-Type: application/json

{
    "approved": true,
    "comments": "菜品设计符合要求",
    "reviewer": "张厨师长"
}
```

### WebSocket实时通信
```http
WS /api/v1/ws/workflows/{workflow_id}
```

## 工作流程

1. **客户输入** → 创建新工作流
2. **运营总监** → 提取关键信息
3. **营养师** → 设计营养配比
4. **研发主厨** → 设计概念卡
5. **厨师长** → 生成标准食谱卡
6. **人工审批** → 通过/驳回

## 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL + SQLAlchemy (异步)
- **缓存**: Redis
- **LLM**: LongCat（美团龙猫）
- **实时通信**: WebSocket
- **部署**: Docker + Docker Compose

## 许可证

MIT License
