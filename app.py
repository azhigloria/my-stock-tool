import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面配置
st.set_page_config(page_title="散户深度选股笔记", layout="wide")

# 2. 自定义样式：打造“深度研报”既视感
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
            max(1, min(10, 50/pe*5 if pe>0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), 
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*8))
        ]
        
        # 深度逻辑模块化
        if roe > 15:
            logic = "典型的“白马股”。依靠极强的品牌力或成本护城河实现超额利润。"
            advantage = "经营极其稳健，抗风险能力强，分红相对稳定，是时间的朋友。"
        else:
            logic = "典型的“周期/成长股”。业绩受行业景气度影响大，需关注国产替代或扩产节奏。"
            advantage = "资产质量尚可，管理层执行力强，正处于行业地位爬坡期。"

        risk = "盘子较大，股价受全球宏观经济和外资流动影响显著。" if pe > 25 else "行业竞争加剧可能导致毛利承压，需关注新产能释放进度。"

        return {
            "name": name, "code": pure_code, "pe": pe, "roe": roe, "div": div, "growth": growth,
            "scores": scores, "logic": logic, "advantage": advantage, "risk": risk
        }
    except: return None

st.title("🍎 深度研报对比：让投资回归理性")

# 侧边栏
st.sidebar.header("📝 输入对比组合")
input_codes = st.sidebar.text_input("代码(如: 600309, 600426, 002409)", "600309, 600426, 002409")

if st.sidebar.button("生成深度研报"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = [get_pro_data(c) for c in codes if get_pro_data(c)]
    
    if results:
        # 第一部分：公司画像
        st.markdown('<div class="section-title">1. 公司画像与核心竞争力</div>', unsafe_allow_html=True)
        cols = st.columns(len(results))
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f"**{r['name']} ({r['code']})**")
                st.caption(f"{'全球化工巨头' if '万华' in r['name'] else '行业标杆'}")
                st.write(f"核心优势：{r['advantage'][:15]}...")

        # 第二部分：深度对比分析
        st.markdown('<div class="section-title">2. 深度对比分析</div>', unsafe_allow_html=True)
        col_chart, col_text = st.columns([1, 1.2])
        
        with col_chart:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450, margin=dict(t=30, b=30))
            st.plotly_chart(fig, use_container_width=True)
            
        with col_text:
            for r in results:
                st.markdown(f"**{r['name']}：穿越周期的力量**")
                st.markdown(f"- **逻辑：** {r['logic']}")
                st.markdown(f"- **优点：** {r['advantage']}")
                st.markdown(f"- **风险：** {r['risk']}")
                st.write("")

        # 第三部分：理性选择建议
        st.markdown('<div class="section-title">3. 理性选择建议</div>', unsafe_allow_html=True)
        st.write("根据不同的投资画像，你可以参考以下结论：")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            best_v = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
            st.markdown(f"""<div class="recommend-card"><b>偏好“价值投资”与安全边际：</b><br/><br/>
            优先选择 <span class="highlight-text">{best_v['name']}</span>。目前市盈率仅 {best_v['pe']:.1f}，估值优势明显，适合长期底仓。</div>""", unsafe_allow_html=True)
        with c2:
            best_g = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
            st.markdown(f"""<div class="recommend-card"><b>偏好“极致效率”与中短期爆发：</b><br/><br/>
            优先选择 <span class="highlight-text">{best_g['name']}</span>。ROE 高达 {best_g['roe']:.1f}%，是典型的盈利机器，进攻性强。</div>""", unsafe_allow_html=True)
        with c3:
            best_d = sorted(results, key=lambda x: x['scores'][2], reverse=True)[0]
            st.markdown(f"""<div class="recommend-card"><b>偏好“国产替代”与高成长性：</b><br/><br/>
            优先选择 <span class="highlight-text">{best_d['name']}</span>。结合行业景气度，适合能承受高波动、看好产业爆发的投资者。</div>""", unsafe_allow_html=True)
    else:
        st.error("数据调取失败，请检查代码或网络。")
