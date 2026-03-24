import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 프리미엄 디자인 UI/UX
st.set_page_config(page_title="우리 가족 자산 마스터 v16.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 20px !important; 
    }
    
    section[data-testid="stSidebar"] {
        background-color: #e0f2fe !important;
        border-right: 1px solid #bae6fd;
    }
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stHeader,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 25px !important; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #0ea5e9;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 22px !important; font-weight: 700; padding: 12px 30px;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700; background-color: #0ea5e9; color: white; height: 3.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 가족 통합 자산 프로젝션 v16.0")
st.markdown("---")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state: 
    st.session_state.re_trades = []
if 'events' not in st.session_state: 
    st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# --- 3. 사이드바: 설정 레버 ---
st.sidebar.title("🛠️ 재무 전략 설정")

# (1) 시작 연도
with st.sidebar.expander("📅 시나리오 시작 시점", expanded=True):
    start_yr = st.number_input("시작 연도", value=2026, min_value=2024, key="sys_start_yr")

# (2) 부부 소득 및 상여금
with st.sidebar.expander("👤 부부 소득 및 상여금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급(만)", value=830, key="h_s_in")
        h_bonus_r = st.number_input("남편 상여비율(%)", value=20.0, key="h_br_in") / 100
        h_inc = st.number_input("급여 인상률(%)", value=3.0, key="h_i_in") / 100
        h_ret_age = st.number_input("은퇴나이", value=55, key="h_ret_in")
        h_p_amt = st.number_input("월 예상연금", value=150, key="h_p_in")
    with w_tab:
        w_sal = st.number_input("아내 월급(만)", value=500, key="w_s_in")
        w_bonus_r = st.number_input("아내 상여비율(%)", value=20.0, key="w_br_in") / 100
        w_inc = st.number_input("급여 인상률(%)", value=3.0, key="w_inc_in") / 100
        w_ret_age = st.number_input("아내 은퇴나이", value=55, key="w_r_in")
        w_p_amt = st.number_input("아내 월 연금", value=130, key="w_p_in")

# (3) 생활비 레버
with st.sidebar.expander("💸 생활비 레버", expanded=False):
    living_monthly = st.number_input("월 고정 생활비(만)", value=450, key="liv_m_in")
    living_gr = st.number_input("생활비 인상률(%)", value=2.5, key="liv_g_in") / 100

# (4) 금융 투자 자산
with st.sidebar.expander("📈 금융 투자 자산 설정", expanded=False):
    inv_init = st.number_input("현재 투자 원금(만)", value=15000, key="inv_ini_in")
    inv_gr = st.number_input("기대 수익률(%)", value=7.0, key="inv_gr_in") / 100
    inv_ratio = st.slider("💰 흑자 시 투자 비중(%)", 0, 100, 90, key="inv_rat_in")

# (5) 대출 관리 (오더: 갈아타기 대출 동적 생성)
with st.sidebar.expander("💳 대출 및 상환 방식", expanded=False):
    st.markdown("**기존 대출 설정**")
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000, key="debt_ini_in")
    debt_r = st.number_input("기본 대출 금리(%)", value=4.0, key="debt_r_in") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="debt_t_in")
    debt_type = st.selectbox("상환 방식 선택", ["원리금균등", "원금균등"], key="debt_tp_in")
    
    # 부동산 갈아타기가 있을 경우 대출 탭에 조건 설정창 자동 생성
    if st.session_state.re_trades:
        st.markdown("---")
        st.markdown("**🔄 갈아타기 신규 대출 조건**")
        for i, tr in enumerate(st.session_state.re_trades):
            st.caption(f"📍 갈아타기 #{i+1} ({tr.get('year', start_yr+10)}년 실행)")
            c1, c2 = st.columns(2)
            tr['new_debt_r'] = c1.number_input(f"신규 금리(%) {i}", value=tr.get('new_debt_r', 4.0), key=f"nd_r_{i}") / 100
            tr['new_debt_term'] = c2.number_input(f"신규 기간(년) {i}", value=tr.get('new_debt_term', 30), key=f"nd_t_{i}")
            tr['new_debt_type'] = st.selectbox(f"신규 상환 방식 {i}", ["원리금균등", "원금균등"], index=0 if tr.get('new_debt_type', '원리금균등') == '원리금균등' else 1, key=f"nd_tp_{i}")

# (6) 부동산 갈아타기 계획
with st.sidebar.expander("🏠 부동산 갈아타기 계획", expanded=False):
    re_init_val = st.number_input("현재 집 가액(만)", value=150000, key="re_ini_in")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="re_gr_in") / 100
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": start_yr+10, "new_price": 300000, "use_inv": 0, "new_debt_amt": debt_init, "use_cash": 0})
    
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 계획 #{i+1}**")
        tr['year'] = st.number_input(f"매수 연도 {i}", start_yr, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"신규 주택 매수가(만) {i}", value=tr.get('new_price', 300000), step=10000, key=f"tr_np_{i}")
        
        est_sale = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_yr))) * 0.95
        acq_tax = tr['new_price'] * 0.033
        gap = tr['new_price'] + acq_tax - est_sale
        
        st.info(f"예상 매각대금(세후): {est_sale/10000:.2f}억\n\n필요 Gap: {gap/10000:.2f}억 (기존 대출상환 미반영)")
        st.caption("🔻 자금 조달 계획 (합산하여 남고 모자란 현금은 예금에 자동 정산)")
        
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융 매도(만){i}", value=tr.get('use_inv', 0), step=1000, key=f"tr_inv_{i}")
        tr['new_debt_amt'] = c2.number_input(f"신규 대출 총액{i}", value=tr.get('new_debt_amt', 60000), step=5000, key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input(f"보유 예금(만){i}", value=tr.get('use_cash', 0), step=1000, key=f"tr_cash_{i}")
        
        if st.button(f"🗑️ 계획 #{i+1} 삭제", key=f"re_del_{i}"): 
            st.session_state.re_trades.pop(i)
            st.rerun()

# (7) 자녀 및 특별 이벤트
with st.sidebar.expander("🍼 자녀 & 특별 이벤트", expanded=False):
    if st.button("➕ 자녀 추가"): 
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": start_yr+1, "costs": [100, 150, 200, 250, 300]})
    
    for i, kid in enumerate(st.session_state.kids):
        col1, col2 = st.columns([3, 1])
        col1.write(f"👶 **{kid['name']}**")
        if col2.button("삭제", key=f"k_del_{i}"):
            st.session_state.kids.pop(i)
            st.rerun()
            
        kid['birth'] = st.number_input(f"출생년 {i}", 2024, 2050, kid['birth'], key=f"kb_{i}")
        c1, c2 = st.columns(2)
        kid['costs'][0] = c1.number_input(f"영유아 {i}", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = c2.number_input(f"초등 {i}", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = c1.number_input(f"중등 {i}", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = c2.number_input(f"고등 {i}", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = c1.number_input(f"대학 {i}", value=kid['costs'][4], key=f"kc4_{i}")
    
    st.markdown("---")
    if st.button("➕ 이벤트 추가"): 
        st.session_state.events.append({"name": "이벤트", "year": start_yr+3, "cost": 6000})
    
    for i, ev in enumerate(st.session_state.events):
        col1, col2 = st.columns([3, 1])
        ev['name'] = col1.text_input(f"명칭 {i}", ev['name'], key=f"ev_n_{i}")
        if col2.button("삭제", key=f"ev_del_{i}"):
            st.session_state.events.pop(i)
            st.rerun()
            
        ev['year'] = st.number_input(f"년도 {i}", start_yr, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = st.number_input(f"비용 {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

# (8) 은퇴 배당 자산 배분
with st.sidebar.expander("👵 은퇴 배당 자산 배분", expanded=False):
    st.write("은퇴 시점 금융자산을 아래 비율로 나눕니다.")
    s_schd = st.slider("SCHD (배당성장) %", 0, 100, 25, key="ret_schd")
    s_jepq = st.slider("JEPQ (고배당) %", 0, 100, 25, key="ret_jepq")
    st.info(f"기존 금융자산 유지: {100 - s_schd - s_jepq}%")

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re = re_init_val
    c_re_base = re_init_val
    c_inv = inv_init
    c_cash = 1000  # 초기 예금 세팅
    c_debt = debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    # 동적 대출 조건 변수
    curr_debt_r = debt_r
    curr_debt_type = debt_type
    rem_debt_term = debt_term

    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list, pension = [], 0
        t_acq, t_gain = 0, 0
        
        # 1. 소득
        inc_h = (c_h_sal * 12 * (1+h_bonus_r)) if h_age <= h_ret_age else 0
        inc_w = (c_w_sal * 12 * (1+w_bonus_r)) if w_age <= w_ret_age else 0
        if h_age >= 65: pension += (h_p_amt * 12)
        if w_age >= 65: pension += (w_p_amt * 12)
        total_income_y = inc_h + inc_w + pension
        
        # 2. 갈아타기 (대출 완전 갱신 및 현실적 자금 흐름 반영)
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                t_gain = max(0, c_re - c_re_base) * 0.20
                t_acq = tr['new_price'] * 0.033
                
                # 매수 필요 자금 (순수 집값 차액)
                est_sale_actual = c_re * 0.95
                cash_needed = tr['new_price'] - est_sale_actual
                
                # 조달 자금 반영
                new_debt = tr.get('new_debt_amt', c_debt) 
                debt_cash_flow = new_debt - c_debt  # 대출 증가분은 플러스 현금
                
                c_inv -= tr['use_inv']
                c_cash -= tr['use_cash']
                
                # 매수 후 남거나 모자란 자금은 예금(c_cash)에 반영
                c_cash += (tr['use_inv'] + tr['use_cash'] + debt_cash_flow - cash_needed)
                
                # 자산 상태 업데이트
                c_debt = new_debt
                c_re = tr['new_price']
                c_re_base = tr['new_price']
                
                # 신규 대출 조건으로 엎어치기
                curr_debt_r = tr.get('new_debt_r', curr_debt_r)
                curr_debt_type = tr.get('new_debt_type', curr_debt_type)
                rem_debt_term = tr.get('new_debt_term', debt_term)
                
                ev_list.append("🏠갈아타기")

        # 3. 세금 및 양육비
        t_hold = (c_re * 0.6) * 0.002
        t_comp = max(0, (c_re - 120000) * 0.005)
        total_tax_y = (total_income_y * 0.15) + t_hold + t_comp + t_gain + t_acq
        
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if 0<=ka<=7: k_total += kid['costs'][0]*12
            elif 8<=ka<=13: k_total += kid['costs'][1]*12
            elif 14<=ka<=16: k_total += kid['costs'][2]*12
            elif 17<=ka<=19: k_total += kid['costs'][3]*12
            elif 20<=ka<=23: k_total += kid['costs'][4]*12
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")

        # 4. 부채 상환 (동적 이율, 기간 적용)
        interest_a = c_debt * curr_debt_r
        principal_a, repay_a = 0, 0
        
        if c_debt > 0 and rem_debt_term > 0:
            if curr_debt_type == "원리금균등":
                pmt = (c_debt * curr_debt_r * (1+curr_debt_r)**rem_debt_term) / ((1+curr_debt_r)**rem_debt_term - 1) if curr_debt_r > 0 else (c_debt / rem_debt_term)
                principal_a = pmt - interest_a
                repay_a = pmt
            else:
                principal_a = c_debt / rem_debt_term
                repay_a = principal_a + interest_a
            rem_debt_term -= 1
        elif c_debt > 0:
            repay_a = interest_a
        
        # 5. 지출 및 자산배분
        curr_living_y = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        total_exp_y = curr_living_y + k_total + total_tax_y + repay_a + ev_cost
        net_flow_y = total_income_y - total_exp_y
        
        if net_flow_y >= 0:
            c_inv += net_flow_y * (inv_ratio / 100)
            c_cash += net_flow_y * (1 - inv_ratio/100)
        else:
            c_inv += net_flow_y 
            if c_inv < 0:
                c_cash += c_inv
                c_inv = 0
                if c_cash < 0:
                    c_debt -= c_cash
                    c_cash = 0
            
        c_re *= (1 + re_gr_rate)
        c_inv *= (1 + inv_gr)
        c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "연도": year, "순자산_억": round((c_re + c_inv + c_cash - c_debt)/10000, 2),
            "총자산_억": round((c_re + c_inv + c_cash)/10000, 2),
            "부동산_억": round(c_re/10000, 2), "금융자산_억": round(c_inv/10000, 2), 
            "예금_억": round(c_cash/10000, 2), "대출_억": round(c_debt/10000, 2),
            "월_순현금_만": round(net_flow_y/12, 0), "월_지출_만": round(total_exp_y/12, 0),
            "월_세금_만": round(total_tax_y/12, 0), "양도세_만": round(t_gain, 0), "취득세_만": round(t_acq, 0),
            "이벤트": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc)
        c_w_sal *= (1 + w_inc)
        
    return pd.DataFrame(res)

df_res = run_simulation()

# --- 5. 대시보드 출력 ---
m_tab, t_tab, s_tab, d_tab = st.tabs(["📊 자산 성장 로드맵", "⚖️ 상세 세무 분석", "👵 은퇴 & 배당 시뮬레이션", "📋 데이터 상세"])

with m_tab:
    period = st.radio("🔍 조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4, key="p_sel")
    sub = df_res.head({"5년":5, "10년":10, "20년":20, "30년":30, "전체":len(df_res)}[period])

    # 메인 차트: 호버 오더 (연도 -> 총자산 -> 순자산 -> 부채)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산", marker_color='#10b981',
                         customdata=sub[["총자산_억", "대출_억"]],
                         hovertemplate="<b>%{x}년</b><br>총자산: %{customdata[0]:.2f}억<br>순자산: %{y:.2f}억<br>부채: %{customdata[1]:.2f}억<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="부채", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=18),
                      hoverlabel=dict(bgcolor="white", font_size=20, font_family="Noto Sans KR"))
    st.plotly_chart(fig, use_container_width=True)

    # 서브 차트
    st.markdown("#### 🔍 세부 지표")
    def draw_mini(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color, hovertemplate="<b>%{x}년</b><br>금액: %{y:.2f}억<extra></extra>"))
        f.update_layout(title=dict(text=title, font=dict(size=22)), height=340, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    
    c1, c2 = st.columns(2)
    c1.plotly_chart(draw_mini(sub, "부동산_억", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "금융자산_억", "📈 금융투자(억)", "#8b5cf6"), use_container_width=True)
    
    c3, c4 = st.columns(2)
    c3.plotly_chart(draw_mini(sub, "예금_억", "💰 예금(억)", "#0ea5e9"), use_container_width=True)
    
    f_exp = go.Figure(go.Bar(x=sub["연도"], y=sub["월_지출_만"], marker_color="#f43f5e", hovertemplate="<b>%{x}년</b><br>금액: %{y:,.0f}만<extra></extra>"))
    f_exp.update_layout(title=dict(text="💸 월 지출(만)", font=dict(size=22)), height=340, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
    c4.plotly_chart(f_exp, use_container_width=True)

with t_tab:
    st.header("⚖️ 상세 세무 분석")
    t_disp = sub[["연도", "월_세금_만", "양도세_만", "취득세_만"]].copy()
    t_disp.columns = ["연도", "월세금(만)", "양도세", "취득세"]
    st.dataframe(t_disp.style.format({c: "{:,.0f}" for c in t_disp.columns if "연도" not in c}), use_container_width=True, height=600)

with s_tab:
    st.header("👵 은퇴 배당 시뮬레이션")
    f_ret_yr = start_yr + max((h_ret_age - (start_yr-1995)), (w_ret_age - (start_yr-1994)))
    ret_row = df_res[df_res["연도"] == f_ret_yr].iloc[0]
    div_data = []
    c_inv_val = ret_row["금융자산_억"]
    for y in range(f_ret_yr, 2096):
        schd_p = c_inv_val * (s_schd/100)
        jepq_p = c_inv_val * (s_jepq/100)
        m_div = ((schd_p * 0.035 * (1.05**(y-f_ret_yr))) + (jepq_p * 0.095)) * 10000 / 12
        div_data.append({"연도": y, "월_배당금": m_div})
        c_inv_val *= (1 + inv_gr)
        
    df_div = pd.DataFrame(div_data)
    fig_div = go.Figure()
    fig_div.add_trace(go.Scatter(x=df_div["연도"], y=df_div["월_배당금"], fill='tozeroy', name="월 배당(만)", hovertemplate="<b>%{x}년</b><br>배당: %{y:,.0f}만<extra></extra>"))
    fig_div.update_layout(title="은퇴 후 월 배당 성장 추이", height=500, template="plotly_white")
    st.plotly_chart(fig_div, use_container_width=True)
    st.metric("은퇴 시 금융자산", f"{ret_row['금융자산_억']:.2f}억")

with d_tab:
    st.subheader("📋 전체 상세 데이터")
    st.dataframe(df_res.style.format({c: "{:.2f}" if "_억" in c else "{:,.0f}" for c in df_res.columns if "연도" not in c and "이벤트" not in c}), use_container_width=True)
