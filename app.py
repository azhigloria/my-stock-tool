import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import re

# --- 1. 核心 AI 配置 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_path = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_path)
except Exception as e:
    st.error(f"AI 配置失败，请检查 Secrets: {e}")
    st.stop()

# --- 2. 页面样式 ---
st.set_page_config(page_title="Gemini 极简投资助手", layout="wide")
st.markdown("""
    <style>
    .report-container { background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eee; }
    .stMarkdown h3 { color: #1a73e8; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 极简数据抓取 ---
def get_stock_data(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else: symbol_yf = symbol
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        # 抓取原始名，即使是英文也没关系，后面交给 AI 处理
        return {
            "name": info.get('shortName') or info.get('longName') or symbol,
            "code": symbol,
            "pe": info.get('trailingPE', 0),
            "roe": info.get('returnOnEquity', 0) * 100,
            "growth": info.get('revenueGrowth', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100,
            "debt": info.get('debtToEquity', 0)
        }
    except: return None

# --- 4. 主界面 ---
st.title("🍎 Gemini 极简结构化研报")
st.caption("实时财报数据 + Gemini 逻辑内核 | 遵循《三大化工股对比分析》框架")

with st.sidebar:
    st.header("🔍 配置")
    user_input = st.text_input("代码(逗号分隔)", "600519, 002028")
    analyze_btn = st.button("🚀 启动研判")

if analyze_btn:
    codes = [c.strip() for c in user_input.split(',')]
    raw_results = [get_stock_data(c) for c in codes if get_stock_data(
