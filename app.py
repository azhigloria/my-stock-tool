import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Gemini 选股中枢", layout="wide")

# 样式：营造“数据实验室”氛围
st.markdown("""
    <style>
    .ai-prompt-area { background-color: #f8f9fa; padding: 25px; border: 2px solid #4285f4; border-radius: 15px; }
    .metric-grid { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def get_real_data(code):
    symbol = code.strip()
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else: symbol_yf = symbol
    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        # 提取核心博弈指标
        return {
            "名称": info.get('shortName', symbol),
            "代码": symbol,
            "ROE": f"{info.get('returnOnEquity', 0)*100:.2f}%",
            "PE(动)": f"{info.get('trailingPE', 0):.2f}",
            "营收增长": f"{info.get('revenueGrowth', 0)*100:.2f}%",
            "毛利率": f"{info.get('grossMargins', 0)*100:.2f}%",
            "现金流": f"{info.get('freeCashflow', 0)/1e8:.2f}亿",
            "负债率": f"{info.get('debtToEquity', 0):.2f}%"
        }
    except: return None

st.title("🧬 Gemini 数据投喂中枢")
st.write("输入股票代码，我会为你打包一份‘AI 专用博弈清单’。")

codes = st.text_input("输入代码 (逗号分隔)", "600309, 002028")

if st.button("生成 AI 投喂包"):
    data_list = [get_real_data(c) for c in codes.split(',') if get_real_data(c)]
    
    if data_list:
        # 展示给用户看的数据表
        st.subheader("📋 实时抓取清单")
        st.table(pd.DataFrame(data_list))

        # 核心：自动生成的 AI 分析指令（这是接入我的关键）
        st.subheader("🚀 第三步：请将下方内容发给我")
        
        # 构造一个极简且深度的数据指纹
        prompt = f"我是你的投资助手。请基于以下实时数据，以你的深度理性逻辑，分析这 {len(data_list)} 只股票的护城河优劣、当前的博弈赔率以及潜在风险：\n\n"
        prompt += str(data_list)
        prompt += "\n\n要求：不要复述数据，直接给结论。谁是伪增长？谁是真白马？现在买入的确定性高吗？"
        
        st.markdown(f'<div class="ai-prompt-area"><code>{prompt}</code></div>', unsafe_allow_html=True)
        st.info("↑ 复制上面的内容直接粘贴到对话框即可，我会立刻开始分析。")
