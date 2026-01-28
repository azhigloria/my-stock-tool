import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import json
import re

# --- 1. AI 配置与动态模型选择 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # 动态匹配模型
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_path = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_path)
except Exception as e:
    st.error(f"AI 配置失败: {e}")
    st.stop()

# --- 2. 页面样式 ---
st.set_page_config(page_title="Gemini 结构化研报终端", layout="wide")
st.markdown("""
    <style>
    .report-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-top: 4px solid #1a73e8; height: 100%; }
    .ai-insight-box { background: #f8faff; padding: 15px; border-radius: 8px; border-left: 4px solid #34a853; margin-top: 10px; font-size: 14px; }
    .section-title { color: #1a237e; font-size: 22px; font-weight: bold; margin: 30px 0 15px 0; border-bottom: 2px solid #eee; padding-bottom: 8px; }
    .metric-value { font-size: 20px; font-weight: bold; color: #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据抓取 ---
def get_stock_data(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else: symbol_yf = symbol
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        name = info.get('shortName', symbol)
        # 清洗中文名
        cn_name = "".join(re.findall(r'[\u4e00-\u9fa5]+', name))
        return {
            "name": cn_name if cn_name else name,
            "code": symbol,
            "pe": info.get('trailingPE', 0),
            "roe": info.get('returnOnEquity', 0) * 100,
            "growth": info.get('revenueGrowth', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100,
            "debt": info.get('debtToEquity', 0)
        }
    except: return None

# --- 4. 界面逻辑 ---
st.title("🛡️ Gemini 结构化决策终端")
st.caption("实时抓取数据 + AI 逻辑建模 + 结构化框架呈现")

user_input = st.sidebar.text_input("代码(逗号分隔)", "600519, 002028")

if st.sidebar.button("启动深度分析"):
    codes = [c.strip() for c in user_input.split(',')]
    raw_results = [get_stock_data(c) for c in codes if get_stock_data(c)]

    if raw_results:
        # --- 核心：请求 AI 生成结构化 JSON 结论 ---
        with st.spinner("Gemini 正在逻辑建模..."):
            prompt = f"""
            作为资深分析师，请根据以下数据，为每家公司提供3个核心结论：1.护城河评价，2.增长风险点，3.投资博弈建议。
            要求：必须以严格的 JSON 格式输出，不要有任何多余解释。格式如下：
            {{"代码": {{"insight": "一句话护城河", "risk": "一句话风险", "advice": "一句话建议"}}}}
            数据：{str(raw_results)}
            """
            try:
                response = model.generate_content(prompt)
                # 提取 JSON 字符串
                json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
                ai_insights = json.loads(json_str)
            except:
                ai_insights = {}

        # --- 第一部分：公司画像卡片 ---
        st.markdown('<div class="section-title">一、公司基本面画像</div>', unsafe_allow_html=True)
        cols = st.columns(len(raw_results))
        for i, r in enumerate(raw_results):
            with cols[i]:
                st.markdown(f"""
                <div class="report-card">
                    <h3>{r['name']} <small>{r['code']}</small></h3>
                    <p>ROE: <span class="metric-value">{r['roe']:.1f}%</span></p>
                    <p>动态PE: <span class="metric-value">{r['pe']:.1f}</span></p>
                    <div class="ai-insight-box">
                        <b>AI 核心洞察：</b><br/>{ai_insights.get(r['code'], {}).get('insight', '分析加载中...')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # --- 第二部分：多维对比 ---
        st.markdown('<div class="section-title">二、多维度逻辑对比</div>', unsafe_allow_html=True)
        col_chart, col_table = st.columns([1, 1.2])
        
        with col_chart:
            categories = ['便宜度', '赚钱底气', '增长动力', '稳健性', '毛利水平']
            fig = go.Figure()
            for r in raw_results:
                scores = [
                    max(1, min(10, 50/r['pe']*5 if r['pe']>0 else 2)),
                    max(1, min(10, r['roe']/3)),
                    max(1, min(10, r['growth']/5)),
                    max(1, min(10, 10 - r['debt']/20)),
                    max(1, min(10, r['margin']/5))
                ]
                fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            

        with col_table:
            # 这里的表格结合了原始数据和 AI 风险提示
            table_data = []
            for r in raw_results:
                table_data.append({
                    "名称": r['name'],
                    "营收增速": f"{r['growth']:.1f}%",
                    "风险预警 (AI)": ai_insights.get(r['code'], {}).get('risk', '需关注基本面波动')
                })
            st.table(pd.DataFrame(table_data))

        # --- 第三部分：最终博弈决策 ---
        st.markdown('<div class="section-title">三、理性博弈决策建议</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, r in enumerate(raw_results):
            target_col = c1 if i % 2 == 0 else c2
            with target_col:
                st.info(f"**{r['name']} 投资建议：** {ai_insights.get(r['code'], {}).get('advice', '观望为主')}")

    else:
        st.error("未获取到数据，请检查输入。")
