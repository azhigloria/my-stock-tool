import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 页面配置
st.set_page_config(page_title="散户炒股对比工具", layout="wide")
st.title("📊 散户自选股深度对比 (专业版)")

def get_real_data(code):
    # 处理 A 股后缀逻辑
    symbol = code.strip()
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 提取真实名字和指标
        name = info.get('longName') or info.get('shortName') or symbol
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        debt = info.get('debtToEquity', 0)
        growth = info.get('revenueGrowth', 0) * 100

        # 计算得分 (1-10) 及其依据
        metrics = {
            "便宜程度": (max(0, min(10, 50/pe*5 if pe > 0 else 2)), f"PE为{pe:.2f}"),
            "赚钱底气": (max(0, min(10, roe/3)), f"ROE为{roe:.1f}%"),
            "回本快慢": (max(0, min(10, div*2)), f"股息率为{div:.2f}%"),
            "抗跌能力": (max(0, min(10, 10 - debt/20)), f"负债率为{debt:.1f}%"),
            "增长潜力": (max(0, min(10, growth*10)), f"营收增长{growth:.1f}%")
        }
        
        return {
            "display_name": f"{name} ({code})",
            "scores": [v[0] for v in metrics.values()],
            "details": [v[1] for v in metrics.values()]
        }
    except:
        return None

# 侧边栏
st.sidebar.header("输入股票代码")
input_codes = st.sidebar.text_input("输入代码 (逗号隔开)", "600519, 002028")

if st.sidebar.button("开始深度分析"):
    codes = [c.strip() for c in input_codes.split(',')]
    all_results = []
    
    with st.spinner('正在抓取真实财务数据...'):
        for c in codes:
            res = get_real_data(c)
            if res: all_results.append(res)
    
    if all_results:
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()

        for r in all_results:
            fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['display_name']))

        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🧐 深度分析依据")
        cols = st.columns(len(all_results))
        for i, r in enumerate(all_results):
            with cols[i]:
                st.markdown(f"### {r['display_name']}")
                # 显示具体的评分依据
                for cat, detail in zip(categories, r['details']):
                    st.write(f"- **{cat}**: {detail}")
    else:
        st.error("暂时无法连接数据源，请稍后再试或检查代码格式。")
