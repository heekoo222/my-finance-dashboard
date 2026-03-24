import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인 (가독성 극대화)
st.set_page_config(page_title="Family Financial Master v3.0", layout="wide")
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
st.info("💡 모든 입력(좌측)은 **'만원'** 단위이며, 결과 리포트는 **'억원'** 및 **'만원'**으로 구분 표시됩니다.")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 탭 기반 기타 가정사항 설정 ---
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

# 요청 사항 1: 금융투자 & 대출 별개 탭 세팅
with st.sidebar.expander("📈 금융투자 & 자산 배분", expanded=False):
    inv_init = st.number_input("현재 금융투자금(만)", value=10000)
    inv_gr = st.number_input("연간 기대 수익률(%)", value=7.0) / 100
    st.markdown("---")
    st.write("💰 **잉여 자금 배분 비율**")
    inv_ratio = st.slider("금융자산 배분율(%)", 0, 100, 90)
    cash_ratio = 100 - inv_ratio
    st.caption(f"나머지 {cash_ratio}%는 예금으로 적립됩니다.")

with st.sidebar.expander("💳 대출 상세 설정", expanded=False):
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000)
    debt_r = st.number_input("대출 이자율(%)", value=3.9) / 100
    debt_term = st.number_input("상환 기간(년)", value=30)
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"])

with st.sidebar.expander("🏠 부동산 & 양육비 & 이벤트", expanded=False):
    re_init_val = st.number_input("현재 부동산(만)", value=140000)
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0) / 100
    living_monthly = st.number_input("현재 월 생활비(만)", value=400)
    living_gr = st.number_input("생활비 인상률(%)", value=2.0) / 100
    if st.button("➕ 부동산 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    if st.button("➕ 특별 이벤트 추가"):
        st.session_state.events.append({"name": "이벤트", "year": 2030, "cost": 0})

# --- 4. 시뮬레이션 엔진 (세금 로직 포함) ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_year, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        
        # 1. 수입 (급여 및 연금)
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pension = (h_p_amt * 12 if h_age >= 65 else 0) + (w_p_amt * 12 if w_age >= 65 else 0)
        total_income_gross = inc_h + inc_w + pension
        
        # 2. 세금 계산 (Simplified Professional Logic)
        tax_income = total_income_gross * 0.15 # 근로소득세+지방세 (평균 15% 가정)
        tax_holding = (c_re * 0.6) * 0.002     # 보유세 (공시지가 60% * 세율 0.2%)
        tax_comprehensive = 0                 # 종부세 (초과분 가정)
        if c_re > 120000: tax_comprehensive = (c_re - 120000) * 0.005
        
        tax_financial = 0                     # 금융소득세 (수익의 15.4%)
        if (c_inv * inv_gr) > 2000: tax_financial = (c_inv * inv_gr) * 0.154
        
        tax_acq = 0; tax_gains = 0            # 취득세, 양도세
        
        # 3. 부동산 갈아타기 처리
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                # 양도세 계산 (수익의 20% 가정)
                profit = (c_re - re_init_val) if c_re > re_init_val else 0
                tax_gains = profit * 0.2
                # 취득세 계산 (매수가의 3.3%)
                tax_acq = tr['new_price'] * 0.033
                # 자금 흐름 반영
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 이동")

        # 4. 대출 상환 로직 (방식별)
        if c_debt > 0 and year < start_year + debt_term:
            interest_annual = c_debt * debt_r
            if debt_type == "원리금균등":
                # PMT 공식: [P*r*(1+r)^n] / [(1+r)^n - 1]
                r = debt_r
                n = debt_term
                repay_total = (debt_init * r * (1+r)**n) / ((1+r)**n - 1)
                principal_repay = repay_total - interest_annual
            else: # 원금균등
                principal_repay = debt_init / debt_term
                repay_total = principal_repay + interest_annual
        else:
            interest_annual = 0; principal_repay = 0; repay_total = 0

        # 5. 기타 지출
        k_cost = 0 # 자녀 양육비 (생략 로직 유지)
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_year))
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        
        # 총 세금 합계
        total_tax_annual = tax_income + tax_holding + tax_comprehensive + tax_financial + tax_acq + tax_gains
        
        # 6. 순현금흐름 및 자산 배분 (요청 사항)
        total_expense = curr_living + k_cost + total_tax_annual + repay_total + ev_cost
        net_flow = total_income_gross - total_expense
        
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
            "total_asset": (c_re + c_inv + c_cash)/10000,
            "re": c_re/10000, "inv": c_inv/10000, "debt": c_debt/10000,
            "income": total_income_gross/10000,
            "m_spend": total_expense/12,
            "m_net": net_flow/12,
            "tax_inc": tax_income, "tax_hold": tax_holding + tax_comprehensive,
            "tax_fin": tax_financial, "tax_trade": tax_acq + tax_gains,
            "event": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 대시보드 출력 ---
main_tab, tax_tab, data_tab = st.tabs(["📊 자산 로드맵", "⚖️ 상세 세금 대시보드", "📋 데이터 시트"])

with main_tab:
    # 조회 기간 필터
    p_choice = st.radio("시뮬레이션 기간", ["10년", "20년", "30년", "전체"], horizontal=True, index=3)
    p_len = {"10년":10, "20년":20, "30년":30, "전체":len(df)}[p_choice]
    sub = df.head(p_len)

    # 누적 막대 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net_asset"], name="순자산(억)", marker_color='#10b981', 
                         hovertemplate="연도: %{x}<br>순자산: %{y:.2f}억<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt"], name="부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=550, template="plotly_white",
                      font=dict(size=16), legend=dict(orientation="h", y=1.1, x=1))
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 지표
    c1, c2, c3, c4 = st.columns(4)
    def draw_mini(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color))
        f.update_layout(title=title, height=280, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_mini(sub, "re", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "inv", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_mini(sub, "m_spend", "💸 월 지출액(만)", "#f43f5e", "만"), use_container_width=True)
    c4.plotly_chart(draw_mini(sub, "m_net", "💰 월 순현금흐름(만)", "#10b981", "만"), use_container_width=True)

with tax_tab:
    st.header("⚖️ 연도별 상세 세금 분석")
    st.markdown("가계에서 지불하는 모든 세금 항목을 연도별로 분석합니다.")
    
    # 세금 추이 그래프
    fig_tax = go.Figure()
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["tax_inc"], name="소득세", stackgroup='one'))
    fig_tax.add_trace(go.Scatter(x=sub["year"], y=sub["tax_hold"], name="보유세(종부세 포함)", stackgroup='one'))
    fig_tax.add_trace(go.Scatter(x=sub_with_trade := sub[sub['tax_trade'] > 0]["year"], 
                                 y=sub[sub['tax_trade'] > 0]["tax_trade"], name="거래세(양도/취득)", mode='markers', marker=dict(size=12)))
    fig_tax.update_layout(title="연도별 세금 지출 비중 (단위: 만원)", height=500, template="plotly_white", font=dict(size=16))
    st.plotly_chart(fig_tax, use_container_width=True)
    
    # 세금 상세 표
    tax_display = sub[["year", "age", "tax_inc", "tax_hold", "tax_fin", "tax_trade"]].copy()
    tax_display.columns = ["연도", "나이", "소득세(만)", "보유/종부세(만)", "금융소득세(만)", "거래세(취득/양도)(만)"]
    st.dataframe(tax_display.style.format("{:.0f}"), use_container_width=True)

with data_tab:
    st.subheader("📋 전체 시뮬레이션 상세 시트")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
