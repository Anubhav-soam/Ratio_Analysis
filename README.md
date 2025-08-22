# 📊 Financial Ratio Analyzer

A **Streamlit web app** to analyze financial statements of companies and compute **key financial ratios** using data from **Yahoo Finance** (`yfinance` library).  

This project is useful for **finance students, analysts, and investors** who want quick access to financial ratios, trends, and visualizations — without manually processing balance sheets.

---

## 🚀 Features

### 📑 Financial Statements
- View **Income Statement, Balance Sheet, and Cash Flow** (up to 5 years).
- Data is automatically pulled from **Yahoo Finance**.
- Tabular view with option to download.

---

### 📊 Ratio Computations

#### ✅ Profitability Ratios
- **Gross Margin** = Gross Profit ÷ Revenue  
- **EBIT Margin** = EBIT ÷ Revenue  
- **Net Profit Margin** = Net Income ÷ Revenue  
- **ROA** (Return on Assets) = Net Income ÷ Average Assets  
- **ROE** (Return on Equity) = Net Income ÷ Average Equity  
- **Asset Turnover** = Revenue ÷ Average Assets  

![Profitability](https://raw.githubusercontent.com/Anubhav-soam/Ratio_Analysis/main/assets/download.png)

---

#### 💧 Liquidity Ratios
- **Current Ratio** = Current Assets ÷ Current Liabilities  
- **Quick Ratio** = (Current Assets - Inventory) ÷ Current Liabilities  
- **Cash Ratio** = (Cash + Short-term Investments) ÷ Current Liabilities  
- **Working Capital (₹)** = Current Assets - Current Liabilities  

![Liquidity](https://raw.githubusercontent.com/Anubhav-soam/Ratio_Analysis/main/assets/download1.png)

---

#### ⚖️ Leverage & Coverage Ratios
- **Debt to Assets** = Total Debt ÷ Total Assets  
- **Debt to Equity** = Total Debt ÷ Equity  
- **Interest Coverage** = EBIT ÷ |Interest Expense|  

![Leverage](https://raw.githubusercontent.com/Anubhav-soam/Ratio_Analysis/main/assets/download2.png)

---

#### ⚡ Efficiency / Activity Ratios
- **Inventory Turnover** = COGS ÷ Average Inventory  
- **Receivables Turnover** = Revenue ÷ Average Receivables  
- **Payables Turnover** = COGS ÷ Average Payables  
- **DIO (Days Inventory Outstanding)** = 365 ÷ Inventory Turnover  
- **DSO (Days Sales Outstanding)** = 365 ÷ Receivables Turnover  
- **DPO (Days Payables Outstanding)** = 365 ÷ Payables Turnover  
- **Cash Conversion Cycle (CCC)** = DIO + DSO - DPO  

![Efficiency](https://raw.githubusercontent.com/Anubhav-soam/Ratio_Analysis/main/assets/download3.png)

---

#### 📈 Market Ratios (Optional)
- **P/E Ratio** = Price ÷ EPS  
- **P/B Ratio** = Price ÷ Book Value per Share  
- **Dividend Yield** = Dividends ÷ Price  
- **Market Cap** = Price × Shares Outstanding  

![Market Ratios](https://raw.githubusercontent.com/Anubhav-soam/Ratio_Analysis/main/assets/download4.png)

---

### 📉 Interactive Charts
- Line charts for trends (margins, liquidity, leverage, CCC).  
- Year-range slider to filter data.  

---

### 📥 Download Results
- Export **all ratios** into a CSV file for offline use.  

---

## ⚙️ How It Works (Code Explanation)

### 1. 📡 Data Fetching
- Uses [`yfinance`](https://pypi.org/project/yfinance/) to pull financial data.  
- Three statements are fetched:  
  - `t.financials` → Income Statement  
  - `t.balance_sheet` → Balance Sheet  
  - `t.cash_flow` → Cash Flow  

### 2. 🧹 Data Normalization
- Raw indices (dates) are converted to **fiscal years**.  
- Duplicate years (if reported multiple times) → only the latest kept.  

### 3. 💾 Caching
- **`st.cache_resource`** → caches the `yfinance.Ticker` object.  
- **`st.cache_data`** → caches processed DataFrames for 30 minutes.  
- Improves performance and reduces API calls.  

### 4. 🧮 Ratio Computation
- Ratios are calculated using helper functions:  
  - `safe_div()` → avoids division errors (NaN, inf).  
  - `avg_series()` → computes average balances (important for ROA, ROE).  
- Computed across aligned **years** from multiple statements.  

### 5. 🎨 UI (Streamlit)
- Sidebar inputs: ticker, year range, decimals.  
- Tabs for each ratio category.  
- DataFrames displayed with formatting (%, ratios, integers).  
- Charts plotted using `st.line_chart`.  
- CSV download button for results.  

---
