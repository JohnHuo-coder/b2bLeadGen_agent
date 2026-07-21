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

### 3. 运行

```bash
# AI startup → LinkedIn
python main.py -t "AI startup" -l "San Francisco, USA" -n 10

# Luxury hotel → Google Maps
python main.py -t "Luxury hotel" -l "New York, USA" -n 20

# Medical device manufacturer → LinkedIn
python main.py -t "Medical device manufacturer" -l "Boston, USA" -n 15

# Coworking space → Google Maps
python main.py -t "Coworking space" -l "Austin, USA" -n 10

# 带 LinkedIn 行业 ID filter（可选，直接传 code）
python main.py -t "AI startup" -l "San Francisco, USA" --industry "4" -n 10
python main.py -t "startup" -l "San Francisco" --industry "4,13" -n 10

# JSON 输出
python main.py -t "Precision machining company" -l "Detroit, USA" -n 10 --json
```

### Python API

```python
from src.agent import LeadGenAgent
from src.models import LeadRequest

agent = LeadGenAgent()
result = agent.run(LeadRequest(
    target_company="AI startup",
    location="San Francisco, USA",
    company_count=10,
    industry="4",  # optional LinkedIn industry ID code
))

for c in result.candidates:
    print(c.company_name, c.website, c.source)
```

## 输出字段

| 字段 | 说明 |
|------|------|
| `company_name` | 公司名称 |
| `website` | 公司网站 |
| `source` | 数据来源 (`google_maps` / `linkedin`) |
| `address` | 地址（Google Maps） |
| `phone` | 电话（Google Maps） |
| `linkedin_url` | LinkedIn 主页（LinkedIn） |
| `employee_count` | 员工数（LinkedIn） |

## LinkedIn industry filter（可选）

默认只用 `target_company` 作为 `searchQuery` 搜索，不传 industry filter。

如果用户知道 LinkedIn industry ID，可以直接传入 code：

```bash
python main.py -t "startup" -l "San Francisco" --industry "4" -n 10
python main.py -t "startup" -l "San Francisco" --industry "4,13" -n 10
```

`--industry` 的值会原样传给 LinkedIn scraper 的 `industryIds` 参数，支持逗号分隔多个 ID。

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
├── main.py
├── src/
│   ├── agent.py
│   ├── source_selector.py      # 数据源选择
│   ├── industry_mapper.py      # target company 关键词分类
│   └── tools/
│       ├── google_maps.py
│       └── linkedin.py
```

## 费用说明

- Google Maps: ~$0.004/place + $0.007/run start
- LinkedIn: ~$0.002/short company + $0.001/run start

具体价格见 [Apify Console](https://console.apify.com/)。
