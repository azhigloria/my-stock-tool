import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 1. 页面配置：散户更喜欢紧凑但重点突出的布局
st.set_page_config(page_title="散户炒股助手", layout="wide")

# 自定义 CSS：移除沉重的专业感，增加对比鲜明的卡片
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .status-card { background-color: #ffffff; padding: 25px; border-radius: 15px; 
                  box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #ff4b4b; margin-bottom: 25px; }
    .recommend-box { background-color: #e8f4ea; padding: 20px; border-radius: 12px; border-left: 6px solid #2e7d32; }
    h3 { color: #31333f; font-weight: 800; }
    .metric-value { font-size: 24px; font-weight: bold; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 股票pk台：哪只股票更值得买？")

def get_pro_analysis(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. 中文名处理 (如果 yfinance 返回的是英文，这里可以手动映射或显示代码)
        name = info.get('shortName', symbol)
        # 简单处理常见的 A 股显示
        if "Moutai" in name: name = "贵州茅台"
        if "Wanhua" in name: name = "万华化学"
        
        # 抓取数据
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 逻辑画像引擎
        if roe > 18 and div > 3:
            persona = "【养老神器】高分红优等生"
            reason = "赚钱多且愿意分钱，适合追求稳定收入的长线投资者。"
        elif growth > 20:
            persona = "【爆发黑马】高增长潜力股"
            reason = "生意扩张极快，适合能忍受波动、追求股价翻倍的激进投资者。"
        elif pe < 15 and roe > 10:
            persona = "【价值洼地】稳健老牌公司"
            reason = "价格不贵且公司底子好，适合追求安全感、想买便宜货的投资者。"
        else:
            persona = "【周期波动】行业参与者"
            reason = "业务受行业周期影响大，建议在行业低谷时布局。"

        # 评分
        scores = [
            max(0, min(10, 50/pe*5 if pe>0 else 2)), 
            max(0, min(10, roe/3)), 
            max(0, min(10, div*2)), 
            max(0, min(10, 10 - debt/20)), 
            max(0, min(10, growth*10))
        ]
        
        return {
            "name": name,
            "code": code,
            "persona": persona,
            "reason": reason,
            "pe": pe,
            "roe": roe,
            "div": div,
            "scores": scores
        }
    except:
        return None

# 侧边栏
st.sidebar.header("🕹️ 第一步：输入股票")
input_codes = st.sidebar.text_input("代码(用逗号隔开)", "600519, 600309, 002409")

if st.sidebar.button("开始大白话分析"):
    codes = [c.strip() for c in input_codes.split(',')]
    results = []
    with st.spinner('正在分析中...'):
        for c in codes:
            res = get_pro_analysis(c)
            if res: results.append(res)
    
    if results:
        # 第一部分：对比雷达图（放在最上面，先给视觉冲击）
        st.subheader("🟢 强弱一眼便知")
        categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
        fig = go.Figure()
        for r in results:
            fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # 第二部分：个性化建议卡片
        st.subheader("💡 老师傅的建议")
        for r in results:
            st.markdown(f"""
            <div class="status-card">
                <span style="color:#666;">公司名称：</span><span style="font-size:20px; font-weight:bold;">{r['name']} ({r['code']})</span>
                <div style="margin-top:10px;">
                    <span class="recommend-box"><b>适合人群：{r['persona']}</b></span>
                </div>
                <div style="margin-top:15px; color:#444; line-height:1.6;">
                    <b>为什么推荐它：</b>{r['reason']}<br/>
                    <b>核心数据：</b>估值约 {r['pe']:.1f} 倍，每年赚回本金的 {r['roe']:.1f}%，分红率高达 {r['div']:.2f}%。
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # 第三部分：理性选择矩阵
        st.subheader("🏆 最终选哪个？")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("💰 **稳健分红型**")
            st.write("首选：", sorted(results, key=lambda x: x['div'], reverse=True)[0]['name'])
        with col2:
            st.warning("🚀 **激进增长型**")
            st.write("首选：", sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]['name'])
        with col3:
            st.info("🛡️ **安全避险型**")
            st.write("首选：", sorted(results, key=lambda x: x['scores'][3], reverse=True)[0]['name'])
    else:
        st.error("没抓到数据，请检查代码。")
