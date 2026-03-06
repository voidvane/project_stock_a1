import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import traceback

# --- 1. Streamlit Page Configuration (Must be First) ---
st.set_page_config(
    page_title="AI Pro Stock Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Premium Modern CSS Injection ---
st.markdown("""
<style>
    /* Global Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    /* Backgrounds & Main Area */
    .stApp {
        background-color: #0B0E14; /* Deep dark blue/black background */
    }
    
    /* Sleek Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #131722, #1A1E29);
        border: 1px solid #2A2E39;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        transition: transform 0.2s ease-in-out, border-color 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #2962FF; /* Interactive blue highlight */
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #787B86 !important;
        font-weight: 600 !important;
    }
    
    /* Typography Styles */
    .company-header {
        font-size: 46px;
        font-weight: 800;
        background: -webkit-linear-gradient(0deg, #FFFFFF, #B2B5BE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.2;
    }
    .company-sub {
        color: #787B86;
        font-size: 16px;
        font-weight: 500;
        margin-top: 8px;
        margin-bottom: 30px;
        letter-spacing: 0.5px;
    }
    
    /* Custom Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #2A2E39;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 16px;
        font-weight: 600;
        color: #787B86;
    }
    .stTabs [aria-selected="true"] {
        color: #2962FF !important;
        border-bottom: 3px solid #2962FF !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid #2A2E39;
    }
    
    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2A2E39;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Custom AI Summary Box Container */
    .ai-summary-box {
        background: linear-gradient(180deg, rgba(29, 35, 48, 0.8) 0%, rgba(19, 23, 34, 0.9) 100%);
        border: 1px solid #2A2E39;
        border-left: 4px solid #00E676; /* Accent color */
        padding: 30px;
        border-radius: 12px;
        color: #D1D4DC;
        line-height: 1.7;
        font-size: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    
    /* Spinner Accent */
    .stSpinner > div > div {
        border-bottom-color: #2962FF !important; 
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        height: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #FFFFFF; font-weight: 800; letter-spacing: -1px;'>⚡ AI PRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #787B86; font-size: 14px; margin-top: -15px;'>Intelligent Market Terminal</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("🔍 검색 (Search)")
    st.caption("해외: 티커 (AAPL, NVDA) | 국내: 005930.KS")
    ticker_symbol = st.text_input("Ticker Symbol", value="NVDA", label_visibility="collapsed").upper()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⏳ 차트 기간 (Range)")
    period = st.select_slider(
        "Range Selection",
        label_visibility="collapsed",
        options=["1mo", "3mo", "6mo", "1y", "3y", "5y", "max"],
        value="1y",
        format_func=lambda x: {"1mo":"1M", "3mo":"3M", "6mo":"6M", "1y":"1Y", "3y":"3Y", "5y":"5Y", "max":"ALL"}[x]
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🧠 AI 엔진 연결 (선택)")
    st.caption("재무제표 심층 분석을 위한 OpenAI API Key")
    api_key = st.text_input("API Key (sk-...)", type="password", label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    fetch_button = st.button("실시간 분석 실행", type="primary", use_container_width=True)

# --- 4. Main Dashboard Logic ---
if fetch_button and ticker_symbol:
    with st.spinner(f"Fetching market data for {ticker_symbol}..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            if 'shortName' not in info and 'longName' not in info:
                st.error("티커 정보를 찾을 수 없습니다. (한국 주식은 .KS 또는 .KQ가 필요합니다)")
                st.stop()
                
            company_name = info.get('longName', info.get('shortName', ticker_symbol))
            sector = info.get('sector', 'Unknown Sector')
            industry = info.get('industry', 'Unknown Industry')
            currency = info.get('currency', 'USD')
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)
            
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close else 0
            
            # --- Company Header ---
            st.markdown(f"<div class='company-header'>{company_name} <span style='color: #787B86; font-size: 30px; font-weight: 600;'>{ticker_symbol}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='company-sub'>{sector} &nbsp;•&nbsp; {industry} &nbsp;•&nbsp; Currency in {currency}</div>", unsafe_allow_html=True)
            
            # --- Key Metrics Row ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Current Price", 
                          value=f"{current_price:,.2f}", 
                          delta=f"{price_change:,.2f} ({price_change_pct:,.2f}%)")
            with col2:
                st.metric(label="Market Cap", value=f"{info.get('marketCap', 0):,}  ")
            with col3:
                pe_ratio = info.get('trailingPE', 'N/A')
                st.metric(label="P/E Ratio (TTM)", value=f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
            with col4:
                pb_ratio = info.get('priceToBook', 'N/A')
                st.metric(label="Price to Book", value=f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Content Tabs ---
            tab1, tab2, tab3 = st.tabs(["📊 Technical Chart", "📋 Financial Statements", "🤖 AI Insight Report"])
            
            with tab1:
                hist = stock.history(period=period)
                if not hist.empty:
                    # Sleek Candlestick Chart
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        increasing_line_color='#26A69A', # Modern flat green
                        increasing_fillcolor='#26A69A',
                        decreasing_line_color='#EF5350', # Modern flat red
                        decreasing_fillcolor='#EF5350',
                        name='Price'
                    ))
                    
                    # Premium Dark Theme Layout update
                    fig.update_layout(
                        height=650,
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=False, zeroline=False, color='#787B86'),
                        yaxis=dict(showgrid=True, gridcolor='#2A2E39', zeroline=False, color='#787B86', side='right'),
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("차트 데이터가 존재하지 않습니다.")

            with tab2:
                financials = stock.financials
                if not financials.empty:
                    financials.columns = [str(col).split(' ')[0] for col in financials.columns]
                    # Display as an interactive dataframe
                    st.dataframe(financials.style.format("{:,.0f}"), use_container_width=True, height=500)
                else:
                    st.warning("재무제표 데이터가 제공되지 않는 종목입니다.")
                    
            with tab3:
                if not api_key:
                    st.info("💡 사이드바에서 OpenAI API Key를 입력하시면, AI가 복잡한 재무제표를 심층 분석하여 전문가 수준의 요약 리포트를 제공합니다.")
                else:
                    if financials.empty:
                         st.error("분석할 재무 데이터가 없습니다.")
                    else:
                        with st.spinner("🧠 AI 엔진 작동 중... 재무 데이터 패턴과 펀더멘탈을 분석하고 있습니다..."):
                            try:
                                client = OpenAI(api_key=api_key)
                                recent_years = financials.columns[:3]
                                analysis_data_df = financials[recent_years].head(20) 
                                data_str = analysis_data_df.to_markdown()
                                
                                prompt = f"""
                                당신은 월스트리트의 수석 재무 분석가입니다. 
                                아래는 {company_name} ({ticker_symbol})의 최근 연간 핵심 재무 데이터입니다. (통화: {currency})
                                
                                {data_str}
                                
                                위 데이터를 기반으로 펀더멘탈을 평가하고, 투자자를 위한 프리미엄 리포트를 마크다운으로 작성해주세요.
                                
                                필수 포함 항목:
                                1. 🎯 **Fundamental Summary**: 펀더멘탈 한 줄 핵심 평가
                                2. 📈 **Key Metrics Analysis**: 매출, 이익 등 긍정적/부정적 지표 상세 분석
                                3. 💡 **Investor Actionable Insight**: 향후 리스크 및 투자 고려사항
                                """
                                
                                response = client.chat.completions.create(
                                    model="gpt-3.5-turbo",
                                    messages=[
                                        {"role": "system", "content": "You are a top-tier financial analyst. Provide a professional, objective, and insightful evaluation."},
                                        {"role": "user", "content": prompt}
                                    ],
                                    temperature=0.6,
                                    max_tokens=1000
                                )
                                
                                summary = response.choices[0].message.content
                                
                                # Render inside a custom styled box
                                st.markdown(f"<div class='ai-summary-box'>{summary}</div>", unsafe_allow_html=True)
                                
                            except Exception as e:
                                st.error(f"AI 분석 오류: {str(e)}")
                                
        except Exception as e:
             st.error("데이터 통신 중 오류가 발생했습니다. 티커를 다시 확인해주세요.")
else:
    if not fetch_button:
        # Welcome Screen
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <div style='text-align: center; border: 1px solid #2A2E39; padding: 50px; border-radius: 16px; background: linear-gradient(145deg, #131722, #0B0E14); box-shadow: 0 10px 40px rgba(0,0,0,0.4);'>
                <h1 style='color: #FFFFFF; font-weight: 800; margin-bottom: 20px;'>Market Intelligence Platform</h1>
                <p style='color: #787B86; font-size: 18px; margin-bottom: 30px;'>프로 트레이더를 위한 고급 주식 차트 및 AI 재무 심층 분석 대시보드</p>
                <div style='color: #D1D4DC; font-size: 14px; display: inline-block; text-align: left;'>
                    ✅ <b>실시간 주가 동향 (Global & KR)</b><br>
                    ✅ <b>기업 펀더멘탈 및 주요 지표 추적</b><br>
                    ✅ <b>OpenAI 기반 지능형 재무제표 요약 리포트</b>
                </div>
                <br><br>
                <p style='color: #2962FF; font-weight: 600;'>👈 좌측 사이드바에서 종목을 검색하여 시작하세요.</p>
            </div>
            """, unsafe_allow_html=True)
