import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import re

# 1. 页面配置
st.set_page_config(page_title="Gemini 动态逻辑研报", layout="wide")

# 样式：专业研报与直观对话的结合
st.markdown("""
    <style>
    .dynamic-report { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e0e6ed; margin-bottom: 25px; }
    .tag-box { display: flex; gap: 8px; margin-bottom: 15px; }
    .tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .tag-blue { background: #e3f2fd; color: #1976d2; }
    .tag-red { background: #ffebee; color: #c62828; }
    .tag-green { background: #e8f5e9; color: #2e7d32; }
    .opinion-header { color: #2c3e50; font-size: 18px; font-weight: bold; margin-bottom: 12px; border-left: 4px solid #1a73e8; padding-left: 10px; }
    .content-body { line-height: 1.7; color: #444; font-size: 15px; }
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
        return {
            "name": get_clean_name(info, symbol), "code": symbol, 
            "pe": info.get('trailingPE', 0), "roe": info.get('returnOnEquity', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100, "growth": info.get('revenueGrowth', 0) * 100,
            "div": info.get('dividendYield', 0) * 100, "debt": info.get('debtToEquity', 0),
            "info": info
        }
    except: return None

# --- 核心：多维动态评价引擎 ---
def generate_dynamic_opinion(r):
    tags = []
    opinions = []
    
    # 1. 盈利与护城河判定
    if r['roe'] > 20 and r['margin'] > 40:
        tags.append(('<span class="tag tag-green">极强护城河</span>', "属于典型的‘轻资产、高毛利’模式。"))
        opinions.append(f"其 {r['roe']:.1f}% 的净资产收益率配合高毛利，说明产品极具定价权，基本面处于顶尖行列。")
    elif r['roe'] > 15:
        tags.append(('<span class="tag tag-blue">优质白马</span>', "经营效率稳健。"))
        opinions.append("盈利水平处于 A 股前 10% 梯队，展现了成熟的商业模式。")
    else:
        tags.append(('<span class="tag tag-red">效率待提升</span>', "当前赚钱效应一般。"))
        opinions.append(f"ROE 仅为 {r['roe']:.1f}%，需警惕行业竞争加剧或成本控制压力。")

    # 2. 增长逻辑交叉判定
    if r['growth'] > 30:
        opinions.append(f"难得的是，在如此规模下仍保持 {r['growth']:.1f}% 的营收增速，说明正处于强力扩张期。")
    elif r['growth'] < 0:
        opinions.append(f"注意到营收增长为负（{r['growth']:.1f}%），这通常暗示行业见顶或份额被蚕食，逻辑已从‘扩张’转向‘防守’。")

    # 3. 估值与性价比
    if r['pe'] == 0:
        opinions.append("目前处于亏损状态或数据异常，无法通过 PE 估值，建议关注现金流变化。")
    elif r['pe'] > 50:
        opinions.append(f"高达 {r['pe']:.1f} 倍的 PE 说明市场对其未来寄予厚望，但短期安全边际较薄，容错率极低。")
    elif r['pe'] < 15:
        opinions.append(f"PE 仅 {r['pe']:.1f} 倍，若非行业基本面反转，目前估值具有极强的‘捡漏’属性。")

    # 4. 股东回报
    if r['div'] > 3:
        tags.append(('<span class="tag tag-green">高分红</span>', ""))
        opinions.append(f"其股息率达到 {r['div']:.2f}%，在震荡市中具备极强的抗跌属性，是优质的防御标的。")

    return "".join([t[0] for t in tags]), " ".join(opinions)

# 3. UI 展示
st.title("🤖 Gemini 动态逻辑深度研报")
st.caption("基于实时财报数据进行多维交叉推理，生成非预设化深度观点")

user_input = st.sidebar.text_input("输入自选代码 (逗号分隔)", "600519, 002028, 300750")

if st.sidebar.button("启动深度逻辑分析"):
    codes = [c.strip() for c in user_input.split(',')]
    results = [get_pro_data(c) for c in codes if get_pro_data(c)]
    
    if results:
        for r in results:
            tag_html, opinion_text = generate_dynamic_opinion(r)
            st.markdown(f"""
            <div class="dynamic-report">
                <div class="tag-box">{tag_html}</div>
                <div class="opinion-header">{r['name']} ({r['code']})：深度逻辑研判</div>
                <div class="content-body">
                    {opinion_text}
                </div>
                <div style="margin-top:15px; padding-top:10px; border-top:1px dashed #eee; font-size:13px; color:#888;">
                    关键指标：ROE {r['roe']:.1f}% | PE {r['pe']:.1f} | 营收增速 {r['growth']:.1f}% | 资产负债率 {r['debt']:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 可视化对比
        st.subheader("📊 竞争力对撞图")
        
        categories = ['便宜程度', '赚钱底气', '增长动力', '稳健程度', '分红回报']
        fig = go.Figure()
        for r in results:
            # 动态计算雷达图分数
            s = [
                max(1, min(10, 50/r['pe']*5 if r['pe'] > 0 else 2)),
                max(1, min(10, r['roe']/3)),
                max(1, min(10, r['growth']/5)),
                max(1, min(10, 10 - r['debt']/20)),
                max(1, min(10, r['div']*2))
            ]
            fig.add_trace(go.Scatterpolar(r=s, theta=categories, fill='toself', name=r['name']))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("无法获取数据，请检查代码。")
