import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import re

# --- 1. 核心 AI 配置 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_path = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_path)
except Exception as e:
    st.error(f"AI 配置失败: {e}")
    st.stop()

# --- 2. 页面样式 ---
st.set_page_config(page_title="Gemini 结构化选股终端", layout="wide")
st.markdown("""
    <style>
    .report-container { background: white; padding: 25px; border-radius: 15px; border: 1px solid #e1e4e8; }
    .stMarkdown h3 { border-left: 5px solid #1a73e8; padding-left: 10px; margin-top: 25px; color: #1a237e; }
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
st.title("🛡️ Gemini 深度投资决策终端")
st.caption("已同步《三大化工股对比分析》文档分析框架")

with st.sidebar:
    user_input = st.text_input("代码(逗号分隔)", "600519, 002028")
    analyze_btn = st.button("🚀 启动结构化研报")

if analyze_btn:
    codes = [c.strip() for c in user_input.split(',')]
    raw_results = [get_stock_data(c) for c in codes if get_stock_data(c)]

    if raw_results:
        with st.spinner("Gemini 正在按指定模板建模..."):
            # 这里的 Prompt 严格参考了文档  的结构
            prompt = f"""
            你现在是一名顶级的理性投资专家。请参考以下财务数据，严格按照《分析框架》输出内容。
            
            ### 分析框架：
            1. 公司画像与核心竞争力：使用Markdown表格，包含[公司名称, 核心标签, 竞争优势]。
            2. 深度对比分析：针对每家公司，给出[逻辑, 优点, 风险]的要点分析。
            3. 理性选择建议：根据不同的投资画像（如价值投资、科技成长等），给出最终推荐。
            
            要求：文案要犀利、理性，不要复述数字，要讲深层博弈逻辑。
            
            待分析数据：{str(raw_results)}
            """
            
            try:
                response = model.generate_content(prompt)
                
                # --- 展示雷达图对比（保留上一版的直观视觉） ---
                st.subheader("📊 竞争力多维对撞")
                categories = ['性价比', '盈利能力', '毛利溢价', '增长动力', '稳健性']
                fig = go.Figure()
                for r in raw_results:
                    scores = [
                        max(1, min(10, 50/r['pe']*5 if r['pe']>0 else 2)),
                        max(1, min(10, r['roe']/3)),
                        max(1, min(10, r['margin']/5)),
                        max(1, min(10, r['growth']/5)),
                        max(1, min(10, 10 - r['debt']/20))
                    ]
                    fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=r['name']))
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
                st.plotly_chart(fig, use_container_width=True)

                # --- 展示 AI 结构化内容 ---
                st.markdown("---")
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.markdown(response.text) # 这里会输出符合文档  模块的内容
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"AI 生成失败: {e}")
    else:
        st.error("数据调取失败。")
