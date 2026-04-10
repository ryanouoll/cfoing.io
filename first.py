import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import errors
# python -m streamlit run first.py

# --- 頁面設定 ---
st.set_page_config(page_title="AI CFO Dashboard", layout="wide")
st.title("📊 supreme AI CFO - startup time")

@st.cache_data 
def load_data():
    data = {
        'date': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', '2024-03-01', '2024-03-15'],
        'type': ['income', 'expense', 'income', 'expense', 'income', 'expense'],
        'category': ['Stripe', 'Payroll', 'Stripe', 'Payroll', 'Stripe', 'Payroll'],
        'amount': [15000, 18000, 17000, 18000, 16000, 18000],
        'description': ['SaaS Revenue', 'Engineer Salary', 'SaaS Revenue', 'Engineer Salary', 'SaaS Revenue', 'Engineer Salary']
    }
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()
current_cash = 150000 

# --- 核心計算邏輯 ---
expenses = df[df['type'] == 'expense']['amount'].sum()
income = df[df['type'] == 'income']['amount'].sum()
total_months = df['date'].dt.to_period('M').nunique()

avg_monthly_expenses = expenses / total_months
avg_monthly_income = income / total_months
burn_rate = avg_monthly_expenses - avg_monthly_income
runway_months = current_cash / burn_rate if burn_rate > 0 else float('inf')

# --- UI 渲染 ---
col1, col2, col3 = st.columns(3)
col1.metric("當前現金 (USD)", f"${current_cash:,}")
col2.metric("月均燒錢 (Burn Rate)", f"${burn_rate:,.2f}", delta_color="inverse")
st.markdown(f"### ⚠️ 警告：依照目前燒錢速度，您的企業將在 **<span style='color:red'>{runway_months:.1f} 個月</span>** 後資金耗盡！", unsafe_allow_html=True)
st.divider()

st.subheader("📈 歷史收支圖")
fig = px.line(df, x='date', y='amount', color='type', title="營收 vs 支出趨勢")
st.plotly_chart(fig, width='stretch')

# ==========================================
# 🚀 模塊 1：即時單位經濟效益 (Unit Economics)
# ==========================================
st.divider()
st.subheader("🎯 即時單位經濟效益 (LTV / CAC Ratio)")
st.markdown("VC 最在乎的指標：您花多少錢獲取一個客戶？這個客戶一輩子能幫您賺多少錢？")

with st.expander("⚙️ 展開以調整本月行銷參數 (Demo 互動區)"):
    st.markdown("👇 **試著拉動下方滑桿，看看指標如何即時變化！**")
    marketing_spend = st.slider("本月廣告總支出 (USD)", 1000, 20000, 5000, step=500)
    new_customers = st.slider("本月新增付費客戶數", 10, 500, 50, step=10)
    avg_revenue_per_user = st.slider("客戶平均終身貢獻 (LTV, USD)", 100, 2000, 400, step=50)

cac = marketing_spend / new_customers if new_customers > 0 else 0
ltv = avg_revenue_per_user
ltv_cac_ratio = ltv / cac if cac > 0 else 0

if ltv_cac_ratio >= 3:
    status_text = "🟢 增長健康 (適合踩油門)"
    ratio_color = "normal"
elif ltv_cac_ratio >= 1:
    status_text = "🟡 警戒狀態 (需優化轉換率)"
    ratio_color = "off"
else:
    status_text = "🔴 嚴重虧損 (每拉一客賠一客)"
    ratio_color = "inverse"

ue_col1, ue_col2, ue_col3 = st.columns(3)
ue_col1.metric("獲客成本 (CAC)", f"${cac:,.0f}")
ue_col2.metric("客戶終身價值 (LTV)", f"${ltv:,.0f}")
ue_col3.metric("LTV/CAC 比例", f"{ltv_cac_ratio:.1f}x", status_text, delta_color=ratio_color)


# ==========================================
# 🚀 模塊 2：AI 核心功能區 (What-If, VC Update & Tax)
# ==========================================
st.divider()
st.subheader("💬 AI CFO 動態情境推演 & 報告生成")

# --- 安全讀取 API Key ---
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    MY_API_KEY = " "

if not MY_API_KEY:
    st.error("👈 老闆，系統找不到 API Key！請確認已經在 Streamlit 後台的 Secrets 貼上 `GEMINI_API_KEY = \"你的英數密碼\"`。")
else:
    client = genai.Client(api_key=MY_API_KEY)

    financial_summary = f"""
    目前現金: ${current_cash}
    月均營收: ${avg_monthly_income:.2f}
    月均支出: ${avg_monthly_expenses:.2f}
    當前 Burn Rate: ${burn_rate:.2f}
    預計 Runway: {runway_months:.1f} 個月
    當前 CAC: ${cac:.0f}
    當前 LTV: ${ltv:.0f}
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("老闆，您想模擬什麼情境？(例如：如果下個月多請一個月薪一萬的工程師...)"):
        
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        system_prompt = f"""
        你是一個矽谷新創的 AI CFO，說話風格專業且一針見血。
        以下是公司目前的財務狀況：
        {financial_summary}
        請根據上述資料回答，精確計算決策對 Runway 和財務的影響。
        CEO 問：{prompt}
        """

        with st.chat_message("assistant"):
            with st.spinner("AI CFO 正在推演未來風險..."):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=system_prompt,
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                except errors.APIError as e:
                    if e.code == 429:
                        st.error("⏳ 老闆，您按太快啦！請喝口水，等候 1 分鐘後再發問一次。")
                    elif e.code == 503:
                        st.error("🚦 Google 伺服器目前大塞車 (503)，請稍等 10 秒後重試！")
                    else:
                        st.error(f"❌ 發生 API 錯誤：{e.code} - {e.message}")
                except Exception as e:
                    st.error(f"❌ 發生未知的系統錯誤：{e}")

    # --- 模塊 2.1：一鍵生成投資人報告 ---
    st.markdown("---")
    st.markdown("#### 📝 一鍵生成 CEO 每月致股東信")
    st.markdown("月底到了，不想寫報告？讓 AI 幫你把數據轉化為專業的 VC Update。")

    if st.button("✨ 幫我寫這封信給 VC", use_container_width=True):
        
        with st.spinner("AI 正在為您撰寫專業的投資人報告..."):
            vc_prompt = f"""
            你是一位專業的矽谷新創 CEO。請根據以下公司本月的財務數據，寫一封給風險投資人 (VC) 的「每月致股東信 (Monthly Investor Update)」。
            語氣要充滿自信、簡潔明瞭，並展現出你對公司狀況的完全掌控。
            
            必須包含以下三個段落：
            1. 執行摘要 (Executive Summary)
            2. 財務亮點與隱憂 (Financial Highlights & Risks)
            3. 下個月的行動計畫 (Next Steps)

            本月真實數據：
            {financial_summary}
            """
            
            try:
                response_vc = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=vc_prompt,
                )
                st.success("✅ 報告生成成功！請過目並直接複製寄出：")
                st.info(response_vc.text)
            except Exception as e:
                st.error(f"❌ 報告生成失敗：{e}")

    # ==========================================
    # 🚀 模塊 3：主動式節稅大腦 (Tax Strategist)
    # ==========================================
    st.markdown("---")
    st.subheader("🧠 主動式節稅大腦 (Proactive Tax Strategist)")
    st.markdown("傳統軟體只會記帳，AI CFO 會主動幫您找錢。系統將自動掃描『雜項』支出，尋找合法的抵稅空間。")

    tax_data = {
        '日期': ['2024-03-18', '2024-03-20', '2024-03-22', '2024-03-25'],
        '廠商': ['AWS', 'Google Workspace', 'WeWork', 'Uber Eats'],
        '金額 (USD)': [2500, 300, 5000, 150],
        '當前分類': ['雲端服務', '軟體訂閱', '雜項 (Misc)', '餐飲']
    }
    df_tax = pd.DataFrame(tax_data)
    
    st.markdown("📋 **本月待審查支出明細：**")
    st.dataframe(df_tax, use_container_width=True)

    if st.button("🔍 啟動 AI 節稅掃描 (Run AI Tax Audit)", type="primary", use_container_width=True):
        
        with st.spinner("AI 正在比對美國國稅局 (IRS) 稅法與您的支出紀錄..."):
            
            tax_prompt = f"""
            你是一位精通美國稅法 (IRS) 的 AI CFO。
            請檢視以下這份公司的支出紀錄清單：
            {df_tax.to_string(index=False)}
            
            你的任務是：
            1. 找出被錯誤歸類在「雜項 (Misc)」的支出（例如 WeWork）。
            2. 建議正確的會計分類（例如：辦公室租金 Office Rent）。
            3. 說明將其正確歸類後，以 21% 企業所得稅率計算，可以為公司合法省下多少稅金？(請列出算式)
            4. 輸出語氣要像一個專業、幫老闆省到錢而準備邀功的頂級財務顧問。
            """
            
            try:
                response_tax = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=tax_prompt,
                )
                
                st.balloons()
                st.success("✨ 掃描完成！發現潛在節稅空間！")
                st.info(response_tax.text)
                
            except Exception as e:
                st.error(f"❌ 掃描失敗：{e}")