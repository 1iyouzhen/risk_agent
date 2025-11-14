# 金融人工智能风险评估系统

## 项目概述

这是一个集成了人工智能、知识图谱、RAG（检索增强生成）技术的综合金融风险评估系统。该系统通过多维度数据分析，为金融机构和企业提供智能化的风险评估、预警和决策支持服务。

>*快速体验项目可以查看use_guide.md*-->使用可视化页面交互的risk_agent！

## 项目意义

本项目的核心价值在于构建了一个端到端的智能风控解决方案，具体体现在以下几个方面：

### 技术创新性
- **多模态数据融合**：整合企业财务数据、市场指标、新闻舆情等多源异构数据，构建全面的风险评估视图
- **知识图谱驱动**：基于Neo4j图数据库构建企业关联关系网络，实现关系型风险传导分析
- **RAG增强决策**：结合检索增强生成技术，从历史案例和专业知识库中检索相似案例，提供可解释的风险建议
- **时序预测模型**：集成PatchTST、DeepLOB等金融SOTA模型，实现精准的风险趋势预测

### 业务价值
- **智能风险识别**：通过AI模型自动识别潜在风险点，替代传统人工审核，提升效率90%以上
- **动态风险监控**：实时跟踪企业风险变化，提供7×24小时不间断监控服务
- **可解释性报告**：生成包含风险因子贡献度、应对建议的结构化报告，满足监管合规要求
- **决策支持系统**：基于多维度分析结果，提供监测型、干预型、防御型分类决策建议

### 技术架构优势
- **模块化设计**：预测、解释、报告、存储、检索、决策六大模块独立解耦，便于维护和扩展
- **混合检索策略**：融合词频、向量、图关系、知识库四种检索方式，确保信息召回的全面性
- **可训练架构**：支持自定义模型训练，适配不同金融业务场景需求
- **生产级部署**：提供Web服务接口、批量处理、实时监控等多种部署形态

## 核心功能模块

### 1. 时序风险预测模块
- 基于企业历史财务指标、市场数据构建风险评估模型
- 支持规则引擎和可训练深度学习模型（PatchTST/DeepLOB）
- 输出风险评分（0-1）和不确定性估计

### 2. 解释性分析模块
- 计算各特征对风险评分的贡献度
- 提供SHAP值计算和特征重要性排序
- 生成可视化解释图表

### 3. 报告生成模块
- 自动生成结构化风险报告
- 包含主要风险、指标说明、应对建议三大板块
- 支持HTML、CSV、PDF多格式输出

### 4. 知识库与RAG检索
- 维护专业金融风险知识文档库
- 实现向量相似度检索和关键词匹配
- 支持BAAI/bge-m3和OpenAI多种嵌入模型

### 5. 图数据库集成
- Neo4j图数据库存储企业关联关系
- 支持产业链上下游、股权关系、担保关系分析
- 提供图遍历和关系推理能力

### 6. 智能决策引擎
- 基于风险评分和历史趋势制定决策策略
- 分类输出：监测型（≥0.5）、干预型（≥0.7）、防御型
- 结合LLM生成个性化风险应对建议

## 技术栈

- **后端**：Python 3.8+, FastAPI, SQLite, Neo4j
- **机器学习**：PyTorch, Scikit-learn, Pandas, NumPy
- **自然语言处理**：Transformers, Sentence-Transformers
- **图数据库**：Neo4j, NetworkX
- **数据存储**：SQLite, CSV, JSON
- **Web服务**：FastAPI, Uvicorn
- **前端**：HTML/CSS/JavaScript（报告生成）

## 安装与配置

### 环境要求
```bash
# Python 3.8+
python --version

# 安装依赖
pip install -r requirements.txt
```

### 核心依赖包
```
torch>=1.9.0
transformers>=4.20.0
sentence-transformers>=2.2.0
neo4j>=5.0.0
fastapi>=0.68.0
uvicorn>=0.15.0
pandas>=1.3.0
scikit-learn>=1.0.0
requests>=2.25.0
```

### 环境变量配置
```bash
# OpenAI API配置（可选）
export OPENAI_API_KEY="your-api-key"
export OPENAI_CHAT_MODEL="deepseek-chat"
export OPENAI_EMBED_MODEL="text-embedding-3-small"

# Neo4j数据库配置（可选）
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="your_username"
export NEO4J_PASSWORD="your_password"

# RAG检索配置
export RAG_TOP_K=3
export RAG_MIN_SCORE=0.25
export KNOWLEDGE_DIRS="knowledge_docs"

# 嵌入模型配置
export EMBED_PROVIDER="baai"  # 或 "openai"
export BAAI_MODEL="BAAI/bge-m3"
```

## 运行指南

### 1. 快速开始 - Demo模式
```bash
# 运行完整演示流程
python app.py --demo

# 指定自定义数据库
python app.py --demo --db my_risk_db.sqlite

# 使用预训练模型
python app.py --demo --model model_weights.json
```

**Demo输出**：
- 生成模拟数据（5个企业，12个月数据）
- 执行风险评估和报告生成
- 导出CSV报告：`risk_reports.csv`
- 生成HTML报告：`html_reports/`目录
- 创建SQLite数据库：`risk_agent.sqlite`

### 2. 数据生成
```bash
# 生成训练数据
python app.py --generate

# 指定输出文件和参数
python app.py --generate --input_csv my_training_data.csv --output synthetic_data.csv
```

### 3. 模型训练
```bash
# 使用默认数据训练
python app.py --train

# 使用自定义数据训练
python app.py --train --input_csv my_data.csv --model my_model.model --epochs 300 --lr 0.0002

# 直接运行训练脚本
python train.py --demo --epochs 300 --lr 0.0002
```

### 4. 批量评估
```bash
# 对数据集进行风险评估
python app.py --assess --input_csv my_data.csv

# 使用训练好的模型评估
python app.py --assess --model trained_forecaster.model --output results.csv
```

### 5. 智能查询
```bash
# 自然语言查询风险信息
python app.py --query "查询三木集团的最新风险状况"

# 结合LLM生成分析报告
python app.py --query "分析农产品行业的系统性风险" --db risk_agent.sqlite
```

### 6. 数据导出
```bash
# 导出所有评估报告
python app.py --export

# 指定输出格式和文件
python app.py --export --output comprehensive_report.csv --db custom_db.sqlite
```

### 7. 知识图谱构建
```bash
# 获取数据并构建图谱
python get_graph_data/crawler/company_info.py
python get_graph_data/crawler/market_index.py
python get_graph_data/crawler/news_sentiment.py

# 数据清洗和导入
python get_graph_data/neo4j_import/create_nodes.py
python get_graph_data/neo4j_import/create_relationships.py

# 一键导入Neo4j
python scripts/neo4j_import.py
```

### 8. Web服务启动
```bash
# 启动API服务
python src/web/server.py

# 或使用uvicorn
uvicorn src.web.server:app --host 0.0.0.0 --port 8000 --reload
```
> 注意：单独运行batch_embed.py时需要通过该项目所有代码同目录之下的终端采取python -m src.agent.batch_embed --dir ...(运行模块)
> 
**API端点**：
- `POST /api/risk/assess` - 风险评估
- `GET /api/risk/report/{entity_id}` - 获取报告
- `POST /api/risk/query` - 智能查询
- `GET /api/risk/export` - 导出数据

## 数据格式说明

### 输入数据格式（CSV）
```csv
entity_id,timestamp,amount,income,credit_score,delinquencies,market_index,label
xxx,2023-01-01,1000.50,5000,650,0,1200,0
xxx,2023-02-01,1200.75,5200,655,1,1180,0
```

### 特征说明
- `entity_id`: 企业唯一标识
- `timestamp`: 评估时间戳
- `amount`: 贷款/交易金额
- `income`: 收入水平
- `credit_score`: 信用评分（300-850）
- `delinquencies`: 违约次数
- `market_index`: 市场指数
- `label`: 风险标签（可选，用于训练）

### 输出报告格式
```
【主要风险】：
- 信用评分偏低，存在违约历史
- 市场波动较大，外部环境不利

【指标说明】：
- credit_score: 当前评分620，低于行业平均水平
- delinquencies: 近12个月违约3次，风险较高
- market_index: 市场指数下降15%，系统性风险增加

【应对建议】：
- 建议加强贷后管理，增加监控频次
- 考虑要求额外担保或抵押物
- 建议购买信用保险转移风险
```

## 扩展与定制

### 1. 模型替换
```python
# 在src/agent/models/中实现新的预测模型
class MyCustomModel(BaseRiskModel):
    def score(self, record):
        # 自定义评分逻辑
        return risk_score
```

### 2. 知识库扩展
```bash
# 添加专业文档到知识库
cp my_risk_knowledge.pdf knowledge_docs/

# 系统自动加载并建立索引
```

### 3. 图数据库扩展
```cypher
// 在Neo4j中添加自定义关系
CREATE (c1:Company {name:"公司A"})-[:SUPPLY_CHAIN]->(c2:Company {name:"公司B"})
```

### 4. 决策规则定制
```python
# 修改src/agent/decision.py中的决策逻辑
def decide(risk_score, history):
    # 自定义决策规则
    if risk_score > 0.8:
        return "IMMEDIATE_INTERVENTION"
    # ...
```

## 性能优化

### 1. 大规模数据处理
- 使用批量处理替代单条记录处理
- 启用多线程/多进程并行计算
- 考虑使用分布式计算框架（如Dask）

### 2. 模型推理加速
- 使用模型量化技术减少计算量
- 部署GPU加速深度学习模型
- 实现模型缓存避免重复计算

### 3. 检索性能优化
- 构建FAISS向量索引加速相似度搜索
- 实现分层检索策略（粗排+精排）
- 使用Redis缓存热点查询结果

### 4. 存储优化
- 对SQLite数据库建立合适索引
- 定期归档历史数据
- 考虑使用列式存储优化分析查询

## 监控与维护

### 1. 模型监控
- 跟踪模型预测准确率变化
- 监控特征分布漂移（PSI指标）
- 设置模型性能告警阈值

### 2. 数据质量监控
- 检查数据完整性和一致性
- 监控异常值和缺失值比例
- 建立数据质量评分体系

### 3. 系统性能监控
- 监控API响应时间和吞吐量
- 跟踪数据库查询性能
- 设置系统资源使用率告警

## 安全与合规

### 1. 数据安全
- 敏感数据加密存储和传输
- 实现数据访问权限控制
- 建立数据脱敏机制

### 2. 模型合规
- 确保模型可解释性满足监管要求
- 建立模型审计日志
- 实现模型版本管理和回滚

### 3. 隐私保护
- 实现差分隐私保护
- 支持数据匿名化处理
- 建立数据删除机制

## 故障排除

### 常见问题
1. **Neo4j连接失败**：检查服务状态和认证配置
2. **模型训练失败**：验证数据格式和特征完整性
3. **内存不足**：减少批处理大小或使用数据分块
4. **检索结果为空**：检查知识库配置和索引状态

### 调试工具
```bash
# 查看系统日志
tail -f logs/app.log

# 检查数据库连接
python -c "from src.agent.neo4j_client import Neo4jClient; print(Neo4jClient().available())"

# 验证模型加载
python -c "from src.agent.models.risk_forecast import RiskForecaster; print(RiskForecaster().score({'amount':1000, 'income':5000, 'credit_score':650, 'delinquencies':0, 'market_index':1200}))"
```

## 项目结构

```
risk_agent/
├── app.py                    # 主程序入口
├── train.py                  # 模型训练脚本
├── src/
│   ├── agent/                # 核心智能体模块
│   │   ├── models/          # 预测模型
│   │   ├── config.py        # 配置管理
│   │   ├── rag.py           # RAG检索
│   │   ├── knowledge_base.py # 知识库
│   │   ├── graph_client.py  # 图数据库客户端
│   │   ├── neo4j_client.py  # Neo4j集成
│   │   ├── llm_client.py    # 大模型客户端
│   │   ├── storage.py       # 数据存储
│   │   ├── reporting.py     # 报告生成
│   │   └── decision.py      # 决策引擎
│   └── web/
│       └── server.py        # Web服务
├── get_graph_data/          # 知识图谱构建工具
├── knowledge_docs/          # 专业知识文档
├── graph_data/              # 图数据文件
├── html_reports/            # 生成的HTML报告
├── scripts/                 # 实用脚本
└── requirements.txt         # 依赖包列表
```

## 更新日志

### v2.0 (当前版本)
- ✅ 集成PatchTST时序预测模型
- ✅ 实现RAG检索生成
- ✅ 添加Neo4j知识图谱支持
- ✅ 支持OpenAI/DeepSeek大模型
- ✅ 完善Web API服务
- ✅ 优化报告生成和导出功能

### 开发计划
- 🚧 集成更多金融SOTA模型（DeepAR、TFT）
- 🚧 开发Web前端界面
- 🚧 支持实时流数据处理
- 🚧 添加模型自动更新机制
- 🚧 集成更多外部数据源
- 🚧 加快RAG的检索速度

## 支持与贡献

如有问题或建议，请通过以下方式联系：
- 提交Issue报告
- 发送邮件至项目维护者
- 参与代码贡献和文档完善

## 许可证

本项目采用MIT开源许可证，详见LICENSE文件。

---

**注意**：本项目为金融人工智能应用，请在生产环境部署前进行充分的测试和验证，确保符合相关监管要求和业务规范。
