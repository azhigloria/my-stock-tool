import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面配置
st.set_page_config(page_title="散户深度选股笔记", layout="wide")

# 2. 自定义样式
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 25px; border-top: 5px solid #4CAF50; }
    .section-title { color: #2c3e50; font-size: 26px; font-weight: bold; margin: 30px 0 15px 0; border-bottom: 2px solid #eee; }
    .recommend-card { background-color: #f9fbf9; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; height: 100%; }
    .highlight-text { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 中文名映射字典
CN_NAMES = {
    "600519": "贵州茅台", "600309": "万华化学", "600426": "华鲁恒升",
    "002409": "雅克科技", "002028": "思源电气", "300750": "宁德时代"
}

def get_pro_data(code):
    symbol = code.strip()
    pure_code = "".join(filter(str.isdigit, symbol))
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        name = CN_NAMES.get(pure_code, info.get('shortName', symbol))
        
        # 指标抓取
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分逻辑
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), 
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*8))
        ]
        
        # 深度逻辑生成
        if roe > 15:
            logic = "典型的“白马股”。依靠极强的品牌力或成本护城河实现超额利润。"
            advantage = "经营极其稳健，抗风险能力强，分红相对稳定，是时间的朋友。"
        else:
            logic = "典型的“周期/成长股”。业绩受行业景气度影响大，需关注国产替代或扩产节奏。"
            advantage = "资产质量尚可，管理层执行力强，正处于行业地位爬坡期。"

        risk = "盘子较大，股价受全球宏观经济影响显著。" if pe > 25 else "行业竞争加剧可能导致毛利承压，需关注新产能释放。"

        return {
            "name": name, "code": pure_code, "pe": pe, "roe": roe, "div": div, "growth": growth,
            "scores": scores, "logic": logic, "advantage": advantage, "risk": risk
        }
    except Exception as e:
        return None

st.title("🍎 深度研报对比：让投资回归理性")

# 侧边栏
st.sidebar.header("📝 输入对比组合")
input_codes = st.sidebar.text_input("代码(如: 600309, 600426, 002409)", "600309, 600426, 002409")

if st.sidebar.button("生成深度研报"):
    codes =
