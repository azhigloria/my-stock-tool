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
        advantage = "经营稳健，抗风险能力极强，是时间的朋友。" if debt < 50 else "财务杠杆利用充分，处于快速扩张期。"
        risk = "盘子较大，股价容易随大盘波动。" if pe > 30 else "行业天花板可见，需关注新业务增长点。"

        return {
            "name": name, "code": code, "pe": pe, "roe": roe, "div": div, "growth": growth, "debt": debt,
            "scores": scores, "logic": logic, "advantage": advantage, "risk": risk
        }
    except: return None

# 3. 侧边栏
st.sidebar.header("📝 输入自选组合")
input_codes = st.sidebar.text_input("代码(如: 600309, 600519)", "600309, 600519, 002028")

if st.sidebar.button("生成深度研究报告"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = [get_pro_analysis(c) for c in codes if get_pro_analysis(c)]
    
    if results:
        # 第一模块：公司画像与可视化
        st.markdown('<div class="section-title">1. 公司画像与核心竞争力对比</div>', unsafe_allow_html=True)
        col_chart, col_table = st.columns([1, 1])
        with col_chart:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col_table:
            df = pd.DataFrame(results)[["name", "pe", "roe", "div"]]
            df.columns = ["公司名称", "市盈率", "盈利能力(ROE)", "股息率"]
            st.table(df)

        # 第二模块：深度逻辑剖析
        st.markdown('<div class="section-title">2. 深度对比分析</div>', unsafe_allow_html=True)
        for r in results:
            with st.container():
                st.markdown(f"### {r['name']}：{'行业领跑者' if r['roe']>15 else '效率机器'}")
                st.markdown(f"""
                * **逻辑：** {r['logic']}
                * **优点：** {r['advantage']} 指标显示，ROE 为 **{r['roe']:.1f}%**。
                * **风险：** {r['risk']} 目前市盈率为 **{r['pe']:.1f}** 倍。
                """)
                st.write("---")

        # 第三模块：理性选择建议
        st.markdown('<div class="section-title">3. 理性选择建议</div>', unsafe_allow_html=True)
        st.write("根据不同的投资画像，你可以参考以下结论：")
        
        best_value = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
        best_growth = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
        best_safety = sorted(results, key=lambda x: x['scores'][3], reverse=True)[0]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="recommend-card"><b>偏好价值与安全边际：</b><br/>优先选择 <b>{best_value["name"]}</b>。它估值低，安全垫厚。</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="recommend-card"><b>偏好成长与高收益：</b><br/>优先选择 <b>{best_growth["name"]}</b>。它扩张极快，弹性大。</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="recommend-card"><b>偏好分红与长线养老：</b><br/>优先选择 <b>{best_safety["name"]}</b>。它现金流稳，是压仓石。</div>', unsafe_allow_html=True)
    else:
        st.error("未获取到数据，请检查网络或代码。")
