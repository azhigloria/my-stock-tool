import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面样式配置
st.set_page_config(page_title="散户深度选股笔记", layout="wide")

st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #4CAF50; margin-bottom: 20px; }
    .section-title { color: #2c3e50; font-size: 24px; font-weight: bold; margin: 25px 0 15px 0; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .recommend-card { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border: 1px solid #eef2ee; height: 100%; }
    .highlight-text { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 中文名字典
CN_NAMES = {
    "600519": "贵州茅台", "600309": "万华化学", "600426": "华鲁恒升",
    "002409": "雅克科技", "002028": "思源电气", "300750": "宁德时代"
}

def get_pro_data(code):
    symbol = code.strip()
    pure_code = "".join(filter(str.isdigit, symbol))
    # 自动补全 A 股后缀
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        name = CN_NAMES.get(pure_code, info.get('shortName', symbol))
        
        # 数据抓取
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分模型 (1-10分)
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), 
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*8))
        ]
        
        # 文本逻辑模版
        if roe > 15:
            logic, adv = "典型的“白马股”，靠护城河赚取超额利润。", "经营稳健，是长线“时间的朋友”。"
        else:
            logic, adv = "典型的“周期/成长股”，受行业景气度驱动。", "资产质量尚可，正处于地位爬坡期。"
        
        risk = "估值较高，需警惕回调。" if pe > 30 else "需关注新产能释放节奏。"

        return {
            "name": name, "code": pure_code, "pe": pe, "roe": roe, "div": div, 
            "growth": growth, "scores": scores, "logic": logic, "adv": adv, "risk": risk
        }
    except:
        return None

st.title("🍎 深度研报对比：让投资回归理性")

# 侧边栏
st.sidebar.header("📝 输入对比组合")
user_input = st.sidebar.text_input("代码(如: 600309, 600426, 002409)", "600309, 600426, 002409")

if st.sidebar.button("生成深度研报"):
    # 修复了这里的赋值逻辑
    codes_list = [c.strip() for c in user_input.split(',')]
    results = [get_pro_data(c) for c in codes_list]
    results = [r for r in results if r is not None]
    
    if results:
        # 模块 1: 画像
        st.markdown('<div class="section-title">1. 公司画像与核心竞争力</div>', unsafe_allow_html=True)
        cols = st.columns(len(results))
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f'<div class="report-card">**{r["name"]} ({r["code"]})**<br/><small>{r["adv"]}</small></div>
