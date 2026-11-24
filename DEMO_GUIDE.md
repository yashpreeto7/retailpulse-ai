# RetailPulse AI — Demo Video Walkthrough & Script
**Application:** RetailPulse AI — AI Data Analyst & Business Intelligence Agent  
**Candidate Name:** John Doe  
**Target Duration:** 3 to 5 minutes  

---

## Demo Video Flowchart
```
1. Startup & Bootstrapping
   └─ Run `python run.py` (or click `start.bat`)
   └─ Automatic ETL verification, SQLite loading (1,008 orders, 161 customers, 25 products)
   └─ Launch Web Application: http://127.0.0.1:8000

2. Dashboard Overview & Real-Time KPIs
   └─ Showcase 4 Executive KPI Cards: Total Revenue ($357,500.76), Total Orders (1,008), AOV ($369.70), Customers (161)
   └─ Review Live Synced Charts: Monthly Revenue Trend, Category Breakdown, Top Products, Customer Activity

3. Natural Language AI Question & Tool Execution
   └─ Question: "What were the top 5 products by revenue?"
   └─ Show Tool Execution Trace: `get_top_products(metric='revenue', limit=5)` executed in <5ms
   └─ Review grounded response with exact dollar amounts and units sold

4. Dynamic Chart Generation
   └─ Question: "Show monthly revenue as a chart."
   └─ Show interactive Line Chart rendered dynamically inside the chat bubble from live SQLite data

5. Multi-Step Root Cause Analysis (Flagship Feature)
   └─ Question: "Why did revenue decline last month?"
   └─ Inspect Multi-Step Execution:
      • Tool 1: `diagnose_revenue_decline()`
      • Tool 2: `generate_chart()`
   └─ Explain the 4-part diagnosis:
      1. Volume vs AOV (-26.9% orders drop vs -18.9% AOV drop)
      2. Category Variance (Electronics fell by -$7,229.82)
      3. Product Drill-Down (Headphones & Monitor stockouts)
      4. Customer Cohorts (Repeat buyer purchase drop of 24%)
   └─ Highlight actionable strategic takeaway

6. Inactive Customer Analytics
   └─ Question: "Which customers have not purchased recently?"
   └─ Show table of dormant customers (>90 days) with last purchase date and lifetime spend

7. Unsupported & Out-of-Domain Question Handling (Guardrails)
   └─ Question: "What is the capital of France?" or "What is the weather in Paris?"
   └─ Demonstrate polite refusal and redirection to retail analytics without hallucination

8. Safe SQL Terminal & ETL Data Quality Audit
   └─ Open System Tools drawer at bottom
   └─ Review ETL Quality Audit: 4 duplicates removed, 2 missing values repaired, 100% clean rate
   └─ Run safe `SELECT name, price FROM products LIMIT 5`
   └─ Show security blocking of `DROP TABLE customers` with 403 Forbidden
```

---

## Detailed Step-by-Step Recording Script

### Scene 1: Startup & Environment Setup (0:00 - 0:35)
- **Visual:** Open terminal / PowerShell window.
- **Action:** Run `python run.py`.
- **Narration:**
  > "Hello everyone. Today I'm presenting RetailPulse AI, an enterprise-grade AI Data Analyst and Business Intelligence Agent built for e-commerce companies.
  > On startup, the system automatically checks for the SQLite database. If not found, it runs the data ingestion and cleaning pipeline, handling duplicates, missing values, and type conversions before starting the FastAPI server on port 8000."

### Scene 2: Executive Dashboard & KPIs (0:35 - 1:10)
- **Visual:** Switch browser to `http://127.0.0.1:8000`.
- **Action:** Point out KPI summary cards and the 4 visual charts on the right.
- **Narration:**
  > "Here is the RetailPulse executive dashboard. Across the top, our KPI cards show real-time metrics computed directly from our transactional database: over $357,000 in gross revenue, 1,008 orders, an Average Order Value of $369.70, and 161 customers.
  > On the right, we have interactive visualizations powered by Chart.js displaying monthly trends, category shares, top products, and customer retention cohorts."

### Scene 3: Natural Language Query & Tool Execution (1:10 - 1:50)
- **Visual:** Click prompt chip: `What were the top 5 products by revenue?`
- **Action:** Watch message stream, show Tool Execution Trace.
- **Narration:**
  > "Let's ask the AI Analyst a standard business question: 'What were the top 5 products by revenue?'
  > Notice the Tool Execution card above the answer: the agent autonomously selected and executed `get_top_products()`, querying the database in under 5 milliseconds. Every number in this response—such as the Pro 4K Monitor at $54,449.01—is strictly grounded in the database without any numerical hallucination."

### Scene 4: Dynamic Chart Generation (1:50 - 2:30)
- **Visual:** Click prompt chip: `Show monthly revenue as a chart.`
- **Action:** Scroll to view the dynamically generated interactive line chart rendered inline.
- **Narration:**
  > "Now, let's request dynamic data visualization: 'Show monthly revenue as a chart.'
  > The agent executes `get_sales_metrics()` and `generate_chart()`, dynamically creating a line chart specification with exact historical monthly revenue points rendered directly in the chat interface."

### Scene 5: Multi-Step Root Cause Analysis (2:30 - 3:40)
- **Visual:** Click highlighted prompt: `Why did revenue decline last month?`
- **Action:** Walk through the 5-step structured diagnostic response.
- **Narration:**
  > "Next is our flagship multi-step capability: 'Why did revenue decline last month?'
  > This is a complex business question that cannot be answered with a simple table lookup. The agent invokes `diagnose_revenue_decline()`, which executes a multi-dimensional decomposition:
  > First, it decomposes revenue into volume versus basket size: orders fell by 26.9% while AOV dropped by 18.9%.
  > Second, category variance: the decline was concentrated in Electronics, which plummeted by $7,229.82.
  > Third, product drill-down: stockouts in Noise-Cancelling Headphones and Gaming Monitors caused the drop.
  > Fourth, customer cohorts: repeat customer purchases collapsed by 24%.
  > Finally, it provides an actionable commercial recommendation for inventory replenishment and win-back marketing."

### Scene 6: Inactive Customers & Guardrails (3:40 - 4:25)
- **Visual:** Ask `Which customers have not purchased recently?`, followed by `What is the weather in Paris?`.
- **Narration:**
  > "For customer analytics, asking 'Which customers have not purchased recently?' identifies inactive customers who haven't ordered in 90 days, along with their days dormant and historical spend.
  > Now, what happens if a user asks an unsupported question, like 'What is the weather in Paris?'
  > Instead of hallucinating, our grounding guardrail detects that the query is out-of-domain and politely redirects the user to valid retail inquiries."

### Scene 7: System Tools, Safe SQL & Conclusion (4:25 - 5:00)
- **Visual:** Expand bottom System Tools accordion.
- **Action:** Show ETL cleaning stats (duplicates cleaned, missing values fixed). Test `SELECT name, price FROM products LIMIT 5` and then type `DROP TABLE customers` to show security rejection.
- **Narration:**
  > "Finally, opening our System Tools reveals our ETL data quality audit, documenting records loaded, duplicates cleaned, and missing values fixed. Our Safe SQL terminal allows ad-hoc queries, and our SQL Guard rejects malicious commands like DROP TABLE with a 403 Forbidden.
  > RetailPulse AI delivers reliable, grounded, production-grade business intelligence. Thank you!"
