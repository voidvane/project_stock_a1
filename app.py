import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import shutil
import os

# Try to clear yfinance cache if it's causing issues
try:
    cache_dirs = [
        os.path.join(os.path.expanduser("~"), ".cache", "py-yfinance"),
        os.path.join(os.path.expanduser("~"), ".cache", "yfinance"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "py-yfinance"), # Windows
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "yfinance"),    # Windows
    ]
    for d in cache_dirs:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════════
# KOREAN STOCK NAME → TICKER DICTIONARY  (popular ~80 stocks)
# ══════════════════════════════════════════════════════════════════════
KR_STOCK_MAP = {
    # ── 대형주 (Large Cap) ──
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "삼성SDI": "006400.KS",
    "현대자동차": "005380.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "POSCO홀딩스": "005490.KS",
    "포스코홀딩스": "005490.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "LG화학": "051910.KS",
    "LG전자": "066570.KS",
    "삼성물산": "028260.KS",
    "삼성생명": "032830.KS",
    "삼성화재": "000810.KS",
    "삼성전기": "009150.KS",
    "삼성에스디에스": "018260.KS",
    "삼성SDS": "018260.KS",
    "현대모비스": "012330.KS",
    "SK이노베이션": "096770.KS",
    "SK텔레콤": "017670.KS",
    "SK": "034730.KS",
    "KT": "030200.KS",
    "KT&G": "033780.KS",
    "한국전력": "015760.KS",
    "한전": "015760.KS",
    "하나금융지주": "086790.KS",
    "우리금융지주": "316140.KS",
    "카카오뱅크": "323410.KS",
    "카카오페이": "377300.KS",
    "크래프톤": "259960.KS",
    "엔씨소프트": "036570.KS",
    "넷마블": "251270.KS",
    "펄어비스": "263750.KS",
    "하이브": "352820.KS",
    "CJ제일제당": "097950.KS",
    "CJ": "001040.KS",
    "롯데케미칼": "011170.KS",
    "한화솔루션": "009830.KS",
    "한화에어로스페이스": "012450.KS",
    "한화오션": "042660.KS",
    "HD현대중공업": "329180.KS",
    "현대중공업": "329180.KS",
    "HD한국조선해양": "009540.KS",
    "두산에너빌리티": "034020.KS",
    "두산밥캣": "241560.KS",
    "포스코퓨처엠": "003670.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "엘앤에프": "066970.KQ",
    "HLB": "028300.KQ",
    "리노공업": "058470.KQ",
    "알테오젠": "196170.KQ",
    # ── 인기 ETF ──
    "KODEX 200": "069500.KS",
    "KODEX 레버리지": "122630.KS",
    "KODEX 인버스": "114800.KS",
    "TIGER 200": "102110.KS",
    "TIGER 미국S&P500": "360750.KS",
    "TIGER 나스닥100": "133690.KS",
    # ── 미국 인기종목 (Korean aliases) ──
    "애플": "AAPL",
    "테슬라": "TSLA",
    "엔비디아": "NVDA",
    "마이크로소프트": "MSFT",
    "아마존": "AMZN",
    "구글": "GOOGL",
    "알파벳": "GOOGL",
    "메타": "META",
    "넷플릭스": "NFLX",
    "AMD": "AMD",
}


def search_stock_suggestions(query, max_results=8):
    """Search Korean stock dictionary and yfinance for full domestic coverage."""
    query_lower = query.lower().strip()
    seen_tickers = set()
    results = []

    # 1) Dictionary partial match
    for name, ticker in KR_STOCK_MAP.items():
        if query_lower in name.lower() or query_lower in ticker.lower():
            if ticker not in seen_tickers:
                results.append((name, ticker))
                seen_tickers.add(ticker)

    # 2) yfinance Search fallback/complement
    try:
        # Note: 'max_results' is not supported in recent yfinance Search()
        # It returns a fixed number (usually 6-10)
        search_results = yf.Search(query)
        for item in getattr(search_results, 'quotes', []):
            symbol = item.get('symbol', '')
            # Yahoo search sometimes hits non-equity indices or OTC, but for KR it's usually good
            name = item.get('shortname', item.get('longname', symbol))
            if symbol and symbol not in seen_tickers:
                results.append((name, symbol))
                seen_tickers.add(symbol)
    except Exception:
        pass

    return results[:max_results]

# ══════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PRO Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# 2. i18n – BILINGUAL TRANSLATIONS  (Korean / English)
# ══════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    "en": {
        "app_title": "PRO Stock Analytics",
        "app_subtitle": "Market Analysis System",
        "lang_label": "Language",
        "symbol_header": "Symbol / Ticker",
        "symbol_hint": "US: AAPL, NVDA | KR: 005930.KS",
        "timeframe": "Timeframe",
        "execute": "Execute Analysis",
        "quick_order": "Quick Order",
        "order_type": "Order Type",
        "buy": "BUY",
        "sell": "SELL",
        "quantity": "Quantity",
        "price": "Price",
        "place_order": "Place Order (Demo)",
        "order_demo_msg": "⚠️ This is a UI demo – no real orders are placed.",
        "processing": "PROCESSING DATA: {}...",
        "ticker_not_found": "Ticker not found. (Korean stocks need .KS or .KQ suffix)",
        "data_error": "Error during data retrieval: {}",
        "search_suggest_title": "🔍 Did you mean one of these?",
        "search_suggest_desc": "Click a button below to search that stock:",
        "search_no_suggest": "No similar stocks found. Please check the ticker symbol.",
        "search_tip": "💡 Tip: For Korean stocks, add .KS (KOSPI) or .KQ (KOSDAQ) after the code. Example: 005930.KS",
        "current_price": "Current Price",
        "market_cap": "Market Cap",
        "pe_ratio": "P/E Ratio (TTM)",
        "price_to_book": "Price to Book",
        "volume_today": "Volume",
        "div_yield_label": "Div Yield",
        "technical_chart": "Technical Chart",
        "financial_data": "Financial Data",
        "analysis_signals": "Analysis & Signals",
        "sma20": "SMA 20",
        "sma50": "SMA 50",
        "volume": "Volume",
        "no_chart": "No chart data available.",
        "no_financials": "No financial data available.",
        "market_consensus": "MARKET CONSENSUS",
        "recommendation": "Recommendation",
        "analyst_coverage": "Analyst Coverage",
        "analysts": "Analysts",
        "price_targets": "PRICE TARGETS",
        "mean_target": "Mean Target",
        "low_target": "Low Target",
        "high_target": "High Target",
        "week52_range": "52-WEEK RANGE",
        "week52_low": "52W Low",
        "week52_high": "52W High",
        "current": "Current",
        "news_feed": "NEWS FEED",
        "no_news": "No recent news available.",
        "news_ref": "News sourced from Yahoo Finance — for reference only.",
        "sys_assessment": "System Assessment for {} ({})",
        "val_negative": "Earnings are currently negative.",
        "val_under15": "P/E below 15 — may indicate undervaluation.",
        "val_over30": "P/E above 30 — premium valuation / high growth expected.",
        "val_moderate": "P/E is moderate, near broad market averages.",
        "target_upside": "Analyst target implies **{:.1f}% upside**.",
        "target_downside": "Analyst target implies **{:.1f}% downside**.",
        "target_near": "Trading near analyst target ({:.1f}% diff).",
        "income_yield": "Dividend yield: **{:.2f}%**.",
        "welcome_status": "System Ready",
        "welcome_title": "Financial Data Terminal",
        "welcome_desc": "Advanced market data processing and technical analysis dashboard.<br>Optimized for rapid fundamental extraction and chart visualization.",
        "welcome_m1": "[ Module 1 ]  Real-time Market Capitalization & Pricing",
        "welcome_m2": "[ Module 2 ]  Consensus Analyst Recommendations & Targets",
        "welcome_m3": "[ Module 3 ]  Fundamental Matrix Evaluation",
        "welcome_m4": "[ Module 4 ]  Live News Feed & Technical Overlays",
        "welcome_cta": "> Initialize search in the left panel to begin.",
        "revenue_trend": "Revenue Trend",
        "net_income_trend": "Net Income Trend",
        "growth_analysis": "Growth & Analysis",
        "yoy_growth": "YoY Growth",
        "margin_analysis": "Margin Analysis",
        "op_margin": "Op. Margin",
        "net_margin": "Net Margin",
        "financial_summary": "Financial Summary",
        "trend_improving": "The financial trend is improving with growing revenue and profits.",
        "trend_declining": "The financial trend shows some signs of declining revenue or profits.",
        "trend_stable": "The financial trend is relatively stable.",
        "revenue_label": "Revenue",
        "net_income_label": "Net Income",
        "market_indices": "Market Indices",
        "stock_rankings": "Stock Rankings",
        "top_value": "Top Value",
        "top_gainers": "Top Gainers",
        "top_losers": "Top Losers",
        "news_highlights": "News Highlights",
        "domestic": "Domestic",
        "overseas": "Overseas",
    },
    "ko": {
        "app_title": "PRO 주식 분석기",
        "app_subtitle": "시장 분석 시스템",
        "lang_label": "언어",
        "symbol_header": "종목 / 티커",
        "symbol_hint": "미국: AAPL, NVDA | 한국: 005930.KS",
        "timeframe": "기간 설정",
        "execute": "분석 실행",
        "quick_order": "빠른 주문",
        "order_type": "주문 유형",
        "buy": "매수",
        "sell": "매도",
        "quantity": "수량",
        "price": "가격",
        "place_order": "주문 (데모)",
        "order_demo_msg": "⚠️ 이것은 UI 데모입니다 – 실제 주문은 실행되지 않습니다.",
        "processing": "데이터 처리 중: {}...",
        "ticker_not_found": "티커 정보를 찾을 수 없습니다. (한국 주식은 .KS 또는 .KQ가 필요합니다)",
        "data_error": "데이터 통신 중 오류가 발생했습니다: {}",
        "search_suggest_title": "🔍 혹시 이 종목을 찾으셨나요?",
        "search_suggest_desc": "아래 버튼을 클릭하면 해당 종목을 검색합니다:",
        "search_no_suggest": "유사한 종목을 찾지 못했습니다. 티커 심볼을 확인해 주세요.",
        "search_tip": "💡 팁: 한국 주식은 종목코드 뒤에 .KS (코스피) 또는 .KQ (코스닥)을 붙여주세요. 예: 005930.KS",
        "current_price": "현재가",
        "market_cap": "시가총액",
        "pe_ratio": "PER (TTM)",
        "price_to_book": "PBR",
        "volume_today": "거래량",
        "div_yield_label": "배당수익률",
        "technical_chart": "기술적 차트",
        "financial_data": "재무 데이터",
        "analysis_signals": "분석 & 시그널",
        "sma20": "20일선",
        "sma50": "50일선",
        "volume": "거래량",
        "no_chart": "차트 데이터가 없습니다.",
        "no_financials": "재무 데이터가 없습니다.",
        "market_consensus": "시장 컨센서스",
        "recommendation": "투자의견",
        "analyst_coverage": "애널리스트 커버리지",
        "analysts": "명",
        "price_targets": "목표 주가",
        "mean_target": "평균 목표가",
        "low_target": "최저 목표가",
        "high_target": "최고 목표가",
        "week52_range": "52주 변동폭",
        "week52_low": "52주 최저",
        "week52_high": "52주 최고",
        "current": "현재",
        "revenue_trend": "매출액 추이",
        "net_income_trend": "당기순이익 추이",
        "growth_analysis": "성장성 및 분석",
        "yoy_growth": "전년 대비 성장률",
        "margin_analysis": "수익성 분석",
        "op_margin": "영업이익률",
        "net_margin": "순이익률",
        "financial_summary": "재무 상태 요약",
        "trend_improving": "매출과 이익이 동반 성장하며 재무 상태가 개선되고 있습니다.",
        "trend_declining": "매출 또는 이익이 정체되거나 하락하는 추세입니다.",
        "trend_stable": "주요 재무 지표가 비교적 안정적인 수준을 유지하고 있습니다.",
        "revenue_label": "매출액",
        "net_income_label": "당기순이익",
        "news_feed": "뉴스 피드",
        "no_news": "최근 뉴스가 없습니다.",
        "news_ref": "뉴스 출처: Yahoo Finance — 참고용입니다.",
        "sys_assessment": "{} ({}) 시스템 평가",
        "val_negative": "현재 수익이 마이너스입니다.",
        "val_under15": "PER 15 미만 — 저평가 가능성이 있습니다.",
        "val_over30": "PER 30 초과 — 고성장 기대 프리미엄 밸류에이션.",
        "val_moderate": "PER이 시장 평균 수준입니다.",
        "target_upside": "애널리스트 목표가 기준 **{:.1f}% 상승 여력**.",
        "target_downside": "애널리스트 목표가 기준 **{:.1f}% 하락 가능성**.",
        "target_near": "현재가가 애널리스트 목표가 근처 ({:.1f}% 차이).",
        "income_yield": "배당수익률: **{:.2f}%**.",
        "welcome_status": "시스템 준비 완료",
        "welcome_title": "금융 데이터 터미널",
        "welcome_desc": "고급 시장 데이터 처리 및 기술적 분석 대시보드.<br>빠른 펀더멘털 분석과 차트 시각화에 최적화.",
        "welcome_m1": "[ 모듈 1 ]  실시간 시가총액 & 시세",
        "welcome_m2": "[ 모듈 2 ]  애널리스트 컨센서스 & 목표가",
        "welcome_m3": "[ 모듈 3 ]  펀더멘털 매트릭스 분석",
        "welcome_m4": "[ 모듈 4 ]  실시간 뉴스 & 기술적 오버레이",
        "welcome_cta": "> 왼쪽 패널에서 검색을 시작하세요.",
        "market_indices": "시장 지수",
        "stock_rankings": "실시간 랭킹 주식",
        "top_value": "거래대금 상위",
        "top_gainers": "상승률 상위",
        "top_losers": "하락률 상위",
        "news_highlights": "이 시각 뉴스",
        "domestic": "국내",
        "overseas": "해외",
    },
}


def t(key):
    """Return translated string for the current language."""
    lang = st.session_state.get("lang", "en")
    return TRANSLATIONS[lang].get(key, key)


# ══════════════════════════════════════════════════════════════════════
# 3. PREMIUM CSS  (M-able Wide inspired dark WTS theme)
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── Global ───────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                     Helvetica, Arial, sans-serif;
    }
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }

    /* ── Sidebar ──────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }

    /* ── Metric Cards ─────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        padding: 18px 16px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        transition: transform .15s, border-color .15s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    [data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        color: #8b949e !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ── Widget Card (reusable) ────────────────── */
    .wts-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .wts-card-title {
        font-size: 12px;
        font-weight: 700;
        color: #58a6ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid #30363d;
    }
    .wts-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
    }
    .wts-label {
        color: #8b949e;
        font-size: 12px;
    }
    .wts-value {
        color: #ffffff;
        font-size: 14px;
        font-weight: 600;
    }

    /* ── News item ────────────────────────────── */
    .news-item {
        padding: 10px 0;
        border-bottom: 1px solid #21262d;
    }
    .news-item:last-child { border-bottom: none; }
    .news-item a {
        color: #c9d1d9 !important;
        text-decoration: none !important;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.4;
    }
    .news-item a:hover { color: #58a6ff !important; }
    .news-meta {
        color: #484f58;
        font-size: 11px;
        margin-top: 3px;
    }

    /* ── Company Header ───────────────────────── */
    .company-header {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        letter-spacing: -0.5px;
    }
    .company-sub {
        color: #8b949e;
        font-size: 13px;
        font-weight: 500;
        margin-top: 2px;
        margin-bottom: 16px;
    }

    /* ── Summary Box ──────────────────────────── */
    .summary-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        padding: 20px;
        border-radius: 6px;
        color: #c9d1d9;
        line-height: 1.6;
        font-size: 14px;
        margin-top: 12px;
    }

    /* ── Tabs ──────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: transparent;
        font-size: 13px;
        font-weight: 600;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom: 3px solid #58a6ff !important;
    }

    /* ── Buttons ───────────────────────────────── */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        height: 40px;
        background-color: #238636;
        color: #ffffff;
        border: 1px solid rgba(240,246,252,0.1);
    }
    .stButton > button:hover {
        background-color: #2ea043;
    }

    /* ── Quick‑Order Buy/Sell buttons ──────────── */
    .buy-btn button {
        background-color: #238636 !important;
        width: 100%;
    }
    .sell-btn button {
        background-color: #da3633 !important;
        width: 100%;
    }

    /* ── DataFrame ─────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #30363d;
    }

    /* ── Spinner accent ────────────────────────── */
    .stSpinner > div > div {
        border-bottom-color: #58a6ff !important;
    }

    /* ── Range bar for 52-week ─────────────────── */
    .range-bar {
        height: 4px;
        background: #30363d;
        border-radius: 2px;
        position: relative;
        margin: 8px 0;
    }
    .range-marker {
        height: 12px;
        width: 12px;
        background: #58a6ff;
        border-radius: 50%;
        position: absolute;
        top: -4px;
        transform: translateX(-50%);
    }
    /* Dashboard CSS */
    .dash-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .dash-index-val { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 2px; }
    .dash-index-delta { font-size: 13px; font-weight: 500; }
    .dash-index-title { font-size: 13px; color: #8b949e; margin-bottom: 8px; }
    
    .news-grid-item {
        background: #0d1117;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 15px;
        border: 1px solid #21262d;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .news-grid-content { flex: 1; padding-right: 15px; }
    .news-grid-title { font-size: 14px; font-weight: 600; color: #c9d1d9; line-height: 1.4; margin-bottom: 5px; }
    .news-grid-meta { font-size: 11px; color: #8b949e; }
    .news-grid-logo { width: 40px; height: 40px; background: #21262d; border-radius: 5px; }
    
    .rank-item {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #21262d;
    }
    .rank-num { width: 25px; font-weight: 700; color: #58a6ff; font-size: 14px; }
    .rank-name { flex: 1; font-weight: 600; font-size: 14px; color: #c9d1d9; cursor: pointer; }
    .rank-name:hover { text-decoration: underline; color: #58a6ff; }
    .rank-price { text-align: right; width: 100px; font-size: 13px; color: #fff; }
    .rank-change { text-align: right; width: 100px; font-size: 12px; }

    .dash-section-title {
        font-size: 18px; font-weight: 700; color: #fff; margin: 25px 0 15px 0;
        display: flex; align-items: center;
    }
    .dash-section-title::after { content: ' >'; color: #8b949e; margin-left: 5px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# 4. DATA FETCHING  (cached)
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def fetch_stock_data(ticker_symbol, period):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        if "shortName" not in info and "longName" not in info:
            return None, "NOT_FOUND"

        hist = stock.history(period=period)
        financials = stock.financials

        # News — safe extraction
        try:
            news_raw = stock.news or []
        except Exception:
            news_raw = []

        news_items = []
        for item in news_raw[:8]:
            title = item.get("title", "")
            link = item.get("link", "")
            publisher = item.get("publisher", "")
            pub_date = ""
            ts = item.get("providerPublishTime")
            if ts:
                try:
                    pub_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            if title:
                news_items.append({"title": title, "link": link, "publisher": publisher, "date": pub_date})

        return {
            "info": info,
            "hist": hist,
            "financials": financials,
            "news": news_items,
        }, None
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=300)
def fetch_dashboard_data():
    """Fetch indices and ranking data for the dashboard (Domestic & Overseas)."""
    # 1. Define Domestic (KR) Assets
    indices_kr = {
        "^KS11": "KOSPI", 
        "^KQ11": "KOSDAQ", 
        "USDKRW=X": "USD/KRW"
    }
    popular_kr = [
        "005930.KS", "000660.KS", "035420.KS", "035720.KS", "005380.KS", 
        "000270.KS", "068270.KS", "105560.KS", "005490.KS", "032830.KS"
    ]

    # 2. Define Overseas (US) Assets
    indices_us = {
        "^DJI": "Dow Jones", 
        "^IXIC": "NASDAQ", 
        "^GSPC": "S&P 500",
        "^SOX": "PHLX Semi",
        "CL=F": "WTI Oil",
        "GC=F": "Gold"
    }
    popular_us = [
        "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", 
        "GOOGL", "META", "AMD", "NFLX", "AVGO"
    ]

    def process_tickers(ticker_dict, period="2d"):
        """Helper to fetch and process index/ticker data."""
        results = []
        tickers = list(ticker_dict.keys())
        
        # Try bulk download
        data = pd.DataFrame()
        try:
            data = yf.download(tickers, period=period, interval="1d", progress=False, threads=False)
        except Exception:
            pass
            
        # If bulk failed or empty, fallback to individual
        if data.empty:
            for sym, name in ticker_dict.items():
                try:
                    t_hist = yf.Ticker(sym).history(period=period)
                    if len(t_hist) >= 1:
                        close = t_hist['Close'].iloc[-1]
                        prev = t_hist['Close'].iloc[-2] if len(t_hist) > 1 else close
                        delta = close - prev
                        pct = (delta / prev * 100) if prev != 0 else 0
                        results.append({"ticker": sym, "name": name, "val": close, "delta": delta, "pct": pct})
                except:
                    continue
        else:
            # Process bulk
            for sym, name in ticker_dict.items():
                try:
                    close_series = None
                    if isinstance(data.columns, pd.MultiIndex):
                        if sym in data['Close'].columns:
                            close_series = data['Close'][sym].dropna()
                    else:
                        if sym in data.columns:
                            close_series = data[sym]
                        elif 'Close' in data.columns and len(tickers) == 1:
                            close_series = data['Close'].dropna()
                    
                    if close_series is not None and len(close_series) >= 1:
                        close = close_series.iloc[-1]
                        prev = close_series.iloc[-2] if len(close_series) > 1 else close
                        delta = close - prev
                        pct = (delta / prev * 100) if prev != 0 else 0
                        results.append({"ticker": sym, "name": name, "val": close, "delta": delta, "pct": pct})
                except:
                    continue
        return results

    def process_rankings(ticker_list, period="5d"):
        """Helper to fetch and process ranking data."""
        results = []
        data = pd.DataFrame()
        try:
            data = yf.download(ticker_list, period=period, interval="1d", progress=False, threads=False)
        except Exception:
            pass

        if data.empty:
            for sym in ticker_list:
                try:
                    t_hist = yf.Ticker(sym).history(period=period)
                    if len(t_hist) >= 2:
                        close = float(t_hist['Close'].iloc[-1])
                        prev = float(t_hist['Close'].iloc[-2])
                        delta = close - prev
                        pct = (delta / prev * 100) if prev != 0 else 0
                        
                        # Name resolution
                        name = sym
                        if sym in KR_STOCK_MAP.values():
                             name = next((k for k, v in KR_STOCK_MAP.items() if v == sym), sym)
                        
                        results.append({
                            "ticker": sym, 
                            "name": name,
                            "price": close, "pct": pct
                        })
                except:
                    continue
        else:
            for sym in ticker_list:
                try:
                    s_data = None
                    if isinstance(data.columns, pd.MultiIndex):
                        if sym in data['Close'].columns:
                            s_data = data['Close'][sym].dropna()
                    else:
                        if 'Close' in data.columns:
                             s_data = data['Close'].dropna()
                    
                    if s_data is not None and len(s_data) >= 2:
                        close = float(s_data.iloc[-1])
                        prev = float(s_data.iloc[-2])
                        delta = close - prev
                        pct = (delta / prev * 100) if prev != 0 else 0
                        
                        # Name resolution
                        name = sym
                        if sym in KR_STOCK_MAP.values():
                             name = next((k for k, v in KR_STOCK_MAP.items() if v == sym), sym)

                        results.append({
                            "ticker": sym, 
                            "name": name,
                            "price": close, "pct": pct
                        })
                except:
                    continue
        return results

    try:
        # Fetch Data
        idx_kr_results = process_tickers(indices_kr)
        idx_us_results = process_tickers(indices_us)
        
        rank_kr_results = process_rankings(popular_kr)
        rank_us_results = process_rankings(popular_us)
        
        # News
        news_data = getattr(yf.Search("Stock Market"), 'quotes', [])
        
        return {
            "kr": {"indices": idx_kr_results, "rankings": rank_kr_results},
            "us": {"indices": idx_us_results, "rankings": rank_us_results},
            "news": news_data
        }, None
    except Exception as e:
        return None, str(e)


def render_dashboard_section(data, key_prefix="kr"):
    """Render indices and rankings for a specific region (KR or US)."""
    if not data:
        st.info("No data available.")
        return

    # 1. Index Cards
    indices = data.get("indices", [])
    if indices:
        cols = st.columns(len(indices)) if len(indices) > 0 else [st.container()]
        for i, item in enumerate(indices):
            color = "#f85149" if item["delta"] < 0 else "#3fb950"
            with cols[i]:
                st.markdown(f"""
                <div class='dash-card'>
                    <div class='dash-index-title'>{item['name']}</div>
                    <div class='dash-index-val'>{item['val']:,.2f}</div>
                    <div class='dash-index-delta' style='color:{color}'>
                        {'▼' if item['delta'] < 0 else '▲'} {abs(item['delta']):,.2f} ({item['pct']:.2f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # 2. Stock Rankings
    st.markdown(f"<div class='dash-section-title'>{t('stock_rankings')}</div>", unsafe_allow_html=True)
    rankings = data.get("rankings", [])
    
    if rankings:
        r_cols = st.columns(3)
        rank_labels = [t('top_value'), t('top_gainers'), t('top_losers')]
        
        # Sort for Gainer/Loser columns
        gainers = sorted(rankings, key=lambda x: x['pct'], reverse=True)
        losers = sorted(rankings, key=lambda x: x['pct'])
        value = rankings # Mixed for variety (or sorted by volume if we had it, but here just default list)
        
        col_data = [value[:5], gainers[:5], losers[:5]]
        
        for i, data_list in enumerate(col_data):
            with r_cols[i]:
                st.markdown(f"<div style='color:#8b949e;font-size:13px;margin-bottom:12px;font-weight:600'>{rank_labels[i]}</div>", unsafe_allow_html=True)
                for idx, r in enumerate(data_list):
                    color = "#f85149" if r["pct"] < 0 else "#3fb950"
                    # Use st.button tailored to look like a list row
                    btn_label = f"{idx+1} \u2000 {r['name']} \u2000 | \u2000 {r['price']:,.2f} \u2000 | \u2000 {'▼' if r['pct'] < 0 else '▲'} {abs(r['pct']):.2f}%"
                    
                    # FIX: Do not update 'ticker_input' in session_state here to avoid StreamlitAPIException
                    if st.button(btn_label, key=f"rank_btn_{key_prefix}_{i}_{idx}", use_container_width=True):
                        st.session_state["auto_ticker"] = r['ticker']
                        st.rerun()

def render_home_dashboard():
    """Render the M-able Wide style home dashboard."""
    
    db_data, error = fetch_dashboard_data()
    if error:
        st.error(f"Dashboard error: {error}")
        return

    # ── Tabs for Domestic / Overseas ──
    tab_kr, tab_us = st.tabs([f"🇰🇷 {t('domestic')}", f"🇺🇸 {t('overseas')}"])

    with tab_kr:
        render_dashboard_section(db_data["kr"], key_prefix="kr")

    with tab_us:
        render_dashboard_section(db_data["us"], key_prefix="us")

    # ── News Highlights (Common) ──
    st.markdown(f"<div class='dash-section-title' style='margin-top:30px'>{t('news_highlights')}</div>", unsafe_allow_html=True)
    news_items = db_data.get("news", [])
    if news_items:
        n_cols = st.columns(3)
        for i in range(min(6, len(news_items))):
            item = news_items[i]
            title = item.get("shortname", "Market update...")
            with n_cols[i % 3]:
                st.markdown(f"""
                <div class='news-grid-item'>
                    <div class='news-grid-content'>
                        <div class='news-grid-title'>{title[:50]}...</div>
                        <div class='news-grid-meta'>Yahoo Finance · Live</div>
                    </div>
                    <div class='news-grid-logo'></div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No news highlights available.")


# ══════════════════════════════════════════════════════════════════════
# 5. HANDLE SUGGESTION CLICK  (must run BEFORE sidebar renders)
# ══════════════════════════════════════════════════════════════════════
if "auto_ticker" in st.session_state and st.session_state["auto_ticker"]:
    st.session_state["ticker_input"] = st.session_state["auto_ticker"]
    st.session_state["trigger_analysis"] = True
    del st.session_state["auto_ticker"]

# 6. SIDEBAR  (search · timeframe · language · quick-order)
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Language toggle at very top
    lang = st.selectbox(
        "🌐",
        options=["en", "ko"],
        format_func=lambda x: "English" if x == "en" else "한국어",
        index=0,
        key="lang",
    )

    st.markdown(
        f"<h2 style='text-align:center;color:#fff;font-weight:700;letter-spacing:1px;margin-top:8px'>"
        f"{t('app_title')}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;color:#8b949e;font-size:12px;margin-top:-12px;"
        f"text-transform:uppercase'>{t('app_subtitle')}</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:#30363d'>", unsafe_allow_html=True)

    # ── Search form ──
    with st.form("search_form"):
        st.subheader(t("symbol_header"))
        st.caption(t("symbol_hint"))
        ticker_symbol = st.text_input("Ticker", value="NVDA", label_visibility="collapsed", key="ticker_input").upper()

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader(t("timeframe"))
        period = st.select_slider(
            "Range",
            label_visibility="collapsed",
            options=["1mo", "3mo", "6mo", "1y", "3y", "5y", "max"],
            value="1y",
            format_func=lambda x: {
                "1mo": "1M", "3mo": "3M", "6mo": "6M",
                "1y": "1Y", "3y": "3Y", "5y": "5Y", "max": "ALL",
            }[x],
        )
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_button = st.form_submit_button(t("execute"), use_container_width=True)

    # ── Quick‑Order UI (demo) ──
    st.markdown("<hr style='border-color:#30363d'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='wts-card-title' style='border-bottom:none;padding-bottom:0'>"
        f"💹 {t('quick_order')}</div>",
        unsafe_allow_html=True,
    )
    order_type = st.radio(t("order_type"), [t("buy"), t("sell")], horizontal=True, label_visibility="collapsed")
    col_q, col_p = st.columns(2)
    with col_q:
        qty = st.number_input(t("quantity"), min_value=1, value=1, step=1)
    with col_p:
        order_price = st.number_input(t("price"), min_value=0.0, value=0.0, step=0.01, format="%.2f")

    if order_type == t("buy"):
        st.markdown("<div class='buy-btn'>", unsafe_allow_html=True)
        st.button(f"🟢 {t('buy')}", use_container_width=True, key="buy_btn")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sell-btn'>", unsafe_allow_html=True)
        st.button(f"🔴 {t('sell')}", use_container_width=True, key="sell_btn")
        st.markdown("</div>", unsafe_allow_html=True)

    st.caption(t("order_demo_msg"))


# ── Auto-resolve Korean names to tickers ──
raw_input = ticker_symbol  # preserve original for suggestions
resolved_ticker = ticker_symbol
force_trigger = st.session_state.get("trigger_analysis", False)

if (fetch_button or force_trigger) and ticker_symbol:
    if force_trigger:
        st.session_state["trigger_analysis"] = False
    
    # Direct dictionary lookup (exact match)
    if ticker_symbol in KR_STOCK_MAP:
        resolved_ticker = KR_STOCK_MAP[ticker_symbol]
    else:
        # Case-insensitive match
        for name, code in KR_STOCK_MAP.items():
            if name.upper() == ticker_symbol.upper():
                resolved_ticker = code
                break

if (fetch_button or force_trigger) and resolved_ticker:
    with st.spinner(t("processing").format(resolved_ticker)):
        data, error = fetch_stock_data(resolved_ticker, period)

        if error == "NOT_FOUND" or (error and "NOT_FOUND" in str(error)):
            st.error(t("ticker_not_found"))
            st.info(t("search_tip"))

            # Show suggestions
            suggestions = search_stock_suggestions(raw_input)
            if suggestions:
                st.markdown(f"### {t('search_suggest_title')}")
                st.markdown(t("search_suggest_desc"))
                suggest_cols = st.columns(min(len(suggestions), 3))
                for idx, (name, code) in enumerate(suggestions):
                    with suggest_cols[idx % 3]:
                        st.markdown(f"""
                        <div style='background:#161b22;border:1px solid #30363d;border-radius:6px;
                                    padding:12px;text-align:center;margin-bottom:8px'>
                            <div style='color:#ffffff;font-size:14px;font-weight:600'>{name}</div>
                            <div style='color:#58a6ff;font-size:12px;margin-top:4px'>{code}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"▶ {code}", key=f"suggest_{idx}", use_container_width=True):
                            st.session_state["auto_ticker"] = code
                            st.rerun()
            else:
                st.warning(t("search_no_suggest"))
        elif error:
            st.error(t("data_error").format(error))
        elif data:
            info = data["info"]
            hist = data["hist"]
            financials = data["financials"]
            news = data["news"]

            company_name = info.get("longName", info.get("shortName", ticker_symbol))
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            currency = info.get("currency", "USD")
            current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            previous_close = info.get("previousClose", 0)

            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close else 0

            # ── Company Header ──
            st.markdown(
                f"<div class='company-header'>{company_name} "
                f"<span style='color:#8b949e;font-size:20px;font-weight:500;margin-left:8px'>"
                f"{ticker_symbol}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='company-sub'>[ {sector} ] &nbsp; {industry} "
                f"&nbsp;|&nbsp; {currency}</div>",
                unsafe_allow_html=True,
            )

            # ── Key Metrics Row ──
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                st.metric(
                    label=t("current_price"),
                    value=f"{current_price:,.2f}",
                    delta=f"{price_change:,.2f} ({price_change_pct:,.2f}%)",
                )
            with mc2:
                market_cap = info.get("marketCap", 0)
                if market_cap >= 1e12:
                    cap_str = f"{market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    cap_str = f"{market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    cap_str = f"{market_cap/1e6:.2f}M"
                else:
                    cap_str = f"{market_cap:,}"
                st.metric(label=t("market_cap"), value=cap_str)
            with mc3:
                pe_ratio = info.get("trailingPE", "N/A")
                st.metric(
                    label=t("pe_ratio"),
                    value=f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio,
                )
            with mc4:
                pb_ratio = info.get("priceToBook", "N/A")
                st.metric(
                    label=t("price_to_book"),
                    value=f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio,
                )
            with mc5:
                vol = info.get("volume", info.get("regularMarketVolume", "N/A"))
                if isinstance(vol, (int, float)):
                    if vol >= 1e6:
                        vol_str = f"{vol/1e6:.1f}M"
                    else:
                        vol_str = f"{vol:,.0f}"
                else:
                    vol_str = str(vol)
                st.metric(label=t("volume_today"), value=vol_str)

            st.markdown("<br>", unsafe_allow_html=True)

            # ══════════════════════════════════════════════════════════
            # MAIN LAYOUT:  chart/data (left 70%)  |  info panel (right 30%)
            # ══════════════════════════════════════════════════════════
            main_col, info_col = st.columns([7, 3])

            # ──────────────────────────────────────────────────────────
            # LEFT:  TABS  (Chart · Financials · Analysis)
            # ──────────────────────────────────────────────────────────
            with main_col:
                tab1, tab2, tab3 = st.tabs([
                    f"📊 {t('technical_chart')}",
                    f"📋 {t('financial_data')}",
                    f"🔍 {t('analysis_signals')}",
                ])

                # ── TAB 1 : Technical Chart ──
                with tab1:
                    if not hist.empty:
                        # Compute SMAs
                        hist["SMA20"] = hist["Close"].rolling(window=20).mean()
                        hist["SMA50"] = hist["Close"].rolling(window=50).mean()

                        fig = make_subplots(
                            rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_heights=[0.75, 0.25],
                        )

                        # Candlestick
                        fig.add_trace(
                            go.Candlestick(
                                x=hist.index,
                                open=hist["Open"],
                                high=hist["High"],
                                low=hist["Low"],
                                close=hist["Close"],
                                increasing_line_color="#3fb950",
                                increasing_fillcolor="#3fb950",
                                decreasing_line_color="#f85149",
                                decreasing_fillcolor="#f85149",
                                name="Price",
                            ),
                            row=1, col=1,
                        )

                        # SMA 20
                        fig.add_trace(
                            go.Scatter(
                                x=hist.index,
                                y=hist["SMA20"],
                                mode="lines",
                                line=dict(color="#58a6ff", width=1.2),
                                name=t("sma20"),
                            ),
                            row=1, col=1,
                        )

                        # SMA 50
                        fig.add_trace(
                            go.Scatter(
                                x=hist.index,
                                y=hist["SMA50"],
                                mode="lines",
                                line=dict(color="#d2a8ff", width=1.2),
                                name=t("sma50"),
                            ),
                            row=1, col=1,
                        )

                        # Volume bars
                        colors = [
                            "#3fb950" if c >= o else "#f85149"
                            for c, o in zip(hist["Close"], hist["Open"])
                        ]
                        fig.add_trace(
                            go.Bar(
                                x=hist.index,
                                y=hist["Volume"],
                                marker_color=colors,
                                opacity=0.55,
                                name=t("volume"),
                            ),
                            row=2, col=1,
                        )

                        fig.update_layout(
                            height=560,
                            margin=dict(l=0, r=0, t=10, b=0),
                            xaxis_rangeslider_visible=False,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="left",
                                x=0,
                                font=dict(size=11, color="#8b949e"),
                            ),
                            xaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, color="#8b949e"),
                            xaxis2=dict(showgrid=True, gridcolor="#21262d", zeroline=False, color="#8b949e"),
                            yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, color="#8b949e", side="right"),
                            yaxis2=dict(showgrid=True, gridcolor="#21262d", zeroline=False, color="#8b949e", side="right"),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(t("no_chart"))

                # ── TAB 2 : Financials ──
                with tab2:
                    if not financials.empty:
                        # 1. Visualization of Trends
                        st.markdown(f"### {t('growth_analysis')}")
                        
                        # Prepare data for plotting
                        # financials is Ticker.financials, usually indexed by account name, columns are dates
                        try:
                            # Extract Revenue and Net Income
                            # Note: yfinance account names can vary slightly, so we use common keywords
                            fin_t = financials.T
                            rev_key = next((k for k in fin_t.columns if 'Total Revenue' in k or 'Revenue' in k), None)
                            ni_key = next((k for k in fin_t.columns if 'Net Income' in k), None)
                            op_key = next((k for k in fin_t.columns if 'Operating Income' in k), None)

                            if rev_key and ni_key:
                                # Reverse to show chronological order
                                plot_df = fin_t[[rev_key, ni_key]].iloc[::-1]
                                
                                fig_fin = go.Figure()
                                fig_fin.add_trace(go.Bar(
                                    x=plot_df.index.astype(str),
                                    y=plot_df[rev_key],
                                    name=t('revenue_label'),
                                    marker_color='#58a6ff'
                                ))
                                fig_fin.add_trace(go.Bar(
                                    x=plot_df.index.astype(str),
                                    y=plot_df[ni_key],
                                    name=t('net_income_label'),
                                    marker_color='#3fb950'
                                ))
                                
                                fig_fin.update_layout(
                                    height=350,
                                    barmode='group',
                                    template="plotly_dark",
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(l=0, r=0, t=30, b=0),
                                    xaxis=dict(showgrid=False, color="#8b949e"),
                                    yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"),
                                    legend=dict(orientation="h", y=1.1)
                                )
                                st.plotly_chart(fig_fin, use_container_width=True)
                                
                                # 2. Key Calculated Metrics
                                c1, c2, c3, c4 = st.columns(4)
                                
                                # YoY Revenue Growth
                                if len(plot_df) >= 2:
                                    last_rev = plot_df[rev_key].iloc[-1]
                                    prev_rev = plot_df[rev_key].iloc[-2]
                                    rev_growth = ((last_rev - prev_rev) / prev_rev * 100) if prev_rev != 0 else 0
                                    c1.metric(t("yoy_growth"), f"{rev_growth:,.1f}%", f"{rev_growth:,.1f}%")
                                    
                                    # Operating Margin
                                    if op_key:
                                        last_op = plot_df[op_key].iloc[-1] if op_key in plot_df.columns else fin_t[op_key].iloc[0]
                                        op_margin = (last_op / last_rev * 100) if last_rev != 0 else 0
                                        c2.metric(t("op_margin"), f"{op_margin:,.1f}%")
                                        
                                    # Net Margin
                                    last_ni = plot_df[ni_key].iloc[-1]
                                    net_margin = (last_ni / last_rev * 100) if last_rev != 0 else 0
                                    c3.metric(t("net_margin"), f"{net_margin:,.1f}%")

                                # 3. Contextual Summary
                                summary_text = f"**{t('financial_summary')}**<br>"
                                if len(plot_df) >= 2:
                                    rev_up = plot_df[rev_key].iloc[-1] > plot_df[rev_key].iloc[-2]
                                    ni_up = plot_df[ni_key].iloc[-1] > plot_df[ni_key].iloc[-2]
                                    
                                    if rev_up and ni_up:
                                        summary_text += f"- {t('trend_improving')}<br>"
                                    elif not rev_up and not ni_up:
                                        summary_text += f"- {t('trend_declining')}<br>"
                                    else:
                                        summary_text += f"- {t('trend_stable')}<br>"
                                
                                st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.debug(f"Analysis error: {e}")

                        # 4. Raw Data View
                        with st.expander(t("financial_data")):
                            fin_display = financials.copy()
                            fin_display.columns = [str(c).split(" ")[0] for c in fin_display.columns]
                            st.dataframe(
                                fin_display.style.format("{:,.0f}"),
                                use_container_width=True,
                                height=400,
                            )
                    else:
                        st.warning(t("no_financials"))

                # ── TAB 3 : Analysis & Signals ──
                with tab3:
                    target_price = info.get("targetMeanPrice", "N/A")
                    target_high = info.get("targetHighPrice", "N/A")
                    target_low = info.get("targetLowPrice", "N/A")
                    recommendation = info.get("recommendationKey", "N/A").upper().replace("_", " ")
                    fifty_two_w_high = info.get("fiftyTwoWeekHigh", "N/A")
                    fifty_two_w_low = info.get("fiftyTwoWeekLow", "N/A")
                    analyst_count = info.get("numberOfAnalystOpinions", "N/A")

                    is_buy = "BUY" in recommendation or "OUTPERFORM" in recommendation
                    is_sell = "SELL" in recommendation or "UNDERPERFORM" in recommendation
                    signal_color = "#3fb950" if is_buy else ("#f85149" if is_sell else "#d2a8ff")

                    ac1, ac2 = st.columns(2)

                    with ac1:
                        st.markdown(f"""
                        <div class='wts-card'>
                            <div class='wts-card-title'>{t('market_consensus')}</div>
                            <div class='wts-row'>
                                <span class='wts-label'>{t('recommendation')}</span>
                                <span class='wts-value' style='color:{signal_color}'>{recommendation}</span>
                            </div>
                            <div class='wts-row'>
                                <span class='wts-label'>{t('analyst_coverage')}</span>
                                <span class='wts-value'>{analyst_count} {t('analysts')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with ac2:
                        st.markdown(f"""
                        <div class='wts-card'>
                            <div class='wts-card-title'>{t('price_targets')}</div>
                            <div class='wts-row'>
                                <span class='wts-label'>{t('mean_target')}</span>
                                <span class='wts-value' style='color:#58a6ff'>{target_price} {currency}</span>
                            </div>
                            <div class='wts-row'>
                                <span class='wts-label'>{t('low_target')}</span>
                                <span class='wts-value'>{target_low}</span>
                            </div>
                            <div class='wts-row'>
                                <span class='wts-label'>{t('high_target')}</span>
                                <span class='wts-value'>{target_high}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # 52-week range with visual bar
                    range_pct = 50
                    if isinstance(fifty_two_w_low, (int, float)) and isinstance(fifty_two_w_high, (int, float)):
                        span = fifty_two_w_high - fifty_two_w_low
                        if span > 0 and isinstance(current_price, (int, float)):
                            range_pct = max(0, min(100, ((current_price - fifty_two_w_low) / span) * 100))

                    st.markdown(f"""
                    <div class='wts-card'>
                        <div class='wts-card-title'>{t('week52_range')}</div>
                        <div class='wts-row'>
                            <span class='wts-label'>{t('week52_low')}: <strong style='color:#fff'>{fifty_two_w_low}</strong></span>
                            <span class='wts-label'>{t('week52_high')}: <strong style='color:#fff'>{fifty_two_w_high}</strong></span>
                        </div>
                        <div class='range-bar'>
                            <div class='range-marker' style='left:{range_pct}%'></div>
                        </div>
                        <div style='text-align:center'>
                            <span class='wts-label'>{t('current')}: <strong style='color:#58a6ff'>{current_price}</strong></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ── Fundamental Summary ──
                    summary_parts = []
                    if isinstance(pe_ratio, (int, float)):
                        if pe_ratio < 0:
                            summary_parts.append(f"- **Valuation:** {t('val_negative')}")
                        elif pe_ratio < 15:
                            summary_parts.append(f"- **Valuation:** {t('val_under15')}")
                        elif pe_ratio > 30:
                            summary_parts.append(f"- **Valuation:** {t('val_over30')}")
                        else:
                            summary_parts.append(f"- **Valuation:** {t('val_moderate')}")

                    if isinstance(target_price, (int, float)) and isinstance(current_price, (int, float)) and current_price > 0:
                        upside = ((target_price - current_price) / current_price) * 100
                        if upside > 10:
                            summary_parts.append(f"- **Target:** {t('target_upside').format(upside)}")
                        elif upside < -10:
                            summary_parts.append(f"- **Target:** {t('target_downside').format(abs(upside))}")
                        else:
                            summary_parts.append(f"- **Target:** {t('target_near').format(upside)}")

                    div_yield = info.get("dividendYield", 0)
                    if isinstance(div_yield, (int, float)) and div_yield > 0:
                        summary_parts.append(f"- **Income:** {t('income_yield').format(div_yield * 100)}")

                    if summary_parts:
                        header = f"**{t('sys_assessment').format(company_name, ticker_symbol)}**<br><br>"
                        body = "<br>".join(summary_parts)
                        st.markdown(f"<div class='summary-box'>{header}{body}</div>", unsafe_allow_html=True)

            # ──────────────────────────────────────────────────────────
            # RIGHT:  INFO PANEL  (consensus summary · news feed)
            # ──────────────────────────────────────────────────────────
            with info_col:
                # ── Compact Consensus Card ──
                recommendation = info.get("recommendationKey", "N/A").upper().replace("_", " ")
                is_buy = "BUY" in recommendation or "OUTPERFORM" in recommendation
                is_sell = "SELL" in recommendation or "UNDERPERFORM" in recommendation
                signal_color = "#3fb950" if is_buy else ("#f85149" if is_sell else "#d2a8ff")
                target_price_val = info.get("targetMeanPrice", "N/A")

                st.markdown(f"""
                <div class='wts-card'>
                    <div class='wts-card-title'>{t('market_consensus')}</div>
                    <div style='text-align:center;padding:8px 0'>
                        <div style='font-size:28px;font-weight:700;color:{signal_color}'>{recommendation}</div>
                        <div style='color:#8b949e;font-size:11px;margin-top:4px'>{t('analyst_coverage')}: {info.get('numberOfAnalystOpinions','N/A')} {t('analysts')}</div>
                    </div>
                    <div class='wts-row' style='margin-top:6px'>
                        <span class='wts-label'>{t('mean_target')}</span>
                        <span class='wts-value' style='color:#58a6ff'>{target_price_val} {currency}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── 52W compact ──
                fifty_two_w_high = info.get("fiftyTwoWeekHigh", "N/A")
                fifty_two_w_low = info.get("fiftyTwoWeekLow", "N/A")
                range_pct = 50
                if isinstance(fifty_two_w_low, (int, float)) and isinstance(fifty_two_w_high, (int, float)):
                    span = fifty_two_w_high - fifty_two_w_low
                    if span > 0 and isinstance(current_price, (int, float)):
                        range_pct = max(0, min(100, ((current_price - fifty_two_w_low) / span) * 100))

                st.markdown(f"""
                <div class='wts-card'>
                    <div class='wts-card-title'>{t('week52_range')}</div>
                    <div class='wts-row'>
                        <span class='wts-label'>{t('week52_low')}</span>
                        <span class='wts-value'>{fifty_two_w_low}</span>
                    </div>
                    <div class='range-bar'>
                        <div class='range-marker' style='left:{range_pct}%'></div>
                    </div>
                    <div class='wts-row'>
                        <span class='wts-label'>{t('week52_high')}</span>
                        <span class='wts-value'>{fifty_two_w_high}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Dividend ──
                div_yield = info.get("dividendYield", 0)
                if isinstance(div_yield, (int, float)) and div_yield > 0:
                    st.markdown(f"""
                    <div class='wts-card'>
                        <div class='wts-row'>
                            <span class='wts-label'>{t('div_yield_label')}</span>
                            <span class='wts-value' style='color:#3fb950'>{div_yield*100:.2f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # ── News Feed ──
                st.markdown(f"""
                <div class='wts-card'>
                    <div class='wts-card-title'>📰 {t('news_feed')}</div>
                """, unsafe_allow_html=True)

                if news:
                    news_html = ""
                    for item in news:
                        link = item["link"] if item["link"] else "#"
                        news_html += f"""
                        <div class='news-item'>
                            <a href='{link}' target='_blank'>{item['title']}</a>
                            <div class='news-meta'>{item['publisher']} · {item['date']}</div>
                        </div>
                        """
                    news_html += f"<p style='color:#484f58;font-size:10px;margin-top:8px'>{t('news_ref')}</p>"
                    st.markdown(news_html + "</div>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<p class='wts-label' style='padding:8px 0'>{t('no_news')}</p></div>",
                        unsafe_allow_html=True,
                    )

else:
    if not fetch_button:
        # ── Dashboard (M-able Wide style) ──
        render_home_dashboard()
