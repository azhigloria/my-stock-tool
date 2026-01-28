import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面设置：采用适合散户阅读的清爽风格
st.set_page_config(page_title="老股民对比笔记", layout="wide")

# 2. 自定义样式：让界面像精美的投资笔记
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    .note-card { background-color: #ffffff; padding: 25px; border-radius: 20px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-left: 8px solid #4CAF50; margin-bottom: 25px; }
    .tag { background-color: #ff4b4b; color: white; padding: 4px 12px; border-radius: 50px; font-size: 14px; font-weight: bold; }
    .advice-title { color: #1e88e5; font-size: 22px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 核心：中文名称映射字典（如果你的股票没变中文，可以在这里手动添加）
CN_NAMES = {
    "Kweichow Moutai": "贵州茅台", "Wanhua Chemical": "万华化学", "Hualu-Hengsheng": "华鲁恒升",
    "Yoke Technology": "雅克科技", "Ping An Insurance": "中国平安", "Contemporary Amperex": "宁德时代",
    "Siyuan Electric": "思源电气", "BYD": "比亚迪", "Tencent": "腾讯控股", "Alibaba": "阿里巴巴"
}

def translate_name(name, symbol):
    for en, cn in CN_NAMES.items():
        if en.lower() in name.lower(): return cn
    # 如果找不到，尝试去掉拼音后的冗余词
    clean_name = name.replace("Co.,Ltd", "").replace("Group", "").strip()
    return clean_name

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
        
        # 抓取真实核心指标
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分计算 (1-10分)
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)), # 便宜度
            max(1, min(10, roe/3)), # 赚钱底气
            max(1, min(10, div*200)), # 回本快慢
            max(1, min(10, 10 - debt/20)), # 抗跌能力
            max(1, min(10, growth*5)) # 增长潜力
        ]
        
        return {
            "name": name, "code": code, "pe": pe, "roe": roe, "div": div, "growth": growth, "scores": scores
        }
    except Exception as e:
        return None

# 3. 侧边栏：输入区域
st.sidebar.header("✍️ 记录你想对比的代码")
input_codes = st.sidebar.text_input("代码(如: 600309, 600519)", "600309, 600519")

if st.sidebar.button("开始分析"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = []
    with st.spinner('正在调取实时账本...'):
        for c in codes:
            res = get_retail_analysis(c)
            if res: results.append(res)
    
    if results:
        # 第一部分：雷达图
        st.subheader("🟢 强弱分布一览")
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()
        for r in results:
            fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
        st.plotly_chart(fig, use_container_width=True)

        # 第二部分：个性化建议（这就是你想要的“大白话”理由）
        st.subheader("💡 理性选择建议")
        for r in results:
            with st.container():
                st.markdown(f'<div class="note-card">', unsafe_allow_html=True)
                # 修正了这里之前漏掉的括号！
                st.markdown(f'<span class="tag">股票代码: {r["code"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="advice-title">{r["name"]}</div>', unsafe_allow_html=True)
                
                # 画像逻辑判断
                if r['scores'][2] > 6:
                    st.write("💰 **适合人群：追求领退休金的“收租公”**")
                    st.write(f"**理由：** 它的分红率高达 {r['div']:.2f}%。这种公司像是不动产，如果你不想折腾，只想每年领钱，它是首选。")
                elif r['scores'][4] > 7:
                    st.write("🚀 **适合人群：想要翻倍体感的“进取型玩家”**")
                    st.write(f"**理由：** 营收增长高达 {r['growth']:.1f}%。公司正处于跑马圈地阶段，股价弹性大，适合能承受波动的年轻人。")
                elif r['scores'][0] > 7:
                    st.write("💎 **适合人群：爱捡漏的“价值投资者”**")
                    st.write(f"**理由：** 估值仅 {r['pe']:.1f} 倍。现在价格被低估了，如果你有耐心等它价值回归，现在是‘捡便宜’的好机会。")
                else:
                    st.write("⚖️ **适合人群：均衡配置的“稳健派”**")
                    st.write(f"**理由：** 各项数据都很平衡，没有明显短板。适合作为你账户里的‘压舱石’，陪着公司慢慢长大。")
                
                st.markdown('</div>', unsafe_allow_html=True)

        # 第三部分：总结陈词
        st.success(f"📊 **快速总结：** 追求安全感选 **{sorted(results, key=lambda x: x['scores'][3], reverse=True)[0]['name']}**；追求爆发力选 **{sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]['name']}**。")
    else:
        st.error("暂时没抓到数据。可能是网络原因，请稍后再点一下‘开始分析’。")
