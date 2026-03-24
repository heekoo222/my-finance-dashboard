import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인 고도화
st.set_page_config(page_title="Family Wealth Master v4.0", layout="wide")

# 가독성을 위한 CSS (폰트 확대 및 카드 디자인)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 20px !important; }
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 700; background-color: #2563eb; color: white; height: 3.5rem; font-size: 22px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset & Tax Master")
st.markdown("남편(95) & 아내(94)를 위한 **최고급 통합 자산 시뮬레이터**")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 환경 설정")

with st.sidebar.expander("📅 기본 정보 & 시작연도", expanded=True):
    start_year = st.number_input("시뮬레이션 시작 연도", value=2026, min_value=2024)
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830); h_inc = st.number_input("인상률(%)", value=3.0) / 100
        h_ret = st.number_input("은퇴나이", value=55, key="hret"); h_p_amt = st.number_input("연금액", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500); w_inc = st.number_input("인상률(%)", value=3.0) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55, key="wret"); w_p_amt = st.number_input("연금액", value=130)

with st.sidebar.expander("📈 금융투자 & 자산 배분", expanded=False):
    inv_init = st.number_input("현재 금융투자금(만)", value=10000)
    inv_gr = st.number_input("연간 기대 수익률(%)", value=7.0) / 100
    st.markdown("---")
    st.write("💰 **잉여 자금 배분 비율**")
    inv_ratio = st.slider("금융자산 배분율(%)", 0, 100, 90)
    cash_ratio = 100 - inv_ratio

with st.sidebar.expander("💳 대출 상세 설정", expanded=False):
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000)
    debt_r = st.number_input("대출 이자율(%)", value=3.9) / 100
    debt_term = st.number_input("상환 기간(년)", value=30)
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"])

with st.sidebar.expander("🏠 부동산 & 지출 & 이벤트", expanded=False):
    re_init_val = st.number_input("현재 부동산(만)", value=140000)
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0) / 100
    living_monthly = st.number_input("월 생활비(만)", value=400)
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
        total_income_gross = inc_h + inc_w + pension
        
        # 2. 세금 (모든 변수 0으로 초기화하여 에러 방지)
        t_inc, t_hold, t_comp, t_fin, t_acq, t_gain = 0, 0, 0, 0, 0, 0
        t_inc = total_income_gross * 0.15 
        t_hold = (c_re * 0.6) * 0.0015
        t_comp = max(0, (c_re - 120000) * 0.005)
        t_fin = max(0, (c_inv * inv_gr - 2000) * 0.154)
        
        # 3. 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                t_gain = max(0, c_re - re_init_val) * 0.20
                t_acq = tr['new_price'] * 0.033
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 이동")

        # 4. 대출 및 지출
        interest_a = c_debt * debt_r
        if c_debt > 0 and (year < start_year + debt_term):
            if debt_type == "원리금균등":
                repay_a = (debt_init * debt_r * (1+debt_r)**debt_term) / ((1+debt_r)**debt_term - 1)
                principal_a = repay_a - interest_a
            else:
                principal_a = debt_init / debt_term
                repay_a = principal_a + interest_a
        else:
            principal_a, repay_a = 0, 0

        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_year))
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        for ev in st.session_state.events:
            if year == ev['year']: ev_list.append(f"🚀{ev['name']}")
            
        k_cost = 0 # 자녀 양육비 생략 로직 유지
        
        # 5. 자산 배분
        total_tax = t_inc + t_hold + t_comp + t_fin + t_acq + t_gain
        total_exp = curr_living + k_cost + total_tax + repay_a + ev_cost
        net_flow = total_income_gross - total_exp
        
        if net_flow > 0:
            c_inv += net_flow * (inv_ratio / 100)
            c_cash += net_flow * (cash_ratio / 100)
        else:
            c_cash += net_flow
            
        c_re *= (1 + re_gr_rate)
        c_inv *= (1 + inv_gr)
        c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "year": year, "age": f"{h_age}/{w_age}",
            "net_asset": (c_re + c_inv + c_cash - c_debt)/10000,
            "re": c_re/10000, "inv": c_inv/10000, "debt": c_debt/10000,
            "m_spend": total_exp/12, "m_net": net_flow/12,
            "t_total": total_tax, "t_inc": t_inc, "t_hold": t_hold + t_comp,
            "t_fin": t_fin, "t_trade": t_acq + t_gain,
            "event": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 결과 시각화 및 대시보드 ---
m_tab, t_tab, d_tab = st.tabs(["📊 자산 로드맵", "⚖️ 상세 세금 분석", "📋 데이터 시트"])

with m_tab:
    # 요청하신 기간 선택 탭 방식
    p_choice = st.radio("시뮬레이션 조회 기간", ["10년", "20년", "30년", "전체"], horizontal=True, index=3)
    p_len = {"10년":10, "20년":20, "30년":30, "전체":len(df)}[p_choice]
    sub = df.head(p_len)

    # 메인 누적 막대 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net_asset"], name="순자산(억)", marker_color='#10b981',
                         customdata=sub[["age", "m_net", "event"]],
                         hovertemplate="<b>%{x}년 (%{customdata[0]})</b><br>순자산: %{y:.2f}억<br>월 순현금: %{customdata[1]:,.0f}만<br>이벤트: %{customdata[2]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt"], name="부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=16))
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 지표
    c1, c2, c3, c4 = st.columns(4)
    def draw_mini(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=20)), height=300, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_mini(sub, "re", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "inv", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_mini(sub, "m_spend", "💸 월 지출(만)", "#f43f5e", "만"), use_container_width=True)
    c4.plotly_chart(draw_mini(sub, "m_net", "💰 월 순현금(만)", "#10b981", "만"), use_container_width=True)

with t_tab:
    st.header("⚖️ 연도별 상세 세금 리포트")
    # 세금 차트
    fig_tax = go.Figure()
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["t_inc"], name="소득세", stackgroup='one', fill='tonexty'))
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["t_hold"], name="보유/종부세", stackgroup='one', fill='tonexty'))
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["t_fin"], name="금융소득세", stackgroup='one', fill='tonexty'))
    
    trade_only = sub[sub['t_trade'] > 0]
    if not trade_only.empty:
        fig_tax.add_trace(go.Scatter(x=trade_only["year"], y=trade_only["t_trade"], name="취득/양도세", mode='markers', marker=dict(size=15, symbol='diamond')))
    
    fig_tax.update_layout(height=500, template="plotly_white", font=dict(size=16), title="연도별 세목별 지출(만원)")
    st.plotly_chart(fig_tax, use_container_width=True)

    # 세금 데이터 표 (에러 수정 포인트: 숫자 컬럼만 포맷팅)
    tax_df = sub[["year", "age", "t_inc", "t_hold", "t_fin", "t_trade", "t_total"]].copy()
    tax_df.columns = ["연도", "나이", "소득세(만)", "보유세(만)", "금융세(만)", "거래세(만)", "합계(만)"]
    
    # 스타일 적용 시 숫자 컬럼만 지정하여 ValueError 방지
    num_cols = ["소득세(만)", "보유세(만)", "금융세(만)", "거래세(만)", "합계(만)"]
    st.dataframe(tax_df.style.format({c: "{:,.0f}" for c in num_cols}), use_container_width=True)

with d_tab:
    st.subheader("📋 전체 시뮬레이션 상세 수치")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
