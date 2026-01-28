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
    st.error(f"AI 配置失败，请检查 Secrets: {e}")
    st.stop()

# --- 2. 页面样式 ---
st.set_page_config(page_title="Gemini 极简投资助手", layout="wide")
st.markdown("""
    <style>
    .report-container { background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eee; }
    .stMarkdown h3 { color: #1a73e8; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 极简数据抓取 ---
def get_stock_data(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else: symbol_yf = symbol
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        # 抓取原始名，即使是英文也没关系，后面交给 AI 处理
        return {
            "name": info.get('shortName') or info.get('longName') or symbol,
            "code": symbol,
            "pe": info.get('trailingPE', 0),
            "roe": info.get('returnOnEquity', 0) * 100,
            "growth": info.get('revenueGrowth', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100,
            "debt": info.get('debtToEquity', 0)
        }
    except: return None

# --- 4. 主界面 ---
st.title("🍎 Gemini 极简结构化研报")
st.caption("实时财报数据 + Gemini 逻辑内核 | 遵循《三大化工股对比分析》框架")

with st.sidebar:
    st.header("🔍 配置")
    user_input = st.text_input("代码(逗号分隔)", "600519, 002028")
    analyze_btn = st.button("🚀 启动研判")

if analyze_btn:
    codes = [c.strip() for c in user_input.split(',')]
    raw_results = [get_stock_data(c) for c in codes if get_stock_data(c)]

    if raw_results:
        with st.spinner("AI 正在解析数据并汉化名称..."):
            # 核心 Prompt：强制要求中文名、极简表格、短句结论
            prompt = f"""
            你现在是极简主义选股专家。请根据以下数据，参考《分析框架》输出报告。
            
            ⚠️ 重要要求：
            1. 名称汉化：必须根据代码将公司名转换为准确的【中文简称】（如：贵州茅台）。
            2. 字数控制：严禁长段落。多用表格和 Emoji。
            
            ### 报告框架：
            一、公司画像：使用Markdown表格 [公司中文名 | 核心标签 | 一句话护城河]。
            二、多维对撞：对比各家，列出 [✅机会点] 和 [❌风险点]（每项限20字）。
            三、理性结论：直接给出针对【稳健派】和【进攻派】的唯一首选，并给出理由。
            
            待分析数据：{str(raw_results)}
            """
            
            try:
                response = model.generate_content(prompt)
                
                # --- 视觉对比图 ---
                st.subheader("📊 竞争力多维对撞")
                categories = ['性价比', '盈利能力', '溢价力', '增长动力', '稳健性']
                fig = go.Figure()
                for r in raw_results:
                    scores = [
                        max(1, min(10, 50/r['pe']*5 if r['pe']>0 else 2)),
                        max(1, min(10, r['roe']/3)),
                        max(1, min(10, r['margin']/5)),
                        max(1, min(10, r['growth']/5)),
                        max(1, min(10, 10 - r['debt']/20))
                    ]
                    fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=r['code']))
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=400)
                st.plotly_chart(fig, use_container_width=True)

                # --- AI 结构化报告 ---
                st.markdown("---")
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.markdown(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"AI 生成失败: {e}")
    else:
        st.error("无法抓取数据，请检查代码。")
