import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面设置
st.set_page_config(page_title="散户深度选股笔记", layout="wide")

# 2. 自定义样式：打造“深度研报”既视感
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .report-card { background-color: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 30px; }
    .section-title { color: #2c3e50; font-size: 24px; font-weight: bold; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; margin-bottom: 20px; }
    .highlight-box { background-color: #f1f8e9; padding: 15px; border-radius: 8px; border-left: 5px solid #4CAF50; margin: 10px 0; }
    .recommend-card { background-color: #fff3e0; padding: 15px; border-radius: 8px; border-left: 5px solid #ff9800; }
    </style>
    """, unsafe_allow_html=True)

# 中文名映射字典
CN_NAMES = {
    "Kweichow Moutai": "贵州茅台", "Wanhua Chemical": "万华化学", "Hualu-Hengsheng": "华鲁恒升",
    "Yoke Technology": "雅克科技", "Siyuan Electric": "思源电气", "Contemporary Amperex": "宁德时代"
}

def get_pro_analysis(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        raw_name = info.get('shortName', symbol)
        name = next((v for k, v in CN_NAMES.items() if k.lower() in raw_name.lower()), raw_name.split(' ')[0])
        
        # 核心指标抓取
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分计算
        scores = [
            max(1, min(10, 50/pe*5 if pe>0 else 2)), # 便宜程度
            max(1, min(10, roe/3)), # 赚钱底气
            max(1, min(10, div*200)), # 回本快慢
            max(1, min(10, 10 - debt/20)), # 抗跌能力
            max(1, min(10, growth*8)) # 增长潜力
        ]
        
        # 深度逻辑生成
        logic = "由于其高ROE，它是典型的白马股。公司正在核心领域扩张，成本控制极强。" if roe > 15 else "业务受行业周期影响大。只要行业利差存在，它就能靠效率赚到钱。"
        advantage = "经营稳健，抗风险能力极强，是时间
