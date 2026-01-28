import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import re

# 1. 页面配置
st.set_page_config(page_title="AI 逻辑驱动投资终端", layout="wide")

# 2. 注入更具“极客感”的研报样式
st.markdown("""
    <style>
    .ai-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; margin-bottom: 20px; line-height: 1.6; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #4CAF50; text-align: center; }
    .section-title { color: #1a237e; font-size: 24px; font-weight: bold; margin: 30px 0 15px 0; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
    .recommend-card { background-color: #f1f8e9; padding: 20px; border-radius: 10px; border: 1px solid #c8e6c9; height: 100%; }
    .status-tag { background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 智能中文名清洗引擎
def get_clean_name(info, symbol):
    raw = info.get('longName', info.get('shortName', symbol))
    # 移除英文杂质
    clean = re.sub(r"(?i)(Co\.,\s*Ltd\.|Group|Inc\.|Corp\.|Holdings|A-Shares|Class A)", "", raw)
    # 提取中文
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
        
        # 核心财务抓取
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        margin = info.get('grossMargins', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)
        fcf = info.get('freeCashflow', 0) / 1e8 # 亿为单位

        # 归一化评分 (1-10)
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)),
            max(1, min(10, roe/3)),
            max(1, min(10, (info.get('dividendYield', 0)*100)*200 if info.get('dividendYield') else 1)),
            max(1, min(10, 10 - debt/25)),
            max(1, min(10, growth*8))
        ]
        
        return {
            "name": get_clean_name(info, symbol), "code": symbol, "pe": pe, "roe": roe,
            "margin": margin, "growth": growth, "debt": debt, "fcf": fcf, "scores": scores
        }
    except: return None

# --- 本地专家分析引擎 (模拟 AI) ---
def expert_ai_analysis(r):
    insights = []
    # 1. 盈利逻辑分析
    if r['roe'] > 20: insights.append(f"该股 ROE 高达 {r['roe']:.1f}%，展现出极强的垄断性或品牌溢价能力。")
    elif r['roe'] > 10: insights.append(f"盈利能力处于行业中上游，经营效率稳健。")
    else: insights.append(f"当前 ROE 为 {r['roe']:.1f}%，盈利能力需警惕，关注是否处于行业低谷。")
    
    # 2. 财务风险分析
    if r['debt'] > 80: insights.append(f"负债率偏高（{r['debt']:.1f}%），AI 提示关注其利息覆盖倍数及资金链安全。")
    else: insights.append(f"财务杠杆控制优异，自由现金流（{r['fcf']:.1f}亿）说明生意成色较好。")
    
    # 3. 估值决策
    if r['pe'] > 40: insights.append("当前估值倍数较高，市场已透支未来成长预期，不建议盲目追高。")
    elif r['pe'] < 15: insights.append("市盈率极具吸引力，若基本面无恶化，属于典型的‘价值捡漏’区间。")
    
    return " ".join(insights)

# 3. 交互界面
st.title("🛡️ 专家级·理性选股决策终端")
st.caption("基于本地专家推理引擎，实时解析企业核心财报指标")

codes_input = st.sidebar.text_input("输入自选代码 (如: 600519, 002028, 600309)", "600519, 002028, 600309")

if st.sidebar.button("启动深度逻辑分析"):
    codes = [c.strip() for c in codes_input.split(',')]
    results = [get_pro_data(c) for c in codes if get_pro_data(c)]
    
    if results:
        # 第一模块：公司画像
        st.markdown('<div class="section-title">1. 公司画像与竞争力标签</div>', unsafe_allow_html=True)
        cols = st.columns(len(results))
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f"""
                <div class="report-card">
                    <span class="status-tag">实时监控中</span>
                    <h3 style="margin-top:10px;">{r['name']}</h3>
                    <p style="color:#666; font-size:14px;">{r['code']}</p>
                    <div style="font-weight:bold; color:#2e7d32;">毛利: {r['margin']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

        # 第二模块：深度对比分析
        st.markdown('<div class="section-title">2. 深度逻辑剖析（本地专家系统）</div>', unsafe_allow_html=True)
        col_chart, col_text = st.columns([1, 1.2])
        
        with col_chart:
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
            st.plotly_chart(fig, use_container_width=True)
            
            
        with col_text:
            for r in results:
                st.markdown(f"**{r['name']} 实时分析结论：**")
                st.markdown(f"""<div class="ai-box">
                <b>深度透视：</b>{expert_ai_analysis(r)}<br/>
                <b>增长预测：</b>营收预期增长 {r['growth']:.1f}%，需对比行业均值判断其份额变化。
                </div>""", unsafe_allow_html=True)

        # 第三模块：理性配置建议
        st.markdown('<div class="section-title">3. 理性配置决策（基于画像匹配）</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        best_v = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
        best_g = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
        best_s = sorted(results, key=lambda x: x['roe'], reverse=True)[0]

        with c1:
            st.markdown(f"""<div class="recommend-card"><b>💎 价值挖掘型：</b><br/><br/>
            推荐：<b>{best_v['name']}</b><br/>
            理由：PE仅 {best_v['pe']:.1f}，在当前组合中估值最亲民，具备较高的安全边际。</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="recommend-card"><b>🚀 爆发成长型：</b><br/><br/>
            推荐：<b>{best_g['name']}</b><br/>
            理由：营收增速达 {best_g['growth']:.1f}%，虽波动可能较大，但属于典型的进取型标的。</div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="recommend-card"><b>🛡️ 优质白马型：</b><br/><br/>
            推荐：<b>{best_s['name']}</b><br/>
            理由：ROE 高达 {best_s['roe']:.1f}%，生意模式优越，是长线持股的首选。</div>""", unsafe_allow_html=True)
    else:
        st.error("数据调取失败，请检查代码输入是否为 6 位数字代码。")
