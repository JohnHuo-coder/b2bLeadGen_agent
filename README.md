# B2B Lead Generation Agent

根据 **target company**（目标公司描述 / 搜索关键词）、**location**（地区）和 **company count**（公司数量），自动从 Apify 的两个数据源中挑选一个或两个来获取 candidate 公司列表。

可选传入 **industry**（LinkedIn 行业 ID code），仅在走 LinkedIn 搜索时作为额外 filter。

## 输入示例

`target company` 不是 formal industry name，而是描述你想找什么公司的搜索词：

```
AI startup
Luxury hotel
Medical device manufacturer
Precision machining company
Coworking space
```

## 数据源

| 来源 | Apify Actor | 适用场景 |
|------|-------------|----------|
| **Google Maps Scraper** | `compass/crawler-google-places` | 本地实体：酒店、coworking space、诊所、零售等 |
| **LinkedIn Company Search** | `harvestapi/linkedin-company-search` | B2B 公司：startup、manufacturer、SaaS、咨询等 |

Agent 会根据描述性关键词自动选择数据源（也支持 OpenAI 增强选择）。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 Apify API Token：

```
APIFY_API_TOKEN=apify_api_xxxxxxxx
```

可选：设置 `OPENAI_API_KEY` 让 agent 对复杂/niche 描述做更智能的数据源选择。

### 3. 启动服务

```bash
# 开发模式
python main.py

# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问 http://localhost:8000/docs 查看 Swagger UI。

### 4. 调用 API

```bash
# Health check
curl http://localhost:8000/health

# 生成 leads
curl -X POST http://localhost:8000/leads/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_company": "AI startup",
    "location": "San Francisco, USA",
    "company_count": 10,
    "industry": [4]
  }'
```

请求体字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_company` | string | 是 | 目标公司描述 / 搜索关键词 |
| `location` | string | 是 | 地区 |
| `company_count` | int | 是 | 数量（1–1000） |
| `industry` | list[int] | 否 | LinkedIn industry ID codes |

### Python API

```python
from src.agent import LeadGenAgent
from src.models import LeadRequest

agent = LeadGenAgent()
result = agent.run(LeadRequest(
    target_company="AI startup",
    location="San Francisco, USA",
    company_count=10,
    industry=[4],  # optional LinkedIn industry ID codes
))

for c in result.candidates:
    print(c.company_name, c.website, c.source)
```

## 输出字段

| 字段 | 说明 |
|------|------|
| `place_id` | Google Maps place ID 或 LinkedIn company ID |
| `company_name` | 公司名称 |
| `website` | 公司网站 |
| `source` | 数据来源 (`google_maps` / `linkedin`) |
| `address` | 地址（Google Maps） |
| `phone` | 电话（Google Maps） |
| `linkedin_url` | LinkedIn 主页（LinkedIn） |
| `employee_count` | 员工数（LinkedIn） |

## LinkedIn industry filter（可选）

默认只用 `target_company` 作为 `searchQuery` 搜索，不传 industry filter。

如果用户知道 LinkedIn industry ID，可以传入整数列表：

```json
{ "industry": [4, 13] }
```

Python / API 中 `industry` 类型为 `list[int] | None`。传给 Apify 时会转为 string array（Apify schema 要求 `"4"` 而非 `4`）。

Industry ID 对照表见 [LinkedIn Industry Codes](https://github.com/HarvestAPI/linkedin-industry-codes-v2/blob/main/linkedin_industry_code_v2_all_eng_with_header.csv)。

## 数据源选择逻辑

### Rule-based（默认，无需 OpenAI）

对 target company 描述做 **短语 + 关键词打分**：

| 信号类型 | 示例关键词 | 倾向数据源 |
|---------|-----------|-----------|
| 本地/实体 | hotel, coworking space, salon, clinic | Google Maps |
| B2B/专业 | startup, manufacturer, machining, SaaS | LinkedIn |
| 混合 | medical center, construction company | 两者都用 |

Rule-based 能 handle 大部分常见描述，例如：

- `"Luxury hotel"` → Google Maps（匹配 `luxury hotel`, `hotel`）
- `"AI startup"` → LinkedIn（匹配 `ai startup`, `startup`）
- `"Medical device manufacturer"` → LinkedIn（匹配 `medical device manufacturer`, `manufacturer`）
- `"Coworking space"` → Google Maps（匹配 `coworking space`）
- `"Precision machining company"` → LinkedIn（匹配 `precision machining`, `machining`）

对于非常 niche 或歧义大的描述，建议配置 `OPENAI_API_KEY` 启用 LLM 增强。

### LLM 增强（可选）

GPT 理解自然语言描述，选择最优数据源并微调搜索词。

## 项目结构

```
b2bleadgen_agent/
├── main.py                  # FastAPI 后端入口
├── Procfile                 # Railway / Heroku 启动命令
├── railway.toml             # Railway 部署配置
├── runtime.txt              # Python 版本
├── src/
│   ├── agent.py
│   ├── source_selector.py      # 数据源选择
│   ├── industry_mapper.py      # target company 关键词分类
│   └── tools/
│       ├── google_maps.py
│       └── linkedin.py
```

## 部署到 Railway

项目已包含 `Procfile`、`railway.toml` 和 `runtime.txt`，可直接部署。

### 1. 连接 GitHub 仓库

1. 打开 [Railway](https://railway.com/) → **New Project** → **Deploy from GitHub repo**
2. 选择 `JohnHuo-coder/b2bLeadGen_agent`
3. Railway 会自动检测 Python 项目并安装 `requirements.txt`

### 2. 配置环境变量

在 Railway 项目的 **Variables** 中添加：

| 变量 | 必填 | 说明 |
|------|------|------|
| `APIFY_API_TOKEN` | 是 | Apify API Token |
| `OPENAI_API_KEY` | 否 | LLM 增强数据源选择 |
| `OPENAI_MODEL` | 否 | 默认 `gpt-4o-mini` |

### 3. 部署

Push 到 `main` 分支后 Railway 会自动重新部署。部署完成后会分配一个 public URL，例如：

```
https://your-app.up.railway.app/health
https://your-app.up.railway.app/docs
```

### 4. 调用

```bash
curl -X POST https://your-app.up.railway.app/leads/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_company": "AI startup",
    "location": "San Francisco, USA",
    "company_count": 10
  }'
```

> **注意：** `/leads/generate` 会调用 Apify scraper，可能需要几十秒到数分钟。Railway 健康检查走 `/health`（已在 `railway.toml` 配置）。

## 费用说明

- Google Maps: ~$0.004/place + $0.007/run start
- LinkedIn: ~$0.002/short company + $0.001/run start

具体价格见 [Apify Console](https://console.apify.com/)。
