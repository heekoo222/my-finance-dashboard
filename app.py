import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Family Wealth Roadmap", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; margin-bottom: 10px; border: 1px solid #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; background-color: #3b82f6; color: white; border: none; height: 3rem;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset Roadmap (2025-2095)")
st.info("💡 모든 입력(왼쪽)은 **'만원'** 단위이며, 결과 차트의 자산은 **'억원'**, 월 지출액은 **'만원'**으로 표시됩니다.")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 모든 레버 통합 (단위: 만원) ---
st.sidebar.header("⚙️ 시뮬레이션 설정 (만원)")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 급여 및 은퇴/연금", expanded=False):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830); h_inc = st.number_input("남편 인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55); h_p_age = st.number_input("남편 연금나이", value=65); h_p_amt = st.number_input("남편 연금액", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500); w_inc = st.number_input("아내 인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55); w_p_age = st.number_input("아내 연금나이", value=65); w_p_amt = st.number_input("아내 연금액", value=130)

# (2) 연간 생활비 설정 (추가)
with st.sidebar.expander("💸 생활비 가정", expanded=True):
    living_2025 = st.number_input("2025년 월 생활비(만원)", value=400)
    living_growth = st.number_input("생활비 연간 인상률(%)", value=2.0, step=0.1) / 100

# (3) 자녀별 시기별 양육비
with st.sidebar.expander("👶 자녀별 양육비 상세", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 탄생년", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학", value=kid['costs'][4], key=f"kc4_{i}")

# (4) 부동산 갈아타기
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.sidebar.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        tr['year'] = st.number_input(f"매수년도 {i}", 2025, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"매수가(만원) {i}", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"투자활용 {i}", value=tr['use_inv'], key=f"tr_i_{i}")
        tr['use_debt'] = c2.number_input(f"대출활용 {i}", value=tr['use_debt'], key=f"tr_d_{i}")
        tr['use_cash'] = c3.number_input(f"예금활용 {i}", value=tr['use_cash'], key=f"tr_c_{i}")

# (5) 특별 이벤트 레버
with st.sidebar.expander("🚀 특별 이벤트 설정", expanded=False):
    if st.sidebar.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "새 이벤트", "year": 2025, "cost": 0})
    for i, ev in enumerate(st.session_state.events):
        e1, e2, e3 = st.columns([2,1,1])
        ev['name'] = e1.text_input(f"이벤트명 {i}", ev['name'], key=f"ev_n_{i}")
        ev['year'] = e2.number_input(f"년도 {i}", 2025, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = e3.number_input(f"비용 {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

# (6) 초기 자산 & 세금
with st.sidebar.expander("📈 기본 자산 & 세금 가정", expanded=False):
    re_init = st.number_input("현재 부동산(만원)", value=140000); re_gr = st.number_input("부동산 상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자자산(만원)", value=10000); inv_gr = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액(만원)", value=60000); debt_r = st.number_input("대출 금리(%)", value=3.9) / 100
    debt_term = st.number_input("상환 기간(년)", value=30)
    tax_base = st.number_input("공시지가비율(%)", value=60.0) / 100; tax_r = st.number_input("보유세율(%)", value=0.2) / 100

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        events_this_year = []

        # 1. 수입
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pension = (h_p_amt * 12 if h_age >= h_p_age else 0) + (w_p_amt * 12 if w_age >= w_p_age else 0)
        y_income = inc_h + inc_w + pension

        # 2. 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                events_this_year.append(f"🏠{tr['new_price']//10000}억 매수")

        # 3. 양육비
        k_cost = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: events_this_year.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_cost += kid['costs'][0]*12
            elif 8<=ka<=13: k_cost += kid['costs'][1]*12
            elif 14<=ka<=16: k_cost += kid['costs'][2]*12
            elif 17<=ka<=19: k_cost += kid['costs'][3]*12
            elif 20<=ka<=23: k_cost += kid['costs'][4]*12

        # 4. 비용 및 세금 (원리금 상환 포함)
        curr_living_annual = (living_2025 * 12) * ((1 + living_growth)**(year - 2025))
        tax = (c_re * tax_base) * tax_r
        interest = c_debt * debt_r
        # 원금 상환: 대출 잔액이 있을 때만 기간에 맞춰 상환한다고 가정
        principal_repayment = (debt_init / debt_term) if (c_debt > 0 and year < 2025 + debt_term) else 0
        loan_cost_annual = interest + principal_repayment
        
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        for ev in st.session_state.events:
            if year == ev['year']: events_this_year.append(f"🚀{ev['name']} ({ev['cost']//10000}억)")

        # 5. 자산 흐름 업데이트
        net_cf = y_income - (curr_living_annual + k_cost + tax + loan_cost_annual + ev_cost)
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_flow := net_cf) * (1 + inv_gr)
        c_debt = max(0, c_debt - principal_repayment)
        
        total_a = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "순자산": round((total_a - c_debt)/10000, 2), "부채": round(c_debt/10000, 2), "총자산": round(total_a/10000, 2),
            "부동산": round(c_re/10000, 2), "금융자산": round(c_inv/10000, 2), "연수입": round(y_income/10000, 2),
            "월생활비": round((curr_living_annual/12), 0), "월원리금": round((loan_cost_annual/12), 0),
            "월총비용": round((curr_living_annual + k_cost + tax + loan_cost_annual + ev_cost)/12, 0),
            "이벤트": ", ".join(events_this_year) if events_this_year else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 시각화 ---
tab1, tab2 = st.tabs(["📊 자산 성장 로드맵", "📋 상세 데이터"])

with tab1:
    p_choice = st.radio("조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4)
    p_len = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}[p_choice]
    sub_df = df.head(p_len)

    # [메인 그래프] 누적 막대 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["순자산"], name="순자산(억)", marker_color='#10b981', 
                         customdata=sub_df[["총자산", "나이", "월총비용", "이벤트"]],
                         hovertemplate="<b>%{x}년 (%{customdata[1]})</b><br>순자산: %{y}억<br>총자산: %{customdata[0]}억<br>월평균 지출: %{customdata[2]:,}만<br>이벤트: %{customdata[3]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채(억)", marker_color='#ef4444', 
                         customdata=sub_df[["총자산", "나이", "월총비용", "이벤트"]],
                         hovertemplate="부채: %{y}억<extra></extra>"))
    
    fig.update_layout(title=dict(text="우리 가족 자산 로드맵", font=dict(size=22)), barmode='stack', hovermode="x unified", height=550, 
                      template="plotly_white", hoverlabel=dict(bgcolor="white", font_size=16, font_family="Noto Sans KR"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # [4분할 상세 막대 그래프]
    st.markdown("### 🔍 항목별 세부 추이 (단위: 억원 / 만원)")
    c1, c2, c3, c4 = st.columns(4)
    def draw_bar(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color, customdata=data["이벤트"],
                             hovertemplate=f"값: %{{y}} {unit}<br>이벤트: %{{customdata}}<extra></extra>"))
        f.update_layout(title=dict(text=title, font=dict(size=16)), height=280, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white",
                        hoverlabel=dict(font_size=14))
        return f
    c1.plotly_chart(draw_bar(sub_df, "부동산", "🏠 부동산 가액", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub_df, "금융자산", "📈 금융자산", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub_df, "월총비용", "💸 월 평균 총비용", "#f43f5e", "만"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub_df, "연수입", "💵 연 수입", "#10b981"), use_container_width=True)

with tab2:
    st.subheader("📋 전체 시뮬레이션 상세 데이터 (단위: 억원 / 만원)")
    st.dataframe(df.style.format({
        "순자산": "{:.2f}억", "부채": "{:.2f}억", "총자산": "{:.2f}억", 
        "부동산": "{:.2f}억", "금융자산": "{:.2f}억", "연수입": "{:.2f}억",
        "월생활비": "{:,.0f}만", "월원리금": "{:,.0f}만", "월총비용": "{:,.0f}만"
    }), use_container_width=True)
