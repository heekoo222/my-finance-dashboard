import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="부부 통합 자산 시뮬레이터", layout="wide")

st.title("🏙️ 부부 통합 자산 관리 & 부동산 갈아타기 시뮬레이터")

# --- 세션 스테이트 초기화 (이벤트 및 갈아타기) ---
if 'events' not in st.session_state:
    st.session_state.events = []
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "priority": ["금융자산", "대출", "예금"]}]

# --- 사이드바 설정 ---
st.sidebar.header("📍 상세 설정")

with st.sidebar.expander("👤 부부 및 기본 소득", expanded=False):
    h_sal = st.number_input("남편 월급(만)", value=550); h_ret = st.number_input("남편 은퇴나이", value=55)
    w_sal = st.number_input("아내 월급(만)", value=500); w_ret = st.number_input("아내 은퇴나이", value=55)
    h_inc = st.number_input("급여 인상률(%)", value=3.0) / 100

with st.sidebar.expander("🏠 부동산 & 대출 초기값", expanded=True):
    re_init = st.number_input("현재 부동산 가액(억)", value=14.0)
    re_growth = st.number_input("부동산 상승률(%)", value=4.0) / 100
    debt_init = st.number_input("현재 대출 잔액(억)", value=6.0)
    debt_rate = st.number_input("대출 이자율(%)", value=4.0) / 100
    
with st.sidebar.expander("💰 금융자산 & 세금", expanded=False):
    inv_init = st.number_input("금융투자 시작(억)", value=1.0)
    inv_growth = st.number_input("투자 수익률(%)", value=7.0) / 100
    cash_init = st.number_input("예금 시작(억)", value=0.5)
    tax_base_rate = st.number_input("공시지가 비율(%)", value=60.0) / 100
    holding_tax_rate = st.number_input("보유세율(%)", value=0.2) / 100

# --- 부동산 갈아타기 설정 ---
st.sidebar.subheader("🔄 부동산 갈아타기 계획")
for i, trade in enumerate(st.session_state.re_trades):
    t_col1, t_col2 = st.sidebar.columns(2)
    trade['year'] = t_col1.number_input(f"매수년도", 2025, 2095, trade['year'], key=f"tr_y_{i}")
    trade['new_price'] = t_col2.number_input(f"매수가(억)", 0.0, 100.0, trade['new_price'], key=f"tr_p_{i}")
    trade['priority'] = st.sidebar.multiselect(f"자금 조달 순위", ["금융자산", "예금", "대출"], default=trade['priority'], key=f"tr_pr_{i}")

if st.sidebar.button("➕ 갈아타기 추가"):
    st.session_state.re_trades.append({"year": 2040, "new_price": 30.0, "priority": ["금융자산", "대출", "예금"]})

# --- 시뮬레이션 엔진 ---
def run_sim():
    data = []
    c_re = re_init; c_inv = inv_init; c_cash = cash_init; c_debt = debt_init
    c_h_sal = h_sal; c_w_sal = w_sal
    
    for year in range(2025, 2096):
        h_age = year - 1995; w_age = year - 1994
        
        # 1. 수입
        inc = ((c_h_sal if h_age <= h_ret else 0) + (c_w_sal if w_age <= w_ret else 0)) * 12 * 1.15 / 10000 
        
        # 2. 부동산 갈아타기 로직
        for trade in st.session_state.re_trades:
            if year == trade['year']:
                gap = trade['new_price'] - (c_re * 0.97) # 취등록세 등 감안하여 기존주택 97% 매도 가정
                for source in trade['priority']:
                    if gap <= 0: break
                    if source == "금융자산":
                        use = min(c_inv, gap); c_inv -= use; gap -= use
                    elif source == "예금":
                        use = min(c_cash, gap); c_cash -= use; gap -= use
                    elif source == "대출":
                        c_debt += gap; gap = 0
                c_re = trade['new_price']

        # 3. 지출 (세금: 가액의 60% 공시지가 기준)
        tax_re = (c_re * tax_base_rate) * holding_tax_rate
        interest = c_debt * debt_rate
        living = (400 * 12) / 10000
        
        # 4. 자산 성장 및 흐름
        c_re *= (1 + re_growth)
        c_inv *= (1 + inv_growth)
        
        surplus = inc - (tax_re + interest + living)
        c_inv += surplus # 남는 돈은 금융자산 재투자
        
        total_asset = c_re + c_inv + c_cash
        net_asset = total_asset - c_debt
        
        data.append({
            "연도": year, "나이": f"{h_age}/{w_age}", "순자산": net_asset, "부동산": c_re, 
            "금융자산": c_inv, "예금": c_cash, "부채": c_debt, "총자산": total_asset
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + h_inc)
        
    return pd.DataFrame(data)

df = run_sim()

# --- 결과 시각화 ---
st.subheader("📊 자산군별 추이 분석")
tabs = st.tabs(["10년(근기)", "30년(중기)", "전체(장기)"])

def plot_assets(sub_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부동산"], name="부동산"))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["금융자산"], name="금융자산"))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["예금"], name="예금"))
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산", line=dict(color='black', width=3)))
    fig.update_layout(barmode='stack', hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tabs[0]: plot_assets(df.head(10))
with tabs[1]: plot_assets(df.head(30))
with tabs[2]: plot_assets(df)

# 상세 표
st.subheader("📋 상세 데이터 (억원)")
st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
