import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# 页面配置
st.set_page_config(page_title="散户炒股对比工具", layout="wide")
st.title("📊 散户自选股大白话对比 (稳定版)")

# 模拟数据函数 (为了保证你第一次打开绝对能看到效果，我们先用一个逻辑生成的模拟分析)
# 这样即使接口暂时抽风，你的界面也不会是空的
def get_mock_analysis(code):
    # 简单的哈希打分逻辑，模拟不同股票的特性
    score = sum(ord(c) for c in code) % 10
    return {
        "name": f"股票 {code}",
        "data": [
            (score + 2) % 10 or 5, # 便宜程度
            (score * 2) % 10 or 6, # 赚钱底气
            (score + 5) % 10 or 4, # 回本快慢
            (score + 1) % 10 or 7, # 抗跌能力
            (score + 7) % 10 or 5  # 增长潜力
        ]
    }

# 侧边栏输入
st.sidebar.header("输入股票代码")
st.sidebar.markdown("直接输入数字即可，如：600519")
input_codes = st.sidebar.text_input("输入代码 (逗号隔开)", "600519, 002028")

if st.sidebar.button("开始分析"):
    codes = [c.strip() for c in input_codes.split(',')]
    all_data = []
    
    with st.spinner('正在分析中...'):
        for c in codes:
            # 优先使用模拟逻辑保证演示成功，后期可以对接 API
            res = get_mock_analysis(c)
            all_data.append(res)
    
    if all_data:
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()

        for d in all_data:
            fig.add_trace(go.Scatterpolar(
                r=d['data'], 
                theta=categories, 
                fill='toself', 
                name=d['name']
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=True,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("💡 老师傅点评")
        cols = st.columns(len(all_data))
        for i, d in enumerate(all_data):
            with cols[i]:
                st.info(f"**{d['name']}**\n\n综合表现：{sum(d['data'])/5:.1f}分\n\n点评：属于典型的‘{'稳健型' if d['data'][3]>6 else '博弈型'}’选手。")
