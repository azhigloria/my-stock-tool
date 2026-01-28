import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import re

# 1. 页面配置
st.set_page_config(page_title="A股深度理财笔记", layout="wide")

# 2. 样式：增强“研报笔记”质感
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #4CAF50; margin-bottom: 20px; }
    .section-title { color: #1b5e20; font-size: 26px; font-weight: bold; margin: 30px 0 15px 0; border-left: 5px solid #4CAF50; padding-left: 15px; }
    .recommend-card { background-color: #f1f8e9; padding: 20px; border-radius: 10px; border: 1px solid #c8e6c9; height: 100%; }
    .highlight-text { color: #d32f2f; font-weight: bold; font-size: 1.2em; }
    </style>
    """, unsafe_allow_html=True)

def get_clean_cn_name(info, symbol):
    """
    智能清洗函数：从抓取到的原始名称中提取纯中文
    """
    # 尝试获取长名称或短名称
    raw_name = info.get('longName', info.get('shortName', symbol))
    
    # 1. 处理常见的英文后缀和拼音杂质
    clean_name = re.sub(r"(?i)(Co\.,\s*Ltd\.|Group|Incorporated|Inc\.|Corp\.|Holdings|A-Shares|Class A)", "", raw_name)
    
    # 2. 如果包含中文字符，则提取中文字符
    chinese_part = "".join(re.findall(r'[\u4e00-\u9fa5]+', clean_name))
    
    # 3. 如果提取到了中文（如“贵州茅台”），直接返回；否则返回清洗后的拼音
    return chinese_part if chinese_part else clean_name.strip()

def get_pro_analysis(code):
    symbol = code.strip()
    pure_code = "".join(filter(str.isdigit, symbol))
    # 自动识别 A 股市场后缀
    if symbol.isdigit():
        symbol_yf = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else:
        symbol_yf = symbol

    try:
        stock = yf.Ticker(symbol_yf)
        info = stock.info
        
        # 使用智能清洗函数获取中文名
        name = get_clean_cn_name(info, symbol)
        
        # 核心指标
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0) * 100
        div = info.get('dividendYield', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt = info.get('debtToEquity', 0)

        # 评分模型 (1-10分)
        scores = [
            max(1, min(10, 50/pe*5 if pe > 0 else 2)), 
            max(1, min(10, roe/3)), 
            max(1, min(10, div*200)), 
            max(1, min(10, 10 - debt/20)), 
            max(1, min(10, growth*8))
        ]
        
        return {
            "name": name, "code": pure_code, "pe": pe, "roe": roe, "div": div, 
            "growth": growth, "scores": scores, "debt": debt
        }
    except:
        return None

st.title("🍎 深度选股研报：直击企业核心价值")

# 3. 交互输入
st.sidebar.header("✍️ 输入股票代码")
user_input = st.sidebar.text_input("代码(如: 002028, 600309, 300750)", "002028, 600309, 300750")

if st.sidebar.button("开始深度分析"):
    codes_list = [c.strip() for c in user_input.split(',')]
    results = [get_pro_analysis(c) for c in codes_list if get_pro_analysis(c)]
    
    if results:
        # --- 模块一：公司画像 ---
        st.markdown('<div class="section-title">一、公司基本面画像</div>', unsafe_allow_html=True)
        cols = st.columns(len(results))
        for i, r in enumerate(results):
            with cols[i]:
                st.markdown(f"""
                <div class="report-card">
                    <h3 style="color:#2e7d32; margin-bottom:5px;">{r['name']}</h3>
                    <p style="color:#666;">代码：{r['code']}</p>
                    <hr/>
                    <p><b>盈利能力:</b> {r['roe']:.1f}% (ROE)</p>
                    <p><b>当前估值:</b> {r['pe']:.1f} (PE)</p>
                </div>
                """, unsafe_allow_html=True)

        # --- 模块二：多维度对比 ---
        st.markdown('<div class="section-title">二、多维度深度对比</div>', unsafe_allow_html=True)
        col_chart, col_text = st.columns([1.2, 1])
        
        with col_chart:
            # 雷达图展示
            categories = ['便宜程度', '赚钱底气', '回本快慢', '抗跌能力', '增长潜力']
            fig = go.Figure()
            for r in results:
                fig.add_trace(go.Scatterpolar(r=r['scores'], theta=categories, fill='toself', name=r['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 10])), height=450)
            st.plotly_chart(fig, use_container_width=True)
            

        with col_text:
            for r in results:
                st.write(f"#### 🔍 {r['name']} 深度评述")
                # 纯逻辑判断生成的“人话”分析
                if r['roe'] > 15:
                    st.success(f"**核心优势：** 典型的优质白马。{r['roe']:.1f}% 的ROE意味着公司拥有极强的行业议价能力。")
                else:
                    st.info(f"**核心特征：** 属于效率驱动型企业。当前盈利能力尚可，需关注其行业天花板。")
                
                if r['debt'] > 60:
                    st.warning("⚠️ **风险提示：** 财务杠杆较高，需警惕资金链及利息成本对利润的侵蚀。")
                else:
                    st.write("✅ **风险提示：** 财务稳健，负债率控制良好，抗风险能力较强。")
                st.write("---")

        # --- 模块三：理性投资建议 ---
        st.markdown('<div class="section-title">三、理性投资建议（匹配画像）</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        # 排序寻找最符合特征的股票
        best_value = sorted(results, key=lambda x: x['scores'][0], reverse=True)[0]
        best_growth = sorted(results, key=lambda x: x['scores'][4], reverse=True)[0]
        best_roe = sorted(results, key=lambda x: x['roe'], reverse=True)[0]

        with c1:
            st.markdown(f"""<div class="recommend-card"><b>💰 价值派选择：</b><br/><br/>
            建议关注：<span class="highlight-text">{best_value['name']}</span><br/>
            理由：PE 仅为 {best_value['pe']:.1f}，在当前组合中估值最亲民，具有较厚的价格保护垫。</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="recommend-card"><b>🚀 成长派选择：</b><br/><br/>
            建议关注：<span class="highlight-text">{best_growth['name']}</span><br/>
            理由：增长潜力得分最高。适合追求股价弹性的进取型选手，但需注意波动风险。</div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="recommend-card"><b>🛡️ 稳健派选择：</b><br/><br/>
            建议关注：<span class="highlight-text">{best_roe['name']}</span><br/>
            理由：ROE 高达 {best_roe['roe']:.1f}%，是典型的“现金奶牛”，抗周期能力最强。</div>""", unsafe_allow_html=True)
    else:
        st.error("未获取到数据，请确保输入的是正确的 6 位数字代码（如 002028）。")
