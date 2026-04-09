import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import errors

# --- 頁面設定 ---
st.set_page_config(page_title="AI CFO Dashboard", layout="wide")
st.title("📊 超級 AI CFO - 新創續命儀表板")

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
st.plotly_chart(fig, width='stretch') # 這裡修復了圖表的過期警告

st.divider()
st.subheader("💬 AI CFO 動態情境推演 (What-If 預測)")

# --- ⚠️ 記得把你的 API Key 貼回這裡 (保留雙引號！) ---
MY_API_KEY = "AIzaSyBUNsG8yUbBUdhJvzoQlwzEPLcgULcJRhw"

if MY_API_KEY == "在這裡貼上你的_API_KEY" or not MY_API_KEY:
    st.warning("👈 老闆，請先到程式碼裡面貼上您的 Gemini API Key，AI 大腦才能啟動！")
else:
    # 這是新版 SDK 的連線方式
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
                    # 剛剛的報錯證明 gemini-2.0-flash 是認得的，直接用它！
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=system_prompt,
                    )
                    st.markdown(response.text)
                    
                    # 只有成功拿到回覆，才寫入對話紀錄 (修正先前的 NameError)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                except errors.APIError as e:
                    # 完美的防彈護盾：把 API 錯誤轉化為人類看得懂的警告，且不讓程式崩潰
                    if e.code == 429:
                        st.error("⏳ 老闆，您按太快啦！免費版 API 有頻率限制，請喝口水，等候 1 分鐘後再發問一次。")
                    elif e.code == 503:
                        st.error("🚦 Google 伺服器目前大塞車 (503)，請稍等 10 秒後重試！")
                    else:
                        st.error(f"❌ 發生 API 錯誤：{e.code} - {e.message}")
                except Exception as e:
                    st.error(f"❌ 發生未知的系統錯誤：{e}")