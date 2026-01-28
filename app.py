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
            # --- 在代码中替换对应的 Prompt 部分 ---

            prompt = f"""
            你现在是极简主义投资专家。请根据以下数据，严格参照《分析框架》输出极简研报。
            禁止使用长段落，禁止废话，多用表格、Emoji和短句。

            ### 框架要求：
            1. **公司画像**：使用Markdown表格 [公司|核心标签|一句话护城河]。
            2. **多维对撞**：对比各家公司，每家只列出 [✅逻辑重点] 和 [❌核心风险]，字数控制在30字内。
            3. **理性定论**：根据数据，直接给出三类人的选择：
               - 稳健派：[选谁+理由]
               - 进攻派：[选谁+理由]
               - 避坑指南：[谁不能碰+理由]

            待分析数据：{str(raw_results)}
            """

# --- 下方渲染部分也做了精简优化 ---
            try:
                response = model.generate_content(prompt)
                
                # 顶部雷达图：直接看体质
                st.subheader("📊 竞争力多维对撞")
                # ...（保持雷达图代码不变）...
                
                # 下方 AI 研报：使用简洁容器
                st.markdown("---")
                st.markdown("### 🤖 Gemini 极简决策报告")
                # 这里的样式让 AI 输出的内容更像卡片
                st.info(response.text) 
                
            except Exception as e:
                st.error(f"AI 生成失败: {e}")
    else:
        st.error("数据调取失败。")
