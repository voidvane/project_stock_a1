import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import traceback

# --- 1. Streamlit Page Configuration (Must be First) ---
st.set_page_config(
    page_title="PRO Stock Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Premium Modern CSS Injection ---
st.markdown("""
<style>
    /* Global Typography */
    html, body, [class*="css"]  {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Backgrounds & Main Area */
    .stApp {
        background-color: #0d1117; /* Deep tech dark background */
        color: #c9d1d9;
    }
    
    /* Sleek Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        padding: 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        transition: transform 0.2s ease-in-out, border-color 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #58a6ff; /* Tech blue highlight */
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #8b949e !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Typography Styles */
    .company-header {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.2;
        letter-spacing: -0.5px;
    }
    .company-sub {
        color: #8b949e;
        font-size: 15px;
        font-weight: 500;
        margin-top: 4px;
        margin-bottom: 24px;
    }
    
    /* Custom Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: transparent;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 15px;
        font-weight: 600;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom: 3px solid #58a6ff !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
    
    /* Custom Summary Box Container */
    .summary-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        padding: 24px;
        border-radius: 8px;
        color: #c9d1d9;
        line-height: 1.6;
        font-size: 15px;
        margin-bottom: 16px;
    }
    
    .buy-sell-box {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
    
    .buy-sell-title {
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 12px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
    }
    
    /* Spinner Accent */
    .stSpinner > div > div {
        border-bottom-color: #58a6ff !important; 
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        height: 44px;
        background-color: #238636;
        color: #ffffff;
        border: 1px solid rgba(240, 246, 252, 0.1);
    }
    .stButton > button:hover {
        background-color: #2ea043;
        border-color: rgba(240, 246, 252, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Data Fetching Logic (Cached) ---
@st.cache_data(ttl=600)
def fetch_stock_data(ticker_symbol, period):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        if 'shortName' not in info and 'longName' not in info:
            return None, "티커 정보를 찾을 수 없습니다. (한국 주식은 .KS 또는 .KQ가 필요합니다)"
            
        hist = stock.history(period=period)
        financials = stock.financials
        
        return {
            'info': info,
            'hist': hist,
            'financials': financials
        }, None
    except Exception as e:
        return None, f"데이터 통신 중 오류가 발생했습니다: {str(e)}"

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #ffffff; font-weight: 700; letter-spacing: 1px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e; font-size: 13px; margin-top: -15px; text-transform: uppercase;'>Market Analysis System</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
    
    with st.form("search_form"):
        st.subheader("Symbol / Ticker")
        st.caption("US: AAPL, NVDA | KR: 005930.KS")
        ticker_symbol = st.text_input("Ticker", value="NVDA", label_visibility="collapsed").upper()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Timeframe")
        period = st.select_slider(
            "Range",
            label_visibility="collapsed",
            options=["1mo", "3mo", "6mo", "1y", "3y", "5y", "max"],
            value="1y",
            format_func=lambda x: {"1mo":"1M", "3mo":"3M", "6mo":"6M", "1y":"1Y", "3y":"3Y", "5y":"5Y", "max":"ALL"}[x]
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_button = st.form_submit_button("Execute Analysis", use_container_width=True)

# --- 4. Main Dashboard Logic ---
if fetch_button and ticker_symbol:
    with st.spinner(f"PROCESSING DATA: {ticker_symbol}..."):
        data, error = fetch_stock_data(ticker_symbol, period)
        
        if error:
            st.error(error)
        elif data:
            info = data['info']
            hist = data['hist']
            financials = data['financials']
            
            company_name = info.get('longName', info.get('shortName', ticker_symbol))
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            currency = info.get('currency', 'USD')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)
            
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close else 0
            
            # --- Company Header ---
            st.markdown(f"<div class='company-header'>{company_name} <span style='color: #8b949e; font-size: 24px; font-weight: 500; margin-left: 10px;'>{ticker_symbol}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='company-sub'>[ {sector} ] &nbsp; {industry} &nbsp;|&nbsp; CURRENCY: {currency}</div>", unsafe_allow_html=True)
            
            # --- Key Metrics Row ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Current Price", 
                          value=f"{current_price:,.2f}", 
                          delta=f"{price_change:,.2f} ({price_change_pct:,.2f}%)")
            with col2:
                market_cap = info.get('marketCap', 0)
                if market_cap >= 1e12:
                    cap_str = f"{market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    cap_str = f"{market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    cap_str = f"{market_cap/1e6:.2f}M"
                else:
                    cap_str = f"{market_cap:,}"
                st.metric(label="Market Cap", value=cap_str)
            with col3:
                pe_ratio = info.get('trailingPE', 'N/A')
                st.metric(label="P/E Ratio (TTM)", value=f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
            with col4:
                pb_ratio = info.get('priceToBook', 'N/A')
                st.metric(label="Price to Book", value=f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Content Tabs ---
            tab1, tab2, tab3 = st.tabs(["[ TECHNICAL CHART ]", "[ FINANCIAL DATA ]", "[ ANALYSIS & SIGNALS ]"])
            
            with tab1:
                if not hist.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        increasing_line_color='#3fb950', # Tech green
                        increasing_fillcolor='#3fb950',
                        decreasing_line_color='#f85149', # Tech red
                        decreasing_fillcolor='#f85149',
                        name='Price'
                    ))
                    
                    fig.update_layout(
                        height=600,
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False, color='#8b949e'),
                        yaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False, color='#8b949e', side='right'),
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No chart data available.")

            with tab2:
                if not financials.empty:
                    financials.columns = [str(col).split(' ')[0] for col in financials.columns]
                    st.dataframe(financials.style.format("{:,.0f}"), use_container_width=True, height=500)
                else:
                    st.warning("No financial data available for this ticker.")
                    
            with tab3:
                # --- Essential Buy/Sell Information ---
                target_price = info.get('targetMeanPrice', 'N/A')
                target_high = info.get('targetHighPrice', 'N/A')
                target_low = info.get('targetLowPrice', 'N/A')
                recommendation = info.get('recommendationKey', 'N/A').upper().replace('_', ' ')
                fifty_two_w_high = info.get('fiftyTwoWeekHigh', 'N/A')
                fifty_two_w_low = info.get('fiftyTwoWeekLow', 'N/A')
                analyst_count = info.get('numberOfAnalystOpinions', 'N/A')
                
                # Signal logic
                is_buy = 'BUY' in recommendation.upper() or 'OUTPERFORM' in recommendation.upper()
                is_sell = 'SELL' in recommendation.upper() or 'UNDERPERFORM' in recommendation.upper()
                signal_color = "#3fb950" if is_buy else ("#f85149" if is_sell else "#d2a8ff")
                
                b1, b2 = st.columns(2)
                
                with b1:
                    st.markdown(f"""
                    <div class='buy-sell-box'>
                        <div class='buy-sell-title'>MARKET CONSENSUS</div>
                        <p style='color: #8b949e; font-size: 13px; margin: 0;'>Recommendation Signal</p>
                        <h3 style='color: {signal_color}; margin-top: 5px;'>{recommendation}</h3>
                        <p style='color: #8b949e; font-size: 13px; margin: 15px 0 0 0;'>Analyst Coverage</p>
                        <p style='color: #ffffff; font-weight: 500; font-size: 16px; margin-top: 5px;'>{analyst_count} Analysts</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with b2:
                    st.markdown(f"""
                    <div class='buy-sell-box'>
                        <div class='buy-sell-title'>PRICE TARGETS</div>
                        <p style='color: #8b949e; font-size: 13px; margin: 0;'>Mean Target</p>
                        <h3 style='color: #58a6ff; margin-top: 5px;'>{target_price} <span style='font-size: 14px; color:#8b949e;'>{currency}</span></h3>
                        <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                            <div>
                                <p style='color: #8b949e; font-size: 12px; margin: 0;'>Low Target</p>
                                <p style='color: #ffffff; font-weight: 500; font-size: 14px; margin-top: 2px;'>{target_low}</p>
                            </div>
                            <div style='text-align: right;'>
                                <p style='color: #8b949e; font-size: 12px; margin: 0;'>High Target</p>
                                <p style='color: #ffffff; font-weight: 500; font-size: 14px; margin-top: 2px;'>{target_high}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class='buy-sell-box'>
                    <div class='buy-sell-title'>52-WEEK RANGE & VOLATILITY</div>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='text-align: left;'>
                            <p style='color: #8b949e; font-size: 13px; margin: 0;'>52W Low</p>
                            <h4 style='color: #ffffff; margin-top: 5px;'>{fifty_two_w_low}</h4>
                        </div>
                        <div style='text-align: center; flex-grow: 1; padding: 0 20px;'>
                            <div style='height: 4px; background: #30363d; border-radius: 2px; position: relative;'>
                                {/* Simple visualization line if values exist */}
                                <div style='height: 4px; background: #58a6ff; border-radius: 2px; position: absolute; left: 50%; width: 10px; margin-left: -5px;'></div>
                            </div>
                            <p style='color: #8b949e; font-size: 12px; margin-top: 8px;'>Current: {current_price}</p>
                        </div>
                        <div style='text-align: right;'>
                            <p style='color: #8b949e; font-size: 13px; margin: 0;'>52W High</p>
                            <h4 style='color: #ffffff; margin-top: 5px;'>{fifty_two_w_high}</h4>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Fundamental Local Summary
                st.markdown("<br>", unsafe_allow_html=True)
                summary_text = f"**System Assessment for {company_name} ({ticker_symbol})**<br><br>"
                
                # P/E Evaluation
                if isinstance(pe_ratio, (int, float)):
                    if pe_ratio < 0:
                        summary_text += "- **Valuation:** Earnings are currently negative.<br>"
                    elif pe_ratio < 15:
                        summary_text += "- **Valuation:** P/E Ratio is below 15, which may indicate undervaluation relative to historical market averages.<br>"
                    elif pe_ratio > 30:
                        summary_text += "- **Valuation:** P/E Ratio is above 30, suggesting a premium valuation expectations of high growth.<br>"
                    else:
                        summary_text += "- **Valuation:** P/E Ratio is moderate, tracking closer to broad market averages.<br>"
                        
                # Upside Evaluation
                if isinstance(target_price, (int, float)) and isinstance(current_price, (int, float)) and current_price > 0:
                    upside = ((target_price - current_price) / current_price) * 100
                    if upside > 10:
                        summary_text += f"- **Target Projection:** Mean analyst target implies a potential **upside of {upside:.1f}%**.<br>"
                    elif upside < -10:
                        summary_text += f"- **Target Projection:** Mean analyst target implies a potential **downside of {abs(upside):.1f}%**.<br>"
                    else:
                        summary_text += f"- **Target Projection:** Current price is trading near the mean analyst target ({upside:.1f}% difference).<br>"
                
                # Dividend Evaluation
                div_yield = info.get('dividendYield', 0)
                if isinstance(div_yield, (int, float)) and div_yield > 0:
                    summary_text += f"- **Income:** Stock offers a dividend yield of **{(div_yield * 100):.2f}%**.<br>"
                
                st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)
else:
    if not fetch_button:
        # Welcome Screen
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <div style='text-align: left; border: 1px solid #30363d; padding: 40px; border-radius: 8px; background: #0d1117;'>
                <div style='font-size: 12px; color: #58a6ff; letter-spacing: 2px; font-weight: 600; text-transform: uppercase; margin-bottom: 15px;'>System Ready</div>
                <h1 style='color: #ffffff; font-weight: 700; margin-bottom: 20px; font-size: 32px; letter-spacing: -0.5px;'>Financial Data Terminal</h1>
                <p style='color: #8b949e; font-size: 15px; margin-bottom: 30px; line-height: 1.6;'>
                    Advanced market data processing and technical analysis dashboard.<br>
                    Optimized for rapid fundamental extraction and chart visualization.
                </p>
                
                <div style='background: #161b22; border-left: 3px solid #3fb950; padding: 15px 20px; border-radius: 4px; color: #c9d1d9; font-size: 14px;'>
                    <div style='margin-bottom: 8px;'>[ Module 1 ] &nbsp; Real-time Market Capitalization & Pricing</div>
                    <div style='margin-bottom: 8px;'>[ Module 2 ] &nbsp; Consensus Analyst Recommendations & Targets</div>
                    <div>[ Module 3 ] &nbsp; Fundamental Matrix Evaluation</div>
                </div>
                
                <br><br>
                <div style='color: #58a6ff; font-weight: 600; font-size: 14px;'>
                    > Initialize search in the left panel to establish connection.
                </div>
            </div>
            """, unsafe_allow_html=True)
