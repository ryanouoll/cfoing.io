import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import errors
#python -m streamlit run first.py

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

st.divider()
st.subheader("💬 AI CFO 動態情境推演 (What-If 預測)")

# --- 安全讀取 API Key ---
try:
    # 這裡會自動去 Streamlit Cloud 的 Secrets 裡面找 GEMINI_API_KEY
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    MY_API_KEY = "AIzaSyAW-6fVW42ANPwRI4AauvI3tmsR_-zRbSg"
    

if not MY_API_KEY:
    st.error("👈 老闆，系統找不到 API Key！請確認已經在 Streamlit 後台的 Secrets 貼上 `GEMINI_API_KEY = \"你的英數密碼\"`。")
else:
    # --- 新版 SDK 的連線方式 ---
    client = genai.Client(api_key=MY_API_KEY)

    financial_summary = f"""
    目前現金: ${current_cash}
    月均營收: ${avg_monthly_income:.2f}
    月均支出: ${avg_monthly_expenses:.2f}
    當前 Burn Rate: ${burn_rate:.2f}
    預計 Runway: {runway_months:.1f} 個月
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 聊天輸入框
    if prompt := st.chat_input("老闆，您想模擬什麼情境？(例如：如果下個月多請一個月薪一萬的工程師...)"):
        
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        system_prompt = f"""
        你是一個矽谷新創的 AI CFO，說話風格專業且一針見血。
        以下是公司目前的財務狀況：
        {financial_summary}
        請根據上述資料回答，精確計算決策對 Runway 的影響。
        CEO 問：{prompt}
        """

        with st.chat_message("assistant"):
            with st.spinner("AI CFO 正在推演未來風險... (若轉圈較久請耐心等待幾秒鐘)"):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=system_prompt,
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                except errors.APIError as e:
                    if e.code == 429:
                        st.error("⏳ 老闆，您按太快啦！免費版 API 有頻率限制，請喝口水，等候 1 分鐘後再發問一次。")
                    elif e.code == 503:
                        st.error("🚦 Google 伺服器目前大塞車 (503)，請稍等 10 秒後重試！")
                    else:
                        st.error(f"❌ 發生 API 錯誤：{e.code} - {e.message}")
                except Exception as e:
                    st.error(f"❌ 發生未知的系統錯誤：{e}")

    # ==========================================
    # 🚀 新功能：一鍵生成投資人報告 (VC Updates)
    # ==========================================
    st.divider()
    st.subheader("📝 一鍵生成 CEO 每月致股東信")
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
                    model='gemini-2.5-flash',
                    contents=vc_prompt,
                )
                st.success("✅ 報告生成成功！請過目並直接複製寄出：")
                st.info(response_vc.text)
            except Exception as e:
                st.error(f"❌ 報告生成失敗：{e}")