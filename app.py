import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 프리미엄 디자인
st.set_page_config(page_title="Family Wealth Master v7.1", layout="wide")

# 가독성을 위한 CSS (폰트 확대 및 디자인 강화)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 20px !important; 
    }
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 700; background-color: #2563eb; color: white; height: 3.5rem; font-size: 22px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset & Tax Master")
st.markdown("남편(95) & 아내(94)를 위한 **최종 통합 자산 관리 시스템**")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = []
if 'events' not in st.session_state:
    st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]

# --- 3. 사이드바 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 환경 설정")

# (1) 기본 정보 및 시작연도
with st.sidebar.expander("📅 기본 정보 & 시작연도", expanded=True):
    start_yr = st.number_input("시작 연도", value=2026, min_value=2024, key="sys_start_yr")
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급(만)", value=830, key="h_sal_in")
        h_inc = st.number_input("남편 인상률(%)", value=3.0, key="h_inc_in") / 100
        h_ret = st.number_input("은퇴나이", value=55, key="h_ret_in")
        h_p_amt = st.number_input("예상연금(월/만)", value=150, key="h_pamt_in")
    with w_tab:
        w_sal = st.number_input("아내 월급(만)", value=500, key="w_sal_in")
        w_inc = st.number_input("아내 인상률(%)", value=3.0, key="w_inc_in") / 100
        w_ret = st.number_input("아내 은퇴나이", value=55, key="w_ret_in")
        w_p_amt = st.number_input("예상연금(월/만)", value=130, key="w_pamt_in")

# (2) 금융투자 & 자산 배분
with st.sidebar.expander("📈 금융투자 & 자산 배분", expanded=False):
    inv_init = st.number_input("현재 금융투자금(만)", value=10000, key="sys_inv_init")
    inv_gr = st.number_input("연간 기대 수익률(%)", value=7.0, key="sys_inv_gr") / 100
    st.markdown("---")
    st.write("💰 **순현금흐름 배분 비율**")
    inv_ratio = st.slider("금융자산 배분율(%)", 0, 100, 90, key="sys_inv_ratio")
    cash_ratio = 100 - inv_ratio

# (3) 대출 상세 설정
with st.sidebar.expander("💳 대출 상세 설정", expanded=False):
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000, key="sys_debt_init")
    debt_r = st.number_input("대출 이자율(%)", value=3.9, key="sys_debt_r") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="sys_debt_term")
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"], key="sys_debt_type")

# (4) [복구] 부동산 갈아타기 (Gap 조달 로직)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    re_init_val = st.number_input("현재 부동산 가액(만)", value=140000, key="sys_re_val")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="sys_re_gr") / 100
    st.markdown("---")
    if st.button("➕ 갈아타기 추가", key="btn_add_re"):
        st.session_state.re_trades.append({"year": start_yr+5, "new_price": 250000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**🏠 갈아타기 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", start_yr, 2090, tr['year'], key=f"tr_yr_{i}")
        # 매각가 추정 (세후 95% 가정)
        est_sale = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_yr))) * 0.95
        st.write(f"👉 예상 매각 대금(세후): **{est_sale/10000:.2f} 억원**")
        tr['new_price'] = st.number_input(f"새 아파트 매수가(만) {i}", 0, 1000000, tr['new_price'], key=f"tr_pr_{i}")
        gap = tr['new_price'] - est_sale
        st.warning(f"⚠️ 추가 조달 필요액: **{gap/10000:.2f} 억원**")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융(만) {i}", value=tr['use_inv'], key=f"tr_inv_{i}")
        tr['use_debt'] = c2.number_input(f"대출(만) {i}", value=tr['use_debt'], key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input(f"예금(만) {i}", value=tr['use_cash'], key=f"tr_cash_{i}")
        if st.button(f"🗑️ #{i+1} 삭제", key=f"btn_del_re_{i}"):
            st.session_state.re_trades.pop(i); st.rerun()

# (5) [복구] 자녀별 시기별 양육비 상세
with st.sidebar.expander("🍼 자녀별 양육비 상세", expanded=False):
    living_monthly = st.number_input("월 생활비(만)", value=400, key="sys_living")
    living_gr = st.number_input("생활비 인상률(%)", value=2.0, key="sys_living_gr") / 100
    st.markdown("---")
    if st.button("➕ 자녀 추가", key="btn_add_kid"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    
    for i, kid in enumerate(st.session_state.kids):
        st.write(f"👶 **{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"출생년도 {i}", 2024, 2050, kid['birth'], key=f"kb_{i}")
        c1, c2 = st.columns(2)
        kid['costs'][0] = c1.number_input(f"영유아(0-7) {i}", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = c2.number_input(f"초등(8-13) {i}", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = c1.number_input(f"중등(14-16) {i}", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = c2.number_input(f"고등(17-19) {i}", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = c1.number_input(f"대학(20-23) {i}", value=kid['costs'][4], key=f"kc4_{i}")
        if st.button(f"🗑️ {kid['name']} 삭제", key=f"btn_del_kid_{i}"):
            st.session_state.kids.pop(i); st.rerun()

# (6) 특별 이벤트
with st.sidebar.expander("🚀 특별 이벤트 설정", expanded=False):
    if st.button("➕ 이벤트 추가", key="btn_add_ev"):
        st.session_state.events.append({"name": "새 이벤트", "year": start_yr+2, "cost": 5000})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"이벤트명 {i}", ev['name'], key=f"ev_nm_{i}")
        cy, cc = st.columns(2)
        ev['year'] = cy.number_input(f"연도 {i}", start_yr, 2095, ev['year'], key=f"ev_yr_{i}")
        ev['cost'] = cc.number_input(f"비용(만) {i}", 0, 1000000, ev['cost'], key=f"ev_cs_{i}")
        if st.button(f"🗑️ 이벤트 #{i+1} 삭제", key=f"btn_del_ev_{i}"):
            st.session_state.events.pop(i); st.rerun()

# --- 4. 시뮬레이션 엔진 (모든 로직 통합) ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        pension = 0
        
        # 1. 수입
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        if h_age >= 65: pension += (h_p_amt * 12)
        if w_age >= 65: pension += (w_p_amt * 12)
        total_income_gross = inc_h + inc_w + pension
        
        # 2. 세목별 세금 초기화
        t_inc, t_hold, t_comp, t_fin, t_acq, t_gain = 0, 0, 0, 0, 0, 0
        t_inc = total_income_gross * 0.15 
        t_hold = (c_re * 0.6) * 0.0015
        t_comp = max(0, (c_re - 120000) * 0.005)
        t_fin = max(0, (c_inv * inv_gr - 2000) * 0.154)
        
        # 3. 부동산 갈아타기 (양도세 vs 취득세 구분)
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                t_gain = max(0, c_re - re_init_val) * 0.20 # 양도세
                t_acq = tr['new_price'] * 0.033           # 취득세
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 이동")

        # 4. 양육비 계산 (단계별)
        k_cost_annual = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_cost_annual += kid['costs'][0]*12
            elif 8<=ka<=13: k_cost_annual += kid['costs'][1]*12
            elif 14<=ka<=16: k_cost_annual += kid['costs'][2]*12
            elif 17<=ka<=19: k_cost_annual += kid['costs'][3]*12
            elif 20<=ka<=23: k_cost_annual += kid['costs'][4]*12

        # 5. 대출 상환
        interest_a = c_debt * debt_r
        if c_debt > 0 and (year < start_yr + debt_term):
            if debt_type == "원리금균등":
                repay_a = (debt_init * debt_r * (1+debt_r)**debt_term) / ((1+debt_r)**debt_term - 1)
                principal_a = repay_a - interest_a
            else:
                principal_a = debt_init / debt_term; repay_a = principal_a + interest_a
        else:
            principal_a, repay_a = 0, 0

        # 6. 최종 지출 및 자산 배분
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        for ev in st.session_state.events:
            if year == ev['year']: ev_list.append(f"🚀{ev['name']}")
        
        total_tax = t_inc + t_hold + t_comp + t_fin + t_acq + t_gain
        total_exp = curr_living + k_cost_annual + total_tax + repay_a + ev_cost
        net_flow = total_income_gross - total_exp
        
        if net_flow > 0:
            c_inv += net_flow * (inv_ratio / 100); c_cash += net_flow * (cash_ratio / 100)
        else:
            c_cash += net_flow
            
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "year": year, "age": f"{h_age}/{w_age}",
            "net_asset": (c_re + c_inv + c_cash - c_debt)/10000,
            "re": c_re/10000, "inv": c_inv/10000, "debt": c_debt/10000,
            "m_spend": total_exp/12, "m_net": net_flow/12,
            "t_total": total_tax, "t_inc": t_inc, "t_hold": t_hold + t_comp, "t_fin": t_fin, 
            "t_acq": t_acq, "t_gain": t_gain,
            "event": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 대시보드 출력 ---
m_tab, t_tab, d_tab = st.tabs(["📊 자산 로드맵", "⚖️ 상세 세금 분석", "📋 데이터 시트"])

with m_tab:
    p_choice = st.radio("시뮬레이션 조회 기간", ["10년", "20년", "30년", "전체"], horizontal=True, index=3, key="main_p")
    sub = df.head({"10년":10, "20년":20, "30년":30, "전체":len(df)}[p_choice])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net_asset"], name="순자산(억)", marker_color='#10b981',
                         customdata=sub[["age", "m_net", "event"]],
                         hovertemplate="<span style='font-size:24px'><b>%{x}년 (%{customdata[0]})</b></span><br>" + 
                                       "순자산: <span style='color:#10b981; font-size:22px'><b>%{y:.2f}억</b></span><br>" + 
                                       "월 순현금: <span style='color:#3b82f6'><b>%{customdata[1]:,.0f}만</b></span><br>" + 
                                       "이벤트: %{customdata[2]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt"], name="부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=18))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    def draw_mini(data, col, title, color):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color))
        f.update_layout(title=title, height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_mini(sub, "re", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "inv", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_mini(sub, "m_spend", "💸 월 지출(만)", "#f43f5e"), use_container_width=True)
    c4.plotly_chart(draw_mini(sub, "m_net", "💰 월 순현금(만)", "#10b981"), use_container_width=True)

with t_tab:
    st.header("⚖️ 연도별 상세 세금 리포트")
    tax_df = sub[["year", "age", "t_inc", "t_hold", "t_fin", "t_acq", "t_gain", "t_total"]].copy()
    tax_df.columns = ["연도", "나이", "소득세", "보유세", "금융세", "취득세", "양도세", "합계"]
    num_cols = ["소득세", "보유세", "금융세", "취득세", "양도세", "합계"]
    st.dataframe(tax_df.style.format({c: "{:,.0f}" for c in num_cols}), use_container_width=True)

with d_tab:
    st.subheader("📋 전체 데이터 상세")
    num_cols_all = ["net_asset", "re", "inv", "debt", "m_spend", "m_net"]
    st.dataframe(df.style.format({c: "{:.2f}" for c in num_cols_all}), use_container_width=True)
