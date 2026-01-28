import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import re

# --- 1. 核心安全配置：动态模型匹配 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # 动态获取可用模型列表，避免 404
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 按照优先级排序寻找可用模型
    target_models = [
        'models/gemini-1.5-flash', 
        'models/gemini-1.5-pro', 
        'models/gemini-1.0-pro'
    ]
    
    selected_model = None
    for target in target_models:
        if target in available_models:
            selected_model = target
            break
            
    if not selected_model:
        selected_model = available_models[0] # 保底选择第一个可用的
        
    model = genai.GenerativeModel(model_name=selected_model)
    st.sidebar.success(f"已连接 AI 大脑: {selected_model}")

except Exception as e:
    st.error(f"❌ AI 配置异常: {str(e)}")
    st.info("请检查 API Key 是否正确，或网络是否可以访问 Google API。")
    st.stop()

# --- 2. 页面美化配置 ---
st.set_page_config(page_title="Gemini 实时智能研报", layout="wide", page_icon="🍎")

st.markdown("""
    <style>
    .main { background-color: #f9fbfd; }
    .ai-card { background-color: #ffffff; padding: 30px; border-radius: 15px; border-left: 10px solid #4285f4; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .metric-pill { background: #e8f0fe; color: #1967d2; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-right: 8px; }
    .section-head { color: #1a73e8; font-size: 24px; font-weight: bold; margin: 20px 0; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 实时数据抓取函数 ---
def get_clean_name(info, symbol):
    raw = info.get('longName', info.get('shortName', symbol))
    clean = re.sub(r"(?i)(Co\.,\s*Ltd\.|Group|Inc\.|Corp\.|Holdings|A-Shares|Class A)", "", raw)
    cn = "".join(re.findall(r'[\u4e00-\u9fa5]+', clean))
    return cn if cn else clean.strip()

def fetch_stock_data(code):
    symbol = code.strip()
    # 自动处理 A 股后缀
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else:
        symbol_yf = symbol
    
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        # 提取给 AI 的“财报指纹”
        metrics = {
            "name": get_clean_name(info, symbol),
            "code": symbol,
            "pe": info.get('trailingPE', 0),
            "roe": info.get('returnOnEquity', 0) * 100,
            "margin": info.get('grossMargins', 0) * 100,
            "growth": info.get('revenueGrowth', 0) * 100,
            "div_yield": info.get('dividendYield', 0) * 100,
            "debt_ratio": info.get('debtToEquity', 0)
        }
        return metrics
    except:
        return None

# --- 4. 界面布局 ---
st.title("🍎 Gemini 实时智能投资大脑")
st.caption("基于 2026 年最新市场数据及 Gemini 1.5 原生逻辑内核")

with st.sidebar:
    st.header("🔍 监控台")
    codes_input = st.text_input("输入对比代码 (逗号分隔)", "600519, 002028, 300750")
    depth_level = st.radio("AI 分析深度", ["标准逻辑", "深度博弈", "风险扫雷"])
    go_analyze = st.button("🚀 启动 AI 实时研判")

if go_analyze:
    codes = [c.strip() for c in codes_input.split(',')]
    
    with st.status("正在建立逻辑连接...", expanded=True) as status:
        st.write("正在抓取全球实时财务数据...")
        results = [fetch_stock_data(c) for c in codes if fetch_stock_data(c)]
        
        if results:
            st.write("正在将数据指纹喂给 Gemini 神经网络...")
            
            # 构建对话 Prompt
            prompt = f"""
            你现在是一名极度理性的顶级投资专家，这是你刚刚收到的实时财务指纹。
            请根据数据，直接给出你的深度分析。
            
            要求：
            1. 分析维度：请根据这些指标（ROE、PE、营收增速、毛利、负债）判断这些标的的‘护城河’是否稳固。
            2. 对话感：不要列清单，直接像在跟我聊天一样点评。指出谁是真正的‘现金奶牛’，谁正在‘带病狂奔’。
            3. 深度级别：{depth_level}。
            4. 最终断言：在这个组合中，从‘赔率和确定性’平衡来看，你最看好哪一个？
            
            实时数据：{str(results)}
            """
            
            try:
                # 调取 Gemini 核心
                response = model.generate_content(prompt)
                status.update(label="✅ 分析完成！", state="complete", expanded=False)
                
                # --- 5. 渲染 AI 研报 ---
                st.markdown('<div class="section-head">💡 Gemini 实时深度点评</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-card">{response.text}</div>', unsafe_allow_html=True)
                
                # --- 6. 数据可视化 (雷达图) ---
                st.markdown('<div class="section-head">📊 体质多维对比</div>', unsafe_allow_html=True)
                categories = ['估值性价比', '盈利能力', '毛利溢价', '增长动力', '稳健程度']
                fig = go.Figure()
                for r in results:
                    # 动态算分
                    scores = [
                        max(1, min(10, 50/r['pe']*5 if r['pe']>0 else 2)),
                        max(1, min(10, r['roe']/3)),
                        max(1, min(10, r['margin']/5)),
                        max(1, min(10, r['growth']/5)),
                        max(1, min(10, 10 - r['debt_ratio']/20))
                    ]
                    fig.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=r['name']))
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=500)
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Gemini API 响应异常: {str(e)}")
        else:
            st.error("抓取失败，请检查网络或代码输入。")

# --- 7. 页脚原始数据 ---
with st.expander("查看底层原始财务指纹"):
    if 'results' in locals() and results:
        st.table(pd.DataFrame(results))
