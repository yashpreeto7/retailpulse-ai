# RetailPulse AI — Enterprise AI Data Analyst & BI Agent

[![Python](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13%20|%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed%20(100%25)-brightgreen.svg)]()
[![Model](https://img.shields.io/badge/LLM-Alibaba%20Qwen%202.5%207B%20(Ollama)-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **Technical Assessment Submission for DDL Labs — Role: AI / Python / LLM Engineer**  
> Candidate: **Yashpreet**  
> Submission Date: **November 2026**  

RetailPulse AI is a production-grade, zero-hallucination AI Data Analyst and Business Intelligence Agent that allows business stakeholders to interact with complex e-commerce data using natural language. It combines deterministic data engineering, controlled tool calling, multi-step root cause diagnostic engines, and dynamic visualization generation.

---

## 📋 Submission Details

| Field | Details |
| :--- | :--- |
| **Candidate Name** | Yashpreet |
| **Role Applied** | AI / Python / LLM Engineer (DDL Labs) |
| **GitHub Repository** | [https://github.com/yashpreeto7/retailpulse-ai](https://github.com/yashpreeto7/retailpulse-ai) |
| **Demo Video** | [Watch Demo Video (Google Drive)](https://drive.google.com/file/d/17Z_S5TknI4iYarwH2-5HYFcsG4tURZ1V/view?usp=sharing) (Script: [DEMO_GUIDE.md](./DEMO_GUIDE.md)) |
| **Executive Summary** | [SOLUTION_EXECUTIVE_SUMMARY.md](./SOLUTION_EXECUTIVE_SUMMARY.md) (500 Words) |
| **LLM Model & Provider** | **Primary:** Alibaba Qwen 2.5 7B (`qwen2.5:7b`) via local Ollama Grounded RAG<br>**Secondary Cloud:** Google Gemini (`gemini-2.5-flash`) & OpenAI (`gpt-4o`)<br>**Offline Default:** RetailPulse Grounded Deterministic Semantic Engine (Zero-API-key local reproducibility) |
| **Database** | SQLite Relational Database with SQLAlchemy 2.0 ORM & Analytical Indexing |
| **Frontend & Visualization** | Obsidian & Electric Cobalt UI, Three.js WebGL 3D Matrix, Chart.js Telemetry |
| **Main Technologies** | Python 3.14, FastAPI, Ollama, Three.js, Chart.js, SQLAlchemy, Pydantic v2, Pandas, HTML5/CSS3 |

---

## 🌟 Key Capabilities & Features

### 1. Robust Data Ingestion & Cleaning Pipeline (ETL)
- **Relational Schema**: 5 core entities (`customers`, `categories`, `products`, `orders`, `order_items`) with foreign key constraints and compound indexes.
- **Automated Data Cleaning**:
  - Deduplicates customer IDs, products, orders, and order items.
  - Imputes missing emails with fallback formats.
  - Recalculates missing or zero order item subtotals (`quantity * unit_price`).
  - Filters out orphan foreign key references.
  - Emits an auditable **Data Quality Report** (`clean_pct`, duplicates removed, missing values handled).

### 2. Core Business Analytics
- **Sales Analytics**: Gross revenue, completed orders, cancellations, Average Order Value (AOV), monthly revenue time series, Month-over-Month (MoM) growth, and category revenue distribution.
- **Customer Analytics**: Total customer base, new signups (last 90d), repeat customers, repeat rate (%), inactive customers (>90d dormant), and top customers ranked by lifetime spend.
- **Product Analytics**: Top products by revenue, top products by volume (units sold), and low-performing stagnant inventory tying up capital.

### 3. Controlled Agent & Tool Calling Architecture
- The agent does **not** rely on unconstrained text generation. It executes controlled tools via strict schemas:
  - `get_kpi_summary()`
  - `get_sales_metrics(metric_type)`
  - `get_top_products(metric, limit)`
  - `get_customer_metrics(segment, limit)`
  - `diagnose_revenue_decline(target_month, baseline_month)`
  - `generate_chart(metric, chart_type, title)`
  - `query_database(sql)`

### 4. Multi-Step Root Cause Diagnostic Engine
Solves complex business questions such as: **"Why did revenue decline last month?"**
- **Step 1 (Macro Decomposition)**: Decomposes $\Delta \text{Revenue}$ into Volume effect ($\Delta$ Orders: -26.9%) vs Basket size effect ($\Delta$ AOV: -18.9%).
- **Step 2 (Category Variance)**: Identifies the specific category responsible for the loss (**Electronics** fell by -$7,229.82).
- **Step 3 (Product SKU Drill-Down)**: Pinpoints out-of-stock items (*Ultra Wireless Headphones* and *Pro 4K Monitor*).
- **Step 4 (Customer Cohort Analysis)**: Reveals a 24% drop in repeat buyer orders.
- **Step 5 (Commercial Actionable Takeaways)**: Synthesizes operational inventory and marketing recommendations.

### 5. Alibaba Qwen 2.5 7B Grounded RAG Pipeline
- **Local Ollama Integration**: Communicates directly with Alibaba's `qwen2.5:7b` model over local REST APIs (`http://127.0.0.1:11434`).
- **Grounded Context Injection**: Injects schema metadata, verified SQLite aggregations, and business knowledge corpora into the LLM prompt.
- **Strict Anti-Hallucination**: The LLM is constrained to only synthesize numbers present in the grounded context, combining natural conversational fluency with mathematical certainty.

### 6. Interactive 3D WebGL Revenue Matrix & Obsidian Studio
- **Three.js Spatial Engine**: 3D category pillars rendered in real-time WebGL with dynamic heights reflecting revenue magnitude.
- **Interactive Raycasting HUD**: Hover tooltips show category revenue, growth percentages, and SKU volume.
- **Camera Viewport Presets**: Instant transitions between Isometric (`ISO`), Top-down (`TOP`), and Front-elevation (`FRONT`) view modes.
- **Obsidian & Electric Cobalt Styling**: Clean architectural design with micro-sparklines, Chart.js telemetry, and an integrated safe SQL workbench.

### 7. Dynamic Chart Generation
- Users can ask: *"Show monthly revenue as a chart"* or *"Plot top products"*.
- The system dynamically extracts live SQL data, produces JSON chart configurations, and renders interactive Chart.js visualizations directly inside chat bubbles and on dashboard panels.

### 8. Grounding Engine & SQL Security Guard
- **Zero Hallucination**: AI numerical responses are cross-referenced against actual tool datasets.
- **Graceful Rejection**: General/unsupported inquiries (e.g. *"What is the weather in Paris?"*) are politely rejected and redirected to retail queries.
- **SQL Guardrails**: AST/regex filters prevent SQL injection and forbid mutation commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`), enforcing read-only execution with mandatory `LIMIT 50`.

---

## 🏗️ Architecture & Project Structure

```
NEW PROJECT/
├── data/
│   ├── raw/                       # Source CSVs with intentional dirty records
│   ├── data_quality_report.json   # ETL audit output
│   └── retailpulse.db             # Relational SQLite database
├── retailpulse/
│   ├── __init__.py
│   ├── config.py                  # Pydantic Settings & environment config
│   ├── core/
│   │   ├── database.py            # SQLAlchemy engine, session, raw SQL runner
│   │   └── logger.py              # Application logging
│   ├── models/
│   │   ├── db_models.py           # SQLAlchemy ORM models (5 entities)
│   │   └── schemas.py             # Pydantic v2 schemas for API & Agent
│   ├── data/
│   │   ├── generator.py           # Synthetic dataset generator with business patterns
│   │   ├── cleaner.py             # Data cleaning, deduplication, imputation
│   │   └── ingestion.py           # Full ETL pipeline orchestration
│   ├── analytics/
│   │   ├── sales.py               # Sales, monthly trends, AOV, categories
│   │   ├── customers.py           # Cohorts, repeat buyers, churned/inactive
│   │   ├── products.py            # Top revenue, top volume, stagnant inventory
│   │   └── root_cause.py          # 5-step revenue decline diagnostic engine
│   ├── agent/
│   │   ├── tools.py               # Controlled tool registry & definitions
│   │   ├── sql_guard.py           # Read-only SQL validator & injection protection
│   │   ├── grounding.py           # Grounding verifier & domain guardrails
│   │   └── orchestrator.py        # Multi-provider LLM & deterministic semantic router
│   ├── api/
│   │   ├── app.py                 # FastAPI application, CORS, static mounting
│   │   └── routes.py              # REST API endpoints (/api/chat, /api/kpis, etc.)
│   └── static/
│       ├── index.html             # Glassmorphic BI dashboard
│       ├── styles.css             # Modern typography, responsive layout
│       └── app.js                 # Chart.js integration, chat streaming, SQL terminal
├── tests/
│   ├── test_data_cleaner.py       # Deduplication, missing value imputation
│   ├── test_analytics.py          # Mathematical validation of business metrics
│   ├── test_root_cause.py         # Multi-step diagnostic logic validation
│   ├── test_sql_guard.py          # SQL injection and DDL blocking tests
│   ├── test_api.py                # FastAPI endpoints & status code verification
│   └── test_agent_grounding.py    # AI golden questions tested against DB truth
├── SOLUTION_EXECUTIVE_SUMMARY.md  # 500-word Executive Summary
├── DEMO_GUIDE.md                  # Demo video script & presentation flow
├── requirements.txt               # Python package dependencies
├── run.py                         # One-click startup script
├── start.bat                      # Windows launcher
├── .env.example                   # Environment configuration template
└── README.md                      # Comprehensive documentation
```

---

## ⚡ Quickstart & Setup Instructions

### 1. Clone & Set Up Environment
```bash
git clone <repository_url>
cd <repository_folder>

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
The application works **100% out of the box** without API keys using the built-in Grounded Semantic Engine.  
If you wish to test with live cloud LLMs, copy `.env.example` to `.env` and add your API key:
```bash
cp .env.example .env
# Set GEMINI_API_KEY=your_key or OPENAI_API_KEY=your_key
```

### 3. Launch the Application
Run one command:
```bash
python run.py
```
*(On Windows, you can also double-click `start.bat`)*

The server will automatically bootstrap the database and start at:
- **Interactive Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running Automated Tests

Run the full automated test suite (28 tests covering data processing, business math, forecasting, multi-turn memory, SQL safety, API endpoints, and AI golden queries):

```bash
python -m pytest -v
```

Expected output:
```
============================= test session starts =============================
collected 28 items

tests/test_agent_grounding.py::test_ai_golden_question_top_products PASSED
tests/test_agent_grounding.py::test_ai_golden_question_monthly_revenue PASSED
tests/test_agent_grounding.py::test_ai_golden_question_top_category PASSED
tests/test_agent_grounding.py::test_ai_golden_question_multi_step_revenue_decline PASSED
tests/test_agent_grounding.py::test_ai_golden_question_inactive_customers PASSED
tests/test_agent_grounding.py::test_ai_unsupported_out_of_domain_question PASSED
tests/test_analytics.py::test_sales_kpi_summary PASSED
tests/test_analytics.py::test_monthly_revenue_analytics PASSED
tests/test_analytics.py::test_category_revenue_shares PASSED
tests/test_analytics.py::test_top_products_ranking PASSED
tests/test_analytics.py::test_customer_segmentation PASSED
tests/test_api.py::test_api_health PASSED
tests/test_api.py::test_api_kpis PASSED
tests/test_api.py::test_api_monthly_sales PASSED
tests/test_api.py::test_api_top_products PASSED
tests/test_api.py::test_api_charts PASSED
tests/test_api.py::test_api_chat_endpoint PASSED
tests/test_api.py::test_api_sql_security PASSED
tests/test_api.py::test_api_data_quality PASSED
tests/test_data_cleaner.py::test_cleaner_deduplication PASSED
tests/test_data_cleaner.py::test_cleaner_missing_values_and_subtotal_repair PASSED
tests/test_data_cleaner.py::test_data_quality_report PASSED
tests/test_elevations.py::test_predictive_sales_forecasting PASSED
tests/test_elevations.py::test_multi_turn_conversational_memory PASSED
tests/test_elevations.py::test_live_server_endpoints PASSED
tests/test_root_cause.py::test_multi_step_revenue_decline_diagnosis PASSED
tests/test_sql_guard.py::test_safe_select_queries_pass PASSED
tests/test_sql_guard.py::test_malicious_sql_rejections PASSED

======================== 28 passed ========================
```

---

## 🎯 Verification of Core AI Questions

| Question | Tool Selected | Ground Truth Verification |
| :--- | :--- | :--- |
| **"What were the top 5 products by revenue?"** | `get_top_products(metric='revenue', limit=5)` | Top SKU: *Pro 4K Gaming & Workstation Monitor* ($54,449.01 across 99 units). |
| **"Show monthly revenue as a chart."** | `get_sales_metrics(metric_type='monthly')` + `generate_chart()` | Generates interactive line chart with historical monthly points. |
| **"Which category generated the most revenue?"** | `get_sales_metrics(metric_type='category')` | Identifies *Electronics* as #1 at $111,685.61 (30.9% share). |
| **"Why did revenue decline last month?"** | `diagnose_revenue_decline()` + `generate_chart()` | 5-step breakdown: -$16,248.49 (-40.7%) drop driven by -$7,229.82 loss in Electronics, stockouts, and -24% repeat buyer drop. |
| **"Which customers have not purchased recently?"** | `get_customer_metrics(segment='inactive', limit=10)` | Returns 48 inactive customers (>90 days without order) with last order dates and spend. |
| **"What is the capital of France?"** | `GroundingEngine.is_in_domain()` | Rejection guardrail triggered; politely redirects to retail analytics. |

---

## ⚠️ Known Limitations & Future Roadmap

1. **Dialect Support**: Currently optimized for SQLite. For enterprise production workloads, adding PostgreSQL/DuckDB drivers via SQLAlchemy dial-in is architecturally straightforward.
2. **Context Window Persistence**: The current chat studio maintains session state in the browser client. Integrating a persistent conversation store (Redis or SQLite session table) would enable multi-day conversation recall.
3. **Automated Alerting**: Future extensions can schedule cron jobs (e.g., daily anomaly detection triggers when daily sales drop >2 standard deviations).

---

## 📄 License
This project is submitted under the MIT License for technical evaluation purposes.
