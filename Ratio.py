import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Financial Ratio Analyzer", page_icon="📊", layout="wide")

# ========================= Caching & Helpers =========================
# Cache the Ticker object as a resource (unpicklable). Keep data outputs cacheable with cache_data.
@st.cache_resource
def get_ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker)

@st.cache_data(ttl=60 * 30)
def load_statements(ticker: str):
    t = get_ticker(ticker)

    inc = t.financials.transpose().copy()
    bal = t.balance_sheet.transpose().copy()
    cfs = t.cash_flow.transpose().copy()

    # normalize indices to year (int)
    def norm(df: pd.DataFrame):
        if df is None or df.empty:
            return pd.DataFrame()
        idx = pd.to_datetime(df.index, errors='coerce')
        df = df.copy()
        df.index = idx
        df = df[~df.index.isna()]
        df["Year"] = df.index.year
        # keep most recent duplicate year
        df = (
            df.sort_index()
              .drop_duplicates(subset=["Year"], keep="last")
              .set_index("Year")
              .sort_index()
        )
        return df

    return norm(inc), norm(bal), norm(cfs)


def sget(df: pd.DataFrame, col: str) -> pd.Series:
    if df is None or df.empty or col not in df.columns:
        return pd.Series(dtype=float)
    s = pd.to_numeric(df[col], errors='coerce')
    s.index.name = 'Year'
    return s.dropna().astype(float)


def avg_series(current: pd.Series) -> pd.Series:
    prev = current.shift(1)
    return (current + prev) / 2.0


def safe_div(n, d) -> pd.Series:
    """Division that gracefully handles Series/scalar combos and infs.
    Broadcasts scalars to the other's index, returns NaN for /0.
    """
    # Convert to Series with aligned index when one of them is a Series
    if isinstance(n, pd.Series) and isinstance(d, pd.Series):
        out = n / d
    elif isinstance(n, pd.Series):  # d is scalar
        out = n / d
    elif isinstance(d, pd.Series):  # n is scalar -> broadcast n
        out = pd.Series(n, index=d.index) / d
    else:  # both scalars -> return a 1-length series
        out = pd.Series([np.nan]) if (d == 0 or d is None) else pd.Series([n / d])
    return out.replace([np.inf, -np.inf], np.nan)


# ========================= Ratio Computation =========================

def compute_ratios(inc: pd.DataFrame, bal: pd.DataFrame):
    # Income statement
    rev = sget(inc, 'Total Revenue')
    ni = sget(inc, 'Net Income')
    ebit = sget(inc, 'EBIT')
    int_exp = sget(inc, 'Interest Expense')
    cogs = sget(inc, 'Cost Of Revenue')
    gross_profit = sget(inc, 'Gross Profit')

    # Balance sheet
    cur_assets = sget(bal, 'Current Assets')
    cur_liab = sget(bal, 'Current Liabilities')
    cash_sti = sget(bal, 'Cash Cash Equivalents And Short Term Investments')
    inventory = sget(bal, 'Inventory')
    receivables = sget(bal, 'Accounts Receivable')
    if receivables.empty:
        receivables = sget(bal, 'Net Receivables')
    payables = sget(bal, 'Accounts Payable')
    total_assets = sget(bal, 'Total Assets')
    total_debt = sget(bal, 'Total Debt')
    total_equity = sget(bal, 'Total Equity Gross Minority Interest')
    if total_equity.empty and 'Total Equity' in bal.columns:
        total_equity = sget(bal, 'Total Equity')
    if total_equity.empty and 'Total Stockholder Equity' in bal.columns:
        total_equity = sget(bal, 'Total Stockholder Equity')

    # Common aligned index across statements
    years = sorted(
        set(rev.index) | set(ni.index) | set(ebit.index) |
        set(cur_assets.index) | set(cur_liab.index) |
        set(total_assets.index) | set(total_equity.index)
    )

    def align(s):
        return s.reindex(years)

    rev, ni, ebit, int_exp, cogs, gross_profit = map(align, [rev, ni, ebit, int_exp, cogs, gross_profit])
    cur_assets, cur_liab, cash_sti, inventory, receivables, payables, total_assets, total_debt, total_equity = map(
        align, [cur_assets, cur_liab, cash_sti, inventory, receivables, payables, total_assets, total_debt, total_equity]
    )

    avg_assets = avg_series(total_assets)
    avg_inventory = avg_series(inventory)
    avg_receivables = avg_series(receivables)
    avg_payables = avg_series(payables)
    avg_equity = avg_series(total_equity)

    # Profitability
    profitability = pd.DataFrame({
        'Gross Margin': safe_div(gross_profit, rev),
        'EBIT Margin': safe_div(ebit, rev),
        'Net Profit Margin': safe_div(ni, rev),
        'ROA': safe_div(ni, avg_assets),
        'ROE': safe_div(ni, avg_equity),  # average equity for ROE
        'Asset Turnover': safe_div(rev, avg_assets),
    }, index=years)

    # Liquidity
    quick_assets = cur_assets - inventory
    liquidity = pd.DataFrame({
        'Current Ratio': safe_div(cur_assets, cur_liab),
        'Quick Ratio': safe_div(quick_assets, cur_liab),
        'Cash Ratio': safe_div(cash_sti, cur_liab),
        'Working Capital (₹)': (cur_assets - cur_liab),
    }, index=years)

    # Leverage / Coverage
    leverage = pd.DataFrame({
        'Debt to Assets': safe_div(total_debt, total_assets),
        'Debt to Equity': safe_div(total_debt, total_equity),
        'Interest Coverage': safe_div(ebit, int_exp.abs()),
    }, index=years)

    # Efficiency / Activity
    dio = safe_div(365, safe_div(cogs, avg_inventory))
    dso = safe_div(365, safe_div(rev, avg_receivables))
    dpo = safe_div(365, safe_div(cogs, avg_payables))
    efficiency = pd.DataFrame({
        'Inventory Turnover': safe_div(cogs, avg_inventory),
        'Receivables Turnover': safe_div(rev, avg_receivables),
        'Payables Turnover': safe_div(cogs, avg_payables),
        'Days Inventory Outstanding': dio,
        'Days Sales Outstanding': dso,
        'Days Payables Outstanding': dpo,
        'Cash Conversion Cycle (days)': dio + dso - dpo,
    }, index=years)

    return profitability, liquidity, leverage, efficiency


# ========================= UI =========================

st.title("📊 Financial Ratio Analyzer")
st.caption("Source: Yahoo Finance via yfinance. Computed on reported annual statements.")

colA, colB, colC = st.columns([2,1,1])
with colA:
    ticker = st.text_input("Ticker (Yahoo Finance)", value="RELIANCE.NS", help="Example: RELIANCE.NS, TCS.NS, AAPL, MSFT, TSLA")
with colB:
    show_market = st.checkbox("Show Market Ratios (P/E, P/B, Yield)", value=True)
with colC:
    digits = st.number_input("Decimal places", min_value=0, max_value=6, value=2, step=1)

if ticker:
    with st.spinner("Loading financials..."):
        inc, bal, cfs = load_statements(ticker)
        t = get_ticker(ticker)

    if inc.empty or bal.empty:
        st.error("Could not load sufficient financial data for this ticker.")
        st.stop()

    profitability, liquidity, leverage, efficiency = compute_ratios(inc, bal)

    # Year range filter to reduce chart/render load
    all_years = sorted(set(profitability.index) | set(liquidity.index) | set(leverage.index) | set(efficiency.index))
    if all_years:
        yr_min, yr_max = int(min(all_years)), int(max(all_years))
        default_start = max(yr_min, yr_max - 5)
        sel = st.slider("Year range", min_value=yr_min, max_value=yr_max, value=(default_start, yr_max))
        slc = slice(sel[0], sel[1])
        profitability = profitability.loc[slc]
        liquidity = liquidity.loc[slc]
        leverage = leverage.loc[slc]
        efficiency = efficiency.loc[slc]

    # ------------------ Market Ratios (optional) ------------------
    market_df = pd.DataFrame()
    if show_market:
        try:
            price = t.fast_info.get('last_price')
            if price is None or (isinstance(price, float) and np.isnan(price)):
                price = t.fast_info.get('last_close')
            if price is None or (isinstance(price, float) and np.isnan(price)):
                hist = t.history(period='5d')
                price = float(hist['Close'].dropna().iloc[-1]) if not hist.empty else np.nan

            shares_out = sget(bal, 'Share Issued')
            if shares_out.empty:
                shares_out = sget(bal, 'Ordinary Shares Number')
            latest_year = shares_out.dropna().index.max() if not shares_out.empty else None

            market_cap = t.fast_info.get('market_cap')
            if (market_cap is None or (isinstance(market_cap, float) and np.isnan(market_cap))) and latest_year:
                market_cap = price * float(shares_out.loc[latest_year])

            eps = sget(inc, 'Basic EPS')
            if eps.empty:
                eps = sget(inc, 'Diluted EPS')
            latest_eps = float(eps.dropna().iloc[-1]) if not eps.empty else np.nan
            pe = np.nan if (latest_eps is None or np.isnan(latest_eps) or latest_eps <= 0) else (price / latest_eps)

            book_equity = sget(bal, 'Total Equity Gross Minority Interest')
            if book_equity.empty and 'Total Equity' in bal.columns:
                book_equity = sget(bal, 'Total Equity')
            if book_equity.empty and 'Total Stockholder Equity' in bal.columns:
                book_equity = sget(bal, 'Total Stockholder Equity')
            book_value_per_share = (
                (book_equity.iloc[-1] / shares_out.iloc[-1])
                if (not book_equity.empty and not shares_out.empty and shares_out.iloc[-1] != 0)
                else np.nan
            )
            pb = np.nan if (book_value_per_share is None or isinstance(book_value_per_share, float) and np.isnan(book_value_per_share) or book_value_per_share == 0) else (price / book_value_per_share)

            dividends = t.dividends
            trailing_div = float(dividends.tail(4).sum()) if dividends is not None and not dividends.empty else np.nan
            dividend_yield = np.nan if (price is None or (isinstance(price, float) and (np.isnan(price) or price == 0))) else (trailing_div / price)

            market_df = pd.DataFrame({
                'Metric': ['Price', 'Market Cap', 'EPS (latest FY)', 'P/E', 'Book Value/Share', 'P/B', 'Trailing 12m Dividends', 'Dividend Yield'],
                'Value': [price, market_cap, latest_eps, pe, book_value_per_share, pb, trailing_div, dividend_yield]
            })
        except Exception as e:
            st.info(f"Market ratio data incomplete: {e}")

    # ------------------ Display ------------------
    st.subheader(f"Results for {ticker}")

    tabs = st.tabs(["Profitability", "Liquidity", "Leverage", "Efficiency", "Market (opt)", "Raw Data"]) 

    def fmt_df(df: pd.DataFrame, pct_cols=None, ratio_cols=None, int_cols=None):
        df_disp = df.copy()
        pct_cols = pct_cols or []
        ratio_cols = ratio_cols or []
        int_cols = int_cols or []
        for c in df_disp.columns:
            if c in pct_cols:
                df_disp[c] = (df_disp[c] * 100).map(lambda x: f"{x:.{digits}f}%" if pd.notna(x) else "")
            elif c in int_cols:
                df_disp[c] = df_disp[c].map(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
            else:
                df_disp[c] = df_disp[c].map(lambda x: f"{x:.{digits}f}" if pd.notna(x) else "")
        return df_disp

    with tabs[0]:
        st.write("### Profitability Ratios")
        st.dataframe(fmt_df(profitability, pct_cols=['Gross Margin','EBIT Margin','Net Profit Margin','ROA'], ratio_cols=['Asset Turnover']))
        st.write("#### Trend")
        st.line_chart(profitability[['Gross Margin','EBIT Margin','Net Profit Margin']])

    with tabs[1]:
        st.write("### Liquidity Ratios")
        st.dataframe(fmt_df(liquidity, pct_cols=[], int_cols=['Working Capital (₹)']))
        st.write("#### Trend")
        st.line_chart(liquidity[['Current Ratio','Quick Ratio','Cash Ratio']])

    with tabs[2]:
        st.write("### Leverage & Coverage")
        st.dataframe(fmt_df(leverage))
        st.write("#### Trend")
        st.line_chart(leverage[['Debt to Assets','Debt to Equity','Interest Coverage']])

    with tabs[3]:
        st.write("### Efficiency / Activity")
        eff_disp = efficiency.copy()
        st.dataframe(fmt_df(eff_disp))
        st.write("#### Trend (CCC)")
        if 'Cash Conversion Cycle (days)' in eff_disp.columns:
            st.line_chart(eff_disp[['Cash Conversion Cycle (days)']])

    with tabs[4]:
        st.write("### Market Ratios (Optional)")
        if not market_df.empty:
            st.dataframe(market_df)
        else:
            st.info("Market data not available for this ticker or period.")

    with tabs[5]:
        st.write("### Raw Financial Statements (Last 5 years if available)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Income Statement**")
            st.dataframe(inc.tail(5))
        with col2:
            st.write("**Balance Sheet**")
            st.dataframe(bal.tail(5))
        with col3:
            st.write("**Cash Flow**")
            st.dataframe(cfs.tail(5))

    # ------------------ Download ------------------
    st.divider()
    st.write("### Download Ratios")
    combined = (
        profitability.add_prefix('Profitability: ')
        .join(liquidity.add_prefix('Liquidity: '), how='outer')
        .join(leverage.add_prefix('Leverage: '), how='outer')
        .join(efficiency.add_prefix('Efficiency: '), how='outer')
    )
    csv = combined.to_csv(index=True)
    st.download_button("Download CSV", data=csv, file_name=f"{ticker}_ratios.csv", mime="text/csv")

    st.caption("Notes: ROE uses average book equity; Interest Coverage uses |Interest Expense|; turnover ratios use average balances; values depend on statement availability.")