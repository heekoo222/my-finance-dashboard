import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Family Wealth Master v3.1", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 19px !important; }
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; color: #1e293b; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 700; background-color: #2563eb; color: white; height: 3.5rem; font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset & Tax Master")
st.info("💡 **좌측 설정**: 만원 단위 | **우측 결과**: 자산(억원), 월 지출/세금(만원)")

# --- 2. 데이터 영속성 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 탭 기반 가정사항 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 환경 설정")

with st.sidebar.expander("📅 기본 정보 & 기간", expanded=True):
    start_year = st.number_input("시작 연도", value=2026, min_value=2024)
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830); h_inc = st.number_input("남편 인상률(%)", value=3.0) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55); h_p_amt = st.number_input("남편 연금액", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500); w_inc = st.number_input("아내 인상률(%)", value=3.0) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55); w_p_amt = st.number_input("아내 연금액", value=130)

# [요청 1-1] 금융 투자 탭
with st.sidebar.expander("📈 금융투자 & 자산 배분", expanded=False):
    inv_init = st.number_input("현재 금융투자금(만)", value=10000)
    inv_gr = st.number_input("연간 기대 수익률(%)", value=7.0) / 100
    st.markdown("---")
    st.write("💰 **잉여 자금 배분 비율**")
    inv_ratio = st.slider("금융자산 배분율(%)", 0, 100, 90)
    cash_ratio = 100 - inv_ratio
    st.caption(f"잉여금의 {inv_ratio}%는 금융자산, {cash_ratio}%는 예금으로 배분됩니다.")

# [요청 1-2] 대출 탭
with st.sidebar.expander("💳 대출 상세 설정", expanded=False):
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000)
    debt_r = st.number_input("대출 이자율(%)", value=3.9) / 100
    debt_term = st.number_input("상환 기간(년)", value=30)
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"])

with st.sidebar.expander("🏠 부동산 & 지출 & 이벤트", expanded=False):
    re_init_val = st.number_input("현재 부동산(만)", value=140000)
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0) / 100
    living_monthly = st.number_input("현재 월 생활비(만)", value=400)
    living_gr = st.number_input("생활비 인상률(%)", value=2.0) / 100
    if st.button("➕ 부동산 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    if st.button("➕ 특별 이벤트 추가"):
        st.session_state.events.append({"name": "이벤트", "year": 2030, "cost": 0})

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_year, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        
        # 1. 수입
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pension = (h_p_amt * 12 if h_age >= 65 else 0) + (w_p_amt * 12 if w_age >= 65 else 0)
        total_income_annual = inc_h + inc_w + pension
        
        # 2. 세금 로직 (전문가 수준 상세화)
        tax_income = total_income_annual * 0.15 # 소득세(지방세 포함)
        tax_holding = (c_re * 0.6) * 0.0015     # 재산세
        tax_comprehensive = max(0, (c_re - 120000) * 0.005) # 종부세(12억 초과분 가정)
        tax_financial = max(0, (c_inv * inv_gr - 2000) * 0.154) # 금융소득과세
        tax_acq, tax_gains = 0, 0 # 취득세, 양도세 초기화
        
        # 3. 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                profit = max(0, c_re - re_init_val)
                tax_gains = profit * 0.20 # 양도세
                tax_acq = tr['new_price'] * 0.033 # 취득세
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 이동")

        # 4. 대출 상환 (상환 방식 반영)
        interest_annual = c_debt * debt_r
        if c_debt > 0 and (year < start_year + debt_term):
            if debt_type == "원리금균등":
                r = debt_r
                n = debt_term
                repay_total = (debt_init * r * (1+r)**n) / ((1+r)**n - 1)
                principal_repay = repay_total - interest_annual
            else: # 원금균등
                principal_repay = debt_init / debt_term
                repay_total = principal_repay + interest_annual
        else:
            principal_repay, repay_total = 0, 0

        # 5. 지출 및 순현금흐름
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_year))
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        k_cost = 0 # 양육비는 설정값 루프 돌려 합산 (생략 로직 유지)
        
        total_tax = tax_income + tax_holding + tax_comprehensive + tax_financial + tax_acq + tax_gains
        total_expense = curr_living + k_cost + total_tax + repay_total + ev_cost
        net_flow = total_income_annual - total_expense
        
        # 6. 자산 배분 (요청하신 배분 비율 적용)
        if net_flow > 0:
            c_inv += net_flow * (inv_ratio / 100)
            c_cash += net_flow * (cash_ratio / 100)
        else:
            c_cash += net_flow # 적자 시 예금에서 차감
            
        c_re *= (1 + re_gr_rate)
        c_inv *= (1 + inv_gr)
        c_debt = max(0, c_debt - principal_repay)
        
        res.append({
            "year": year, "age": f"{h_age}/{w_age}",
            "net_asset": (c_re + c_inv + c_cash - c_debt)/10000,
            "re": c_re/10000, "inv": c_inv/10000, "debt": c_debt/10000,
            "m_spend": total_expense/12, "m_net": net_flow/12,
            "tax_total": total_tax, "tax_inc": tax_income, "tax_hold": tax_holding + tax_comprehensive,
            "tax_fin": tax_financial, "tax_trade": tax_acq + tax_gains,
            "event": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 대시보드 출력 ---
main_tab, tax_tab, data_tab = st.tabs(["📊 자산 로드맵", "⚖️ 상세 세금 분석", "📋 데이터 시트"])

with main_tab:
    p_len = st.select_slider("시뮬레이션 기간", options=[10, 20, 30, 70], value=30)
    sub = df.head(p_len)

    # 누적 막대 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net_asset"], name="순자산(억)", marker_color='#10b981'))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt"], name="부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=550, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 지표
    c1, c2, c3, c4 = st.columns(4)
    def draw_bar(data, col, title, color):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color))
        f.update_layout(title=title, height=280, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_bar(sub, "re", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub, "inv", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub, "m_spend", "💸 월 지출액(만)", "#f43f5e"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub, "m_net", "💰 월 순현금흐름(만)", "#10b981"), use_container_width=True)

with tax_tab:
    # [요청 2] 세금 상세 대시보드
    st.header("⚖️ 연도별 상세 세금 리포트")
    
    # 세금 차트 (에러 수정됨: 바다코끼리 연산자 제거)
    fig_tax = go.Figure()
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["tax_inc"], name="소득세(만)", stackgroup='one', fill='tonexty'))
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["tax_hold"], name="보유/종부세(만)", stackgroup='one', fill='tonexty'))
    
    # 거래세가 있는 연도만 따로 추출하여 표시
    trade_years = sub[sub['tax_trade'] > 0]
    if not trade_years.empty:
        fig_tax.add_trace(go.Scatter(x=trade_years["year"], y=trade_years["tax_trade"], 
                                     name="취득/양도세(이벤트)", mode='markers', marker=dict(size=12, symbol='diamond')))
    
    fig_tax.update_layout(title="세금 항목별 지출 추이 (만원)", height=500, template="plotly_white")
    st.plotly_chart(fig_tax, use_container_width=True)
    
    # 세금 데이터 표
    st.subheader("📋 세목별 상세 데이터 (만원)")
    tax_df = sub[["year", "age", "tax_inc", "tax_hold", "tax_fin", "tax_trade", "tax_total"]].copy()
    tax_df.columns = ["연도", "나이", "소득세", "보유/종부세", "금융소득세", "취득/양도세", "세금합계"]
    st.dataframe(tax_df.style.format("{:.0f}"), use_container_width=True)

with data_tab:
    st.subheader("📋 전체 시뮬레이션 상세 수치")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
