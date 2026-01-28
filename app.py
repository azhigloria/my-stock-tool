import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import re

# --- 1. 核心 AI 配置 ---
try:
    # 确保在 Streamlit Secrets 中配置了 GEMINI_API_KEY
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # 动态匹配模型，确保 404 错误不再发生
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_path = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_path)
except Exception as e:
    st.error(f"AI 配置失败，请检查 Secrets: {e}")
    st.stop()

# --- 2. 页面全局样式 ---
st.set_page_config(page_title="Gemini 自选股大比拼", layout="wide", page_icon="🍎")
st.markdown("""
    <style>
    .report-container { background: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #eef2f6; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    .stMarkdown h3 { color: #1a73e8; border-left: 5px solid #1a73e8; padding-left: 12px; margin-top: 20px; }
    .metric-table { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 极简数据抓取逻辑 ---
def get_stock_data(code):
    symbol = code.strip()
    # 自动识别并添加 A 股后缀
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else:
        symbol_yf = symbol
    
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        # 返回原始数据供 AI 和雷达图使用
        return {
            "name": info.get('shortName') or info.get('longName') or symbol,
            "code": symbol,
            "pe": info.get('trailingPE', 0),
            "roe": info.get('returnOnEquity', 0) * 100,
            "growth": info.get('revenueGrowth', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100,
            "debt": info.get('debtToEquity', 0)
        }
    except:
        return None

# --- 4. 主界面布局 ---
st.title("🍎 自选股大比拼")
st.caption("实时抓取财报数据 · Gemini 逻辑建模 · 理性决策辅助")

with st.sidebar:
    st.header("🔍 擂台配置")
    user_input = st.text_input("请输入股票代码，用英文逗号隔开", "600519, 002028")
    st.info("💡 提示：输入代码后点击下方按钮，Gemini 将为您生成深度对比报告。")
    analyze_btn = st.button("🚀 启动 PK")

if analyze_btn:
    # 处理输入，限制最多 4 支以保证视觉效果
    codes = [c.strip() for c in user_input.split(',')][:4]
    
    with st.spinner("擂台搭建中，正在读取实时数据..."):
        raw_results = [get_stock_data(c) for c in codes if get_stock_data(c)]

    if raw_results:
        # --- A. 视觉对比图模块 ---
        st.subheader("📊 竞争力五边形")
        categories = ['性价比(PE)', '盈利能力(ROE)', '溢价力(毛利)', '增长动力', '财务稳健度']
        
        fig = go.Figure()
        for r in raw_results:
            # 数据归一化处理（1-10分）
            scores = [
                max(1, min(10, 50/r['pe']*5 if r['pe']>0 else 2)),
                max(1, min(10, r['roe']/3)),
                max(1, min(10, r['margin']/5)),
                max(1, min(10, r['growth']/5)),
                max(1, min(10, 10 - r['debt']/20))
            ]
            # 图例名只保留代码数字，防止过长
            legend_name = r['code'].split('.')[0]
            fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=legend_name))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=False, range=[0, 10])),
            height=450,
            margin=dict(t=30, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)
        

        # --- B. AI 结构化报告模块 ---
        with st.spinner("Gemini 正在逻辑建模并撰写研报..."):
            # 强化后的 Prompt，融入了汉化和极简逻辑
            prompt = f"""
            你现在是极简主义选股专家。请根据以下实时财务数据，参考《分析框架》输出一份深度报告。
            
            ⚠️ 核心准则：
            1. 名称汉化：必须根据股票代码，将公司名称转换为标准的【中文简称】（如：将 600519 识别为 贵州茅台）。
            2. 极简表达：严禁长段落。多用表格、Emoji 和短句，确保一目了然。
            3. 深度逻辑：不仅复述数字，要挖掘数字背后的博弈（如：高毛利代表的议价权，或高负债代表的扩张风险）。

            ### 报告框架：
            一、公司画像与核心竞争力：使用 Markdown 表格 [公司名称 | 核心标签 | 核心优势（护城河）]。
            二、深度对比分析：对比各家，列出每家公司的 [✅机会点] 和 [❌风险点]（每条控制在 25 字以内）。
            三、理性选择建议：
               - 稳健派选择：[公司名] + 理由。
               - 进攻派选择：[公司名] + 理由。
            
            待分析数据：{str(raw_results)}
            """
            
            try:
                response = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown("### 🤖 Gemini 深度研判报告")
                st.markdown(f'<div class="report-container">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"AI 生成失败: {e}")
        
        # 附录：原始数据对照
        with st.expander("📝 赛后技术统计（原始财务指标）"):
            st.table(pd.DataFrame(raw_results).rename(columns={
                "name": "原始名", "code": "代码", "pe": "市盈率", 
                "roe": "净资产收益率%", "growth": "营收增长%", 
                "margin": "毛利率%", "debt": "负债率"
            }))
    else:
        st.error("数据抓取失败，请输入正确的股票代码（如：600519）。")

st.info("理性声明：本工具基于 AI 逻辑推演，不构成任何投资建议。市场有风险，入市需谨慎。")
