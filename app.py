import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 页面配置
st.set_page_config(page_title="散户炒股对比工具", layout="wide")
st.title("📊 散户自选股大白话对比")

# 处理 A 股代码逻辑
def handle_code(code):
    code = code.strip()
    if code.isdigit():
        if code.startswith('6'): return f"{code}.SS"
        else: return f"{code}.SZ"
    return code

# 获取数据并转换为大白话维度
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. 便宜程度 (基于 PE)
        pe = info.get('forwardPE') or info.get('trailingPE') or 50
        cheapness = max(0, min(10, 10 - (pe / 10))) # 简化的标准化逻辑
        
        # 2. 赚钱底气 (ROE)
        roe = info.get('returnOnEquity', 0) * 100
        strength = max(0, min(10, roe / 2))
        
        # 3. 回本快慢 (股息率)
        div = info.get('dividendYield', 0) * 1000
        cash_back = max(0, min(10, div))
        
        # 4. 抗跌能力 (资产负债率反向)
        debt = info.get('debtToEquity', 100)
        safety = max(0, min(10, 10 - (debt / 20)))
        
        # 5. 增长潜力
        growth = info.get('revenueGrowth', 0) * 100
        potential = max(0, min(10, growth / 5))

        return {
            "name": info.get('shortName', symbol),
            "data": [cheapness, strength, cash_back, safety, potential]
        }
    except:
        return None

# 侧边栏输入
st.sidebar.header("输入股票代码")
input_codes = st.sidebar.text_input("输入代码（逗号隔开，如：600519, 000858, AAPL）", "600519, 000858")
codes = [handle_code(c) for c in input_codes.split(',')]

# 绘图逻辑
if st.sidebar.button("开始分析"):
    all_data = []
    for c in codes:
        res = get_stock_data(c)
        if res: all_data.append(res)
    
    if all_data:
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()

        for d in all_data:
            fig.add_trace(go.Scatterpolar(r=d['data'], theta=categories, fill='toself', name=d['name']))

        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("💡 老股民大白话总结")
        for d in all_data:
            st.write(f"**{d['name']}**：这个票的‘{'赚钱底气' if d['data'][1]>7 else '抗跌能力'}’表现最突出。建议关注它在行业里的位置。")
    else:
        st.error("没抓到数据，请检查代码输入是否正确（A股直接输数字即可）。")
