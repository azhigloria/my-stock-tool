import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import re

# 1. 页面配置
st.set_page_config(page_title="Gemini 选股笔记：深度分析模式", layout="wide")

# 2. 注入“深度对话”感样式
st.markdown("""
    <style>
    .ai-chat-box { background-color: #f4f7f9; padding: 25px; border-radius: 15px; border-left: 6px solid #1a73e8; margin-bottom: 30px; }
    .logic-header { color: #1a73e8; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    .analysis-text { line-height: 1.8; font-size: 16px; color: #3c4043; }
    .stat-pill { background: #e8f0fe; color: #1967d2; padding: 4px 12px; border-radius: 20px; font-size: 13px; margin-right: 10px; font-weight: bold; }
    .recommend-card { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); height: 100%; border-top: 5px solid #34a853; }
    </style>
    """, unsafe_allow_html=True)

def get_clean_name(info, symbol):
    raw = info.get('longName', info.get('shortName', symbol))
    clean = re.sub(r"(?i)(Co\.,\s*Ltd\.|Group|Inc\.|Corp\.|Holdings|A-Shares|Class A)", "", raw)
    cn = "".join(re.findall(r'[\u4e00-\u9fa5]+', clean))
    return cn if cn else clean.strip()

def get_pro_data(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else: symbol_yf = symbol
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        margin = info.get('grossMargins', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)
        
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)),
            max(1, min(10, roe/3)),
            max(1, min(10, (info.get('dividendYield', 0)*100)*200 if info.get('dividendYield') else 1)),
            max(1, min(10, 10 - debt/25)),
            max(1, min(10, growth*8))
        ]
        return {
            "name": get_clean_name(info, symbol), "code": symbol, "pe": pe, "roe": roe,
            "margin": margin, "growth": growth, "debt": debt, "scores": scores
        }
    except: return None

# --- 对话式 AI 深度分析引擎 ---
def ai_conversational_analysis(r):
    # 核心观点：模拟 Gemini 的理性点评
    if r['roe'] > 20 and r['margin'] > 30:
        conclusion = f"这家公司的生意模式非常硬。{r['margin']:.1f}% 的毛利和 {r['roe']:.1f}% 的 ROE 意味着它在产业链中有绝对的话语权，属于典型的‘躺赚’型企业。"
    elif r['roe'] > 12:
        conclusion = f"盈利能力属于‘优等生’范畴，经营效率不错。但考虑到目前营收增速为 {r['growth']:.1f}%，它更偏向于‘稳健收息’而非‘爆发增长’。"
    else:
        conclusion = "财务指标显示其正面临一定的压力。盈利能力跌破 10%，意味着它可能正在经历行业阵痛期，或者护城河正在变窄，需要谨慎。"

    # 风险直击
    risk_text = "估值（PE）高达 {:.1f}，现在的价格已经透支了未来的预期，短期赔率不高。".format(r['pe']) if r['pe'] > 35 else "目前的估值水平处于合理区间，向下空间有限，安全边际比较厚。"
    
    return conclusion, risk_text

# 3. 界面展示
st.title("🤖 Gemini 深度投资决策助手")
st.markdown("---")

user_input = st.sidebar.text_input("输入自选代码 (如: 600519, 002028)", "600519, 002028")

if st.sidebar.button("启动深度对话分析"):
    codes = [c.strip() for c in user_input.split(',')]
    results = [get_pro_data(c) for c in codes if get_pro_data(c)]
    
    if results:
        # 第一模块：核心观点直达 (取代原本的表格/画像)
        st.subheader("💡 AI 深度点评")
        for r in results:
            conclusion, risk = ai_conversational_analysis(r)
            st.markdown(f"""
            <div class="ai-chat-box">
                <div class="logic-header">关于 {r['name']} ({r['code']}) 的分析结论：</div>
                <div class="analysis-text">
                    <span class="stat-pill">ROE: {r['roe']:.1f}%</span>
                    <span class="stat-pill">PE: {r['pe']:.1f}</span>
                    <span class="stat-pill">毛利: {r['margin']:.1f}%</span>
                    <br/><br/>
                    <b>我的核心观察：</b>{conclusion}<br/><br/>
                    <b>关于风险，我认为：</b>{risk}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 第二模块：多维体质对比
        st.subheader("📊 综合体质雷达图")
        col_chart, col_empty = st.columns([1.5, 1])
        with col_chart:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=500)
            st.plotly_chart(fig, use_container_width=True)
            

        # 第三模块：理性决策矩阵
        st.subheader("⚖️ 最终决策建议")
        c1, c2, c3 = st.columns(3)
        best_v = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
        best_g = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
        best_s = sorted(results, key=lambda x: x['roe'], reverse=True)[0]

        with c1:
            st.markdown(f"""<div class="recommend-card"><b>💎 价值挖掘</b><br/><br/>
            <b>首选：{best_v['name']}</b><br/>
            理由：它是目前组合中最便宜的选择，如果你追求‘低价买好货’，它最合适。</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="recommend-card"><b>🚀 成长进取</b><br/><br/>
            <b>首选：{best_g['name']}</b><br/>
            理由：虽然有波动，但它的扩张速度最快。适合愿意用时间换取爆发空间的投资者。</div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="recommend-card"><b>🛡️ 稳健长线</b><br/><br/>
            <b>首选：{best_s['name']}</b><br/>
            理由：它是这个组合里的‘现金奶牛’。ROE 表现卓越，适合追求确定性的长线底仓。</div>""", unsafe_allow_html=True)
    else:
        st.error("数据调取失败。")
