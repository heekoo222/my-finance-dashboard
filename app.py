import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="우리집 재무 Plan 대시보드", layout="wide")

st.title("💰 개인 자산 현황 및 향후 계획 Dashboard")
st.markdown("가정 사항을 수정하면 하단의 자산 시뮬레이션 결과가 즉시 업데이트됩니다.")

# --- 사이드바: 주요 가정 사항 입력 ---
st.sidebar.header("⚙️ 주요 가정 사항")

# 1. 수입 및 지출 관련
with st.sidebar.expander("💳 수입 및 지출", expanded=True):
    base_salary = st.number_input("현재 월급 (세후, 만원)", value=830)
    salary_growth = st.slider("연봉 인상율 (%)", 0.0, 10.0, 3.0, 0.5) / 100
    incentive_rate = st.slider("성과급 비율 (연봉 대비 %)", 0.0, 50.0, 10.0, 1.0) / 100
    living_expenses = st.number_input("연간 생활비 (만원)", value=2300)
    living_exp_growth = st.slider("생활비 인상율 (%)", 0.0, 5.0, 3.0, 0.5) / 100

# 2. 투자 및 자산 관련
with st.sidebar.expander("📈 투자 및 부동산", expanded=True):
    inv_return_rate = st.slider("투자 수익율 (%)", 0.0, 15.0, 8.0, 0.5) / 100
    re_return_rate = st.slider("부동산 상승율 (%)", 0.0, 10.0, 4.0, 0.5) / 100
    initial_re_asset = st.number_input("현재 부동산 자산 (만원)", value=140000)
    initial_inv_principal = st.number_input("현재 투자 원금 (만원)", value=5900)

# 3. 부채 및 가족
with st.sidebar.expander("🏠 대출 및 육아", expanded=True):
    mortgage = st.number_input("주담대 잔액 (만원)", value=60000)
    interest_rate = st.slider("대출 이자율 (%)", 0.0, 7.0, 3.9, 0.1) / 100
    num_kids = st.radio("자녀 수", [0, 1, 2], index=1)
    retirement_age = st.slider("은퇴 시점 (나이)", 45, 65, 55)

# --- 시뮬레이션 로직 ---
def run_simulation():
    data = []
    current_age = 25
    years = 100 - current_age # 100세까지 시뮬레이션
    
    # 초기값 세팅
    curr_re = initial_re_asset
    curr_inv_principal = initial_inv_principal
    curr_inv_returns = initial_inv_principal * (1 + inv_return_rate)
    curr_debt = mortgage
    curr_salary = base_salary
    
    for i in range(years + 1):
        age = current_age + i
        
        # 1. 수입 계산 (은퇴 전까지만)
        if age <= retirement_age:
            annual_pay = curr_salary * 12
            incentive = annual_pay * incentive_rate
            other_income = 500 # 기타수입 고정값 예시
        else:
            annual_pay = 0
            incentive = 0
            other_income = 2000 # 국민연금 등 가정
            
        # 2. 지출 계산
        curr_interest = curr_debt * interest_rate
        # 육아비용 (자녀 나이에 따른 단순 가중치 적용 가능)
        childcare = (960 if num_kids >= 1 else 0) + (900 if num_kids >= 2 else 0)
        
        # 이벤트 지출 (특정 나이에 발생)
        event_cost = 0
        if age == 27: event_cost = 5000 # 출산 및 차량
        if age == 33: event_cost = 80000 # 상급지 이동 등
        
        # 3. 여유 자금 및 부채 상환
        surplus = (annual_pay + incentive + other_income) - (living_expenses + curr_interest + childcare + event_cost)
        debt_repayment = min(curr_debt, 500 + (surplus * 0.2 if surplus > 0 else 0)) # 매년 최소 500만원 + 여유분 20% 상환 가정
        
        invest_amount = surplus - debt_repayment
        
        # 4. 자산 업데이트
        curr_re *= (1 + re_return_rate)
        curr_inv_returns = (curr_inv_returns + invest_amount) * (1 + inv_return_rate)
        curr_debt -= debt_repayment
        
        total_asset = curr_re + curr_inv_returns + 500 # 예금 500 고정
        net_asset = total_asset - curr_debt
        
        data.append({
            "나이": age,
            "총 자산": round(total_asset),
            "순 자산": round(net_asset),
            "부동산": round(curr_re),
            "금융자산": round(curr_inv_returns),
            "부채": round(curr_debt),
            "연봉": round(annual_pay),
            "여유자금": round(surplus)
        })
        
        # 다음 해를 위한 수입/지출 증가율 반영
        curr_salary *= (1 + salary_growth)
        # living_expenses 는 여기서 직접 업데이트하거나 루프 밖에서 인덱스 처리
        
    return pd.DataFrame(data)

df_result = run_simulation()

# --- 결과 시각화 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 자산 성장 시뮬레이션")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_result["나이"], y=df_result["총 자산"], name="총 자산", fill='tozeroy'))
    fig.add_trace(go.Scatter(x=df_result["나이"], y=df_result["순 자산"], name="순 자산", line=dict(color='firebrick', width=4)))
    fig.update_layout(hovermode="x unified", yaxis_title="만원")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💡 분석 결과")
    final_net_asset = df_result.iloc[retirement_age - 25]["순 자산"]
    st.metric("은퇴 시점 순자산", f"{final_net_asset:,.0f} 만원")
    
    peak_debt = df_result["부채"].max()
    st.metric("최대 부채 규모", f"{peak_debt:,.0f} 만원")

# 상세 데이터 표
st.subheader("📋 연도별 상세 데이터")
st.dataframe(df_result, use_container_width=True)

# 엑셀 다운로드 기능
csv = df_result.to_csv(index=False).encode('utf-8-sig')
st.download_button("결과를 CSV로 다운로드", csv, "financial_plan_result.csv", "text/csv")
