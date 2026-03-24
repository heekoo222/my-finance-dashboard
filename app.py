import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="가족 자산 관리 대시보드", layout="wide")

# --- 전역 설정 및 스타일 ---
st.title("👨‍👩‍👧‍👦 우리 가족 미래 자산 시뮬레이터")
st.markdown("95년생 가장의 100세(2095년)까지의 여정")

# --- 사이드바: 주요 가정 사항 ---
st.sidebar.header("📍 기본 가정")
user_birth_year = 1995
start_year = 2025
end_year = 2095

with st.sidebar.expander("💰 자산 초기값 & 수익률", expanded=True):
    # 부동산
    re_init = st.number_input("부동산 시작 (억원)", value=14.0, step=0.1)
    re_rate = st.slider("부동산 상승률 (%)", 0.0, 10.0, 4.0) / 100
    # 금융투자
    inv_init = st.number_input("금융투자 시작 (억원)", value=0.6, step=0.1)
    inv_rate = st.slider("투자 수익률 (%)", 0.0, 15.0, 8.0) / 100
    # 예금 및 기타
    cash_init = st.number_input("예금/기타 시작 (억원)", value=0.05, step=0.01)
    cash_rate = st.slider("예금 금리 (%)", 0.0, 5.0, 2.0) / 100

with st.sidebar.expander("👶 자녀 계획 & 양육비", expanded=False):
    num_kids = st.number_input("자녀 수", min_value=0, max_value=3, value=1)
    kid_plans = []
    for i in range(num_kids):
        st.write(f"--- {i+1}번째 자녀 ---")
        birth = st.number_input(f"{i+1}번 자녀 출산년도", value=2027 + (i*2), key=f"kid_birth_{i}")
        kid_plans.append(birth)
    
    st.info("시기별 월 양육비(만원)")
    cost_baby = st.number_input("유아기(0~7세)", value=100)
    cost_elem = st.number_input("초등(8~13세)", value=120)
    cost_mid = st.number_input("중등(14~16세)", value=150)
    cost_high = st.number_input("고등(17~19세)", value=180)
    cost_univ = st.number_input("대학(20~23세)", value=250)

with st.sidebar.expander("🚗 특별 이벤트 (육아휴직, 차량 등)", expanded=False):
    event_year = st.number_input("이벤트 발생년도", value=2030)
    event_cost = st.number_input("이벤트 비용 (억원)", value=0.5, step=0.1)
    event_name = st.text_input("이벤트 명", "차량 구매/육아휴직")

# --- 시뮬레이션 로직 ---
def run_simulation():
    rows = []
    curr_re = re_init
    curr_inv = inv_init
    curr_cash = cash_init
    
    # 단순화를 위한 수입/지출 가설 (억원 단위)
    annual_savings = 0.5 # 연간 저축액 가설 (수정 가능)

    for year in range(start_year, end_year + 1):
        age = year - user_birth_year
        
        # 자녀 양육비 계산 (억원 단위 환산)
        total_kid_cost = 0
        for b_year in kid_plans:
            k_age = year - b_year
            if 0 <= k_age <= 7: total_kid_cost += (cost_baby * 12) / 10000
            elif 8 <= k_age <= 13: total_kid_cost += (cost_elem * 12) / 10000
            elif 14 <= k_age <= 16: total_kid_cost += (cost_mid * 12) / 10000
            elif 17 <= k_age <= 19: total_kid_cost += (cost_high * 12) / 10000
            elif 20 <= k_age <= 23: total_kid_cost += (cost_univ * 12) / 10000
        
        # 이벤트 반영
        current_event_cost = event_cost if year == event_year else 0
        
        # 자산 성장
        curr_re *= (1 + re_rate)
        curr_inv *= (1 + inv_rate)
        curr_cash *= (1 + cash_rate)
        
        # 저축액 배분 (금융투자에 합산 가정)
        net_savings = annual_savings - total_kid_cost - current_event_cost
        curr_inv += net_savings
        
        total_asset = curr_re + curr_inv + curr_cash
        
        rows.append({
            "연도": f"{year}년",
            "나이": f"{age}세",
            "부동산": round(curr_re, 2),
            "금융 투자": round(curr_inv, 2),
            "예금": round(curr_cash, 2),
            "합계": round(total_asset, 2)
        })
    return pd.DataFrame(rows)

df = run_simulation()

# --- 대시보드 표시 ---
# 1. 탭 구성 (기간별 보기)
st.subheader("📊 기간별 자산 전망 (단위: 억원)")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["10년", "20년", "30년", "50년", "전체"])

def draw_chart(data):
    fig = go.Figure()
    for col in ["부동산", "금융 투자", "예금"]:
        fig.add_trace(go.Bar(x=data["연도"] + " (" + data["나이"] + ")", y=data[col], name=col))
    
    fig.update_layout(barmode='stack', hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab1: draw_chart(df.head(10))
with tab2: draw_chart(df.head(20))
with tab3: draw_chart(df.head(30))
with tab4: draw_chart(df.head(50))
with tab5: draw_chart(df)

# 2. 데이터 수정 및 확인 섹션
st.divider()
st.subheader("📑 연도별 자산 상세 데이터")
st.info("아래 표에서 수치를 확인하거나, 왼쪽 사이드바에서 가정을 수정해 보세요.")

# 가독성을 위해 데이터프레임 스타일 적용
st.dataframe(
    df,
    column_config={
        "부동산": st.column_config.NumberColumn(format="%.2f 억"),
        "금융 투자": st.column_config.NumberColumn(format="%.2f 억"),
        "예금": st.column_config.NumberColumn(format="%.2f 억"),
        "합계": st.column_config.NumberColumn(format="%.2f 억"),
    },
    use_container_width=True,
    hide_index=True
)

st.success("Tip: 왼쪽 사이드바에서 자녀 출산년도를 바꾸면 즉시 그래프의 성장 곡선이 변화합니다.")
