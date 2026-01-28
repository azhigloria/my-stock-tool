import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面配置
st.set_page_config(page_title="散户深度选股笔记", layout="wide")

# 2. 注入样式
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #4CAF50; margin-bottom: 20px; text-align: center; height: 120px; }
    .section-title { color: #2c3e50; font-size: 24px; font-weight: bold; margin: 25px 0 15px 0; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .recommend-card { background-color: #fcfdfc; padding: 20px; border-radius: 10px; border: 1px solid #eef2ee; min-height: 180px; }
    .highlight-text { color: #ff4b4b; font-weight: bold; font-size: 18px; }
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

        # 评分模型
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), 
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*8))
        ]
        
        # 逻辑判定
        if roe > 15:
            logic, adv = "典型的‘白马股’，靠核心竞争力赚取超额利润。", "经营稳健，是长线‘时间的朋友’。"
        else:
            logic, adv = "典型的‘周期/成长股’，受行业景气度驱动。", "资产质量尚可，正处于地位爬坡期。"
        
        risk = "估值较高，需警惕回调。" if pe > 30 else "需关注新产能释放节奏。"

        return {
            "name": name, "code": pure_code, "pe": pe, "roe": roe, "div": div, 
            "growth": growth, "scores": scores, "logic": logic, "adv": adv, "risk": risk
        }
    except:
        return None

st.title("🍎 深度研报对比：让投资回归理性")

# 3. 侧边栏
st.sidebar.header("📝 输入对比组合")
user_input = st.sidebar.text_input("代码(用逗号隔开)", "600309, 600426, 002409")

if st.sidebar.button("生成深度研报"):
    codes_list = [c.strip() for c in user_input.split(',')]
    results = [get_pro_data(c) for c in codes_list]
    results = [r for r in results if r is not None]
    
    if results:
        # --- 模块 1: 公司画像 ---
        st.markdown('<div class="section-title">1. 公司画像与核心竞争力</div>', unsafe_allow_html=True)
        cols = st.columns(len(results))
        for i, r in enumerate(results):
            with cols[i]:
                # 使用三引号避免单引号闭合错误
                st.markdown(f"""
                <div class="report-card">
                    <b>{r['name']} ({r['code']})</b><br/>
                    <small style="color:#666;">{r['adv']}</small>
                </div>
                """, unsafe_allow_html=True)

        # --- 模块 2: 深度分析 ---
        st.markdown('<div class="section-title">2. 深度对比分析</div>', unsafe_allow_html=True)
        col_chart, col_text = st.columns([1, 1.2])
        
        with col_chart:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_text:
            for r in results:
                st.markdown(f"#### {r['name']} 深度解读")
                st.write(f"**核心逻辑：** {r['logic']}")
                st.write(f"**核心优点：** {r['adv']}")
                st.write(f"**潜在风险：** {r['risk']}")
                st.write("---")

        # --- 模块 3: 理性建议 ---
        st.markdown('<div class="section-title">3. 理性选择建议</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            best_v = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
            st.markdown(f"""
            <div class="recommend-card">
                <b>偏好“价值投资”与安全边际：</b><br/><br/>
                优先选择：<span class="highlight-text">{best_v['name']}</span><br/>
                理由：PE仅 {best_v['pe']:.1f}，在当前组合中价格最便宜，安全垫最厚。
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            best_g = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
            st.markdown(f"""
            <div class="recommend-card">
                <b>偏好“高弹性”与成长爆发：</b><br/><br/>
                优先选择：<span class="highlight-text">{best_g['name']}</span><br/>
                理由：营收增速达 {best_g['growth']:.1f}%，处于快速扩张期，股价弹性最大。
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            best_s = sorted(results, key=lambda x: x['roe'], reverse=True)[0]
            st.markdown(f"""
            <div class="recommend-card">
                <b>偏好“卓越经营”与长线配置：</b><br/><br/>
                优先选择：<span class="highlight-text">{best_s['name']}</span><br/>
                理由：ROE 达 {best_s['roe']:.1f}%，赚钱效率最高，是典型的优质白马。
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("数据调取失败。可能是网络波动，请再次点击按钮试试。")
