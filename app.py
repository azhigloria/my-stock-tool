import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面设置
st.set_page_config(page_title="老股民对比笔记", layout="wide")

# 2. 更加柔和的样式
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    .note-card { background-color: #ffffff; padding: 25px; border-radius: 20px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-left: 8px solid #4CAF50; margin-bottom: 25px; }
    .tag { background-color: #ff4b4b; color: white; padding: 4px 12px; border-radius: 50px; font-size: 14px; font-weight: bold; }
    .advice-title { color: #1e88e5; font-size: 22px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 中文名称映射表（常用 A 股）
CN_NAMES = {
    "Kweichow Moutai": "贵州茅台",
    "Wanhua Chemical": "万华化学",
    "Hualu-Hengsheng": "华鲁恒升",
    "Yoke Technology": "雅克科技",
    "Ping An Insurance": "中国平安",
    "Contemporary Amperex": "宁德时代",
    "Siyuan Electric": "思源电气",
    "BYD": "比亚迪"
}

def translate_name(name, symbol):
    # 先查表，查不到则尝试清理常见的拼音后缀
    for en, cn in CN_NAMES.items():
        if en in name: return cn
    return name.split(' ')[0] # 实在没有就取第一个单词

st.title("🍎 散户选股笔记：一眼看穿好公司")

def get_retail_analysis(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        raw_name = info.get('shortName', symbol)
        name = translate_name(raw_name, code)
        
        # 核心指标
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分计算
        scores = [
            max(1, min(10, 50/pe*5 if pe>0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), # 股息率放大系数
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*5))
        ]
        
        return {
            "name": name,
            "code": code,
            "pe": pe, "roe": roe, "div": div, "growth": growth,
            "scores": scores
        }
    except:
        return None

# 侧边栏
st.sidebar.header("✍️ 记录你想对比的代码")
input_codes = st.sidebar.text_input("代码(如: 600309, 600519)", "600309, 600519")

if st.sidebar.button("开始对比"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = []
    with st.spinner('老股民翻账本中...'):
        for c in codes:
            res = get_retail_analysis(c)
            if res: results.append(res)
    
    if results:
        # 雷达图
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()
        for r in results:
            fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("💡 理性选择建议")
        
        # 动态生成投资画像建议
        for r in results:
            with st.container():
                st.markdown(f'<div class="note-card">', unsafe_allow_html=True)
                st.markdown(f'<span class="tag">股票代码: {r["code"]}</span>',
