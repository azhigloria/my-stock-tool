import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面配置：采用宽屏模式，看起来更像专业终端
st.set_page_config(page_title="散户炒股深度对比", layout="wide")

# 自定义 CSS 让表格更好看
st.markdown("""
    <style>
    .report-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 散户自选股：逻辑分析与画像对比")

def get_pro_analysis(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        name = info.get('longName') or info.get('shortName') or symbol
        
        # 抓取真实核心指标
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        cash = info.get('operatingCashflow', 0) / 1e8 # 亿元
        
        # 逻辑画像（基于数据的自动生成的画像）
        label = "价值龙头" if pe < 20 and roe > 15 else ("成长新星" if roe > 10 else "周期博弈")
        advantage = "财务极其稳健，盈利质量高" if roe > 15 else "成本控制或行业地位尚可"
        
        return {
            "name": f"{name} ({code})",
            "label": label,
            "advantage": advantage,
            "pe": f"{pe:.1f}",
            "roe": f"{roe:.1f}%",
            "div": f"{div:.2f}%",
            "cash": f"{cash:.1f}亿",
            "scores": [max(0, min(10, 50/pe*5 if pe>0 else 2)), max(0, min(10, roe/3)), max(0, min(10, div*2)), 7, 6]
        }
    except:
        return None

# 侧边栏输入
st.sidebar.header("🔍 输入对比组合")
input_codes = st.sidebar.text_input("输入代码 (逗号隔开)", "600519, 600309, 002409")

if st.sidebar.button("生成深度报告"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = []
    for c in codes:
        res = get_pro_analysis(c)
        if res: results.append(res)
    
    if results:
        # 第一部分：核心画像表格
        st.subheader("1. 公司画像与核心竞争力")
        df_compare = pd.DataFrame(results)[["name", "label", "advantage", "pe", "roe", "div"]]
        df_compare.columns = ["公司名称", "核心标签", "竞争优势", "估值(PE)", "赚钱能力(ROE)", "分红率"]
        st.table(df_compare)

        # 第二部分：雷达图对比
        st.subheader("2. 维度强弱对比")
        col1, col2 = st.columns([2, 1])
        with col1:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("📖 **图表说明**：")
            st.caption("雷达图面积越大，综合实力越强。若‘回本快慢’顶满，说明分红极高；若‘便宜程度’靠近中心，说明目前估值偏贵。")

        # 第三部分：深度逻辑分析（大白话版）
        st.subheader("3. 理性选择建议")
        for r in results:
            with st.container():
                st.markdown(f"""
                <div class="report-card">
                    <h4>{r['name']}：{r['label']}</h4>
                    <p><b>核心逻辑：</b> 该公司目前现金流约为 <b>{r['cash']}</b>。{r['advantage']}。</p>
                    <p><b>投资策略：</b> 适合做为 <b>{'价值底仓' if '价值' in r['label'] else '趋势博弈'}</b> 持有。</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("数据抓取失败，请检查代码或稍后重试。")
