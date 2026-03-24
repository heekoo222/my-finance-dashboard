import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인 고도화
st.set_page_config(page_title="Family Wealth Master v13.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 20px !important; }
    .main { background-color: #f8fafc; }
    
    /* 사이드바: 연한 하늘색 바탕 + 검정 글씨 */
    section[data-testid="stSidebar"] { background-color: #e0f2fe !important; border-right: 1px solid #bae6fd; }
    section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stHeader { color: #000000 !important; font-weight: 700 !important; }
    
    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; padding: 12px 30px; }
    
    /* 메트릭 카드 */
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 25px !important; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #0ea5e9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Master Plan v13.0")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# --- 3. 사이드바: 설정 레버 ---
st.sidebar.title("🛠️ 재무 전략 설정")

with st.sidebar.expander("📅 시나리오 시작 시점", expanded=True):
    start_yr = st.number_input("시작 연도", value=2026, min_value=2024, key="sys_start_yr")

with st.sidebar.expander("👤 부부 소득 및 상여금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("월급(만)", value=830, key="h_s_in")
        h_bonus_r = st.number_input("상여비율(%)", value=20.0, key="h_br_in") / 100
        h_inc = st.number_input("인상률(%)", value=3.0, key="h_inc_in") / 100
        h_ret_age = st.number_input("은퇴나이", value=55, key="h_ret_in")
        h_p_amt = st.number_input("월 예상연금", value=150, key="h_p_in")
    with w_tab:
        w_sal = st.number_input("아내 월급(만)", value=500, key="w_s_in")
        w_bonus_r = st.number_input("상여비율(%)", value=20.0, key="w_br_in") / 100
        w_inc = st.number_input("인상률(%)", value=3.0, key="w_inc_in") / 100
        w_ret_age = st.number_input("은퇴나이", value=55, key="w_ret_in")
        w_p_amt = st.number_input("월 연금액", value=130, key="w_p_in")

with st.sidebar.expander("💸 생활비 설정", expanded=False):
    living_monthly = st.number_input("월 생활비(만)", value=450, key="liv_m_in")
    living_gr = st.number_input("물가상승률(%)", value=2.5, key="liv_g_in") / 100

with st.sidebar.expander("📈 자산 배분 및 대출", expanded=False):
    inv_init = st.number_input("투자 원금(만)", value=15000, key="inv_ini_in")
    inv_gr = st.number_input("수익률(%)", value=7.0, key="inv_gr_in") / 100
    inv_ratio = st.slider("흑자 시 투자비중(%)", 0, 100, 90, key="inv_rat_in")
    st.markdown("---")
    debt_init = st.number_input("대출 잔액(만)", value=60000, key="debt_ini_in")
    debt_r = st.number_input("대출 금리(%)", value=4.0, key="debt_r_in") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="debt_t_in")
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"], key="debt_tp_in")

with st.sidebar.expander("🏠 부동산 갈아타기 계획", expanded=False):
    re_init_val = st.number_input("현재 주택가액(만)", value=150000, key="re_ini_in")
    re_gr_rate = st.number_input("상승률(%)", value=4.0, key="re_gr_in") / 100
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": start_yr+10, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 계획 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", start_yr, 2090, tr['year'], key=f"tr_y_{i}")
        est_sale_after_tax = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_yr))) * 0.95
        acq_tax = tr['new_price'] * 0.033
        gap_total = tr['new_price'] + acq_tax - est_sale_after_tax
        st.info(f"매각대금(세후): {est_sale_after_tax/10000:.2f}억\n\nGap(세금포함): {gap_total/10000:.2f}억")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융{i}", value=tr['use_inv'], key=f"tr_inv_{i}")
        tr['use_debt'] = c2.number_input(f"대출{i}", value=tr['use_debt'], key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input(f"예금{i}", value=tr['use_cash'], key=f"tr_cash_{i}")
        if st.button(f"🗑️ 계획 #{i+1} 삭제", key=f"re_del_{i}"): st.session_state.re_trades.pop(i); st.rerun()

with st.sidebar.expander("🍼 자녀 및 이벤트", expanded=False):
    if st.button("➕ 자녀 추가"): st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": start_yr+1, "costs": [100, 150, 200, 250, 300]})
    for i, kid in enumerate(st.session_state.kids):
        st.write(f"👶 **{kid['name']}**")
        kid['birth'] = st.number_input(f"출생년 {i}", 2024, 2050, kid['birth'], key=f"kb_{i}")
        c1, c2 = st.columns(2)
        kid['costs'][0] = c1.number_input(f"영유아 {i}", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = c2.number_input(f"초등 {i}", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = c1.number_input(f"중등 {i}", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = c2.number_input(f"고등 {i}", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = c1.number_input(f"대학 {i}", value=kid['costs'][4], key=f"kc4_{i}")
    st.markdown("---")
    if st.button("➕ 이벤트 추가"): st.session_state.events.append({"name": "이벤트", "year": start_yr+3, "cost": 6000})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"명칭 {i}", ev['name'], key=f"ev_n_{i}")
        ev['year'] = st.number_input(f"년도 {i}", start_yr, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = st.number_input(f"비용 {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
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
        
        # 2. 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                t_gain = max(0, c_re - re_init_val) * 0.20
                t_acq = tr['new_price'] * 0.033
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append("🏠갈아타기")

        # 3. 세금/지출/원리금
        t_hold = (c_re * 0.6) * 0.002
        t_comp = max(0, (c_re - 120000) * 0.005)
        total_tax_y = (total_income_y * 0.15) + t_hold + t_comp + t_gain + t_acq
        
        curr_living_y = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if 0<=ka<=7: k_total += kid['costs'][0]*12
            elif 8<=ka<=13: k_total += kid['costs'][1]*12
            elif 14<=ka<=16: k_total += kid['costs'][2]*12
            elif 17<=ka<=19: k_total += kid['costs'][3]*12
            elif 20<=ka<=23: k_total += kid['costs'][4]*12
            if year == kid['birth']: ev_list.append("👶탄생")

        interest_a = c_debt * debt_r
        if c_debt > 0 and (year < start_yr + debt_term):
            if debt_type == "원리금균등":
                repay_a = (debt_init * debt_r * (1+debt_r)**debt_term) / ((1+debt_r)**debt_term - 1)
                principal_a = repay_a - interest_a
            else:
                principal_a = debt_init / debt_term; repay_a = principal_a + interest_a
        else: principal_a, repay_a = 0, 0
        
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        for ev in st.session_state.events:
            if year == ev['year']: ev_list.append(f"🚀{ev['name']}")

        # 4. 현금흐름 및 자산배분
        total_exp_y = curr_living_y + k_total + total_tax_y + repay_a + ev_cost
        net_flow_y = total_income_y - total_exp_y
        
        if net_flow_y >= 0:
            c_inv += net_flow_y * (inv_ratio / 100); c_cash += net_flow_y * (1 - inv_ratio/100)
        else:
            c_inv += net_flow_y # 적자 시 금융자산 차감
            
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "연도": year, "남편나이": h_age, "아내나이": w_age,
            "순자산_억": round((c_re + c_inv + c_cash - c_debt)/10000, 2),
            "총자산_억": round((c_re + c_inv + c_cash)/10000, 2),
            "부동산_억": round(c_re/10000, 2), "금융자산_억": round(c_inv/10000, 2), "예금_억": round(c_cash/10000, 2), "대출_억": round(c_debt/10000, 2),
            "월_지출_만": round(total_exp_y/12, 0), "월_순현금_만": round(net_flow_y/12, 0),
            "월_세금_만": round(total_tax_y/12, 0), "연_세금_만": round(total_tax_y, 0),
            "양도세_만": round(t_gain, 0), "취득세_만": round(t_acq, 0), "보유세_만": round(t_hold+t_comp, 0), "소득세_만": round(total_income_y*0.15, 0),
            "이벤트": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df_res = run_simulation()

# --- 5. 화면 출력 ---
m_tab, t_tab, s_tab, d_tab = st.tabs(["📊 자산 성장 로드맵", "⚖️ 상세 세무 분석", "👵 은퇴 & 배당 시뮬레이션", "📋 데이터 상세"])

with m_tab:
    period = st.radio("🔍 조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4)
    sub = df_res.head({"5년":5, "10년":10, "20년":20, "30년":30, "전체":len(df_res)}[period])

    # 메인 차트: 프리미엄 호버 툴팁 적용
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산", marker_color='#10b981',
                         customdata=sub[["남편나이", "아내나이", "대출_억", "월_지출_만", "월_순현금_만", "이벤트"]],
                         hovertemplate=(
                             "<span style='font-size:26px;'><b>[%{x}년 (남편:%{customdata[0]} / 아내:%{customdata[1]})]</b></span><br>"
                             "<hr>"
                             "<span style='font-size:22px; color:#10b981;'>■ <b>순자산: %{y:.2f}억</b></span><br>"
                             "<span style='font-size:22px; color:#ef4444;'>■ <b>부채: %{customdata[2]:.2f}억</b></span><br>"
                             "<span style='font-size:18px;'>• 월 평균 지출: <span style='color:#ef4444'>%{customdata[3]:,.0f}만</span></span><br>"
                             "<span style='font-size:18px;'>• 월 평균 순현금: <span style='color:#3b82f6'>%{customdata[4]:,.0f}만</span></span><br>"
                             "<span style='font-size:18px; color:#f59e0b;'>• 이벤트: <b>%{customdata[5]}</b></span>"
                             "<extra></extra>"
                         )))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="부채", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=18),
                      hoverlabel=dict(bgcolor="#1e293b", font_size=18, font_color="white", font_family="Noto Sans KR"))
    st.plotly_chart(fig, use_container_width=True)

    # 1/2 서브 차트
    st.markdown("#### 🔍 항목별 세부 지표 (1/2 크기)")
    def draw_mini(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=22)), height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    c1, c2 = st.columns(2); c1.plotly_chart(draw_mini(sub, "부동산_억", "🏠 부동산 가액(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "금융자산_억", "📈 금융투자 자산(억)", "#8b5cf6"), use_container_width=True)
    c3, c4 = st.columns(2); c3.plotly_chart(draw_mini(sub, "예금_억", "💰 현금 및 예금(억)", "#0ea5e9"), use_container_width=True)
    c4.plotly_chart(draw_mini(sub, "월_지출_만", "💸 월 평균 지출(만)", "#f43f5e", "만"), use_container_width=True)

with t_tab:
    st.header("⚖️ 상세 세무 분석 리포트")
    tax_cols = ["연도", "남편나이", "아내나이", "월_세금_만", "소득세_만", "보유세_만", "양도세_만", "취득세_만"]
    t_disp = sub[tax_cols].copy()
    t_disp.columns = ["연도", "남편", "아내", "월세금", "소득세(연)", "보유세(연)", "양도세", "취득세"]
    st.dataframe(t_disp.style.format({c: "{:,.0f}" for c in t_disp.columns if "나이" not in c and "연도" not in c}), use_container_width=True, height=600)

with s_tab:
    st.header("👵 은퇴 후 배당 성장 시뮬레이션")
    f_ret_yr = start_yr + max((h_ret_age - (start_yr-1995)), (w_ret_age - (start_yr-1994)))
    ret_row = df_res[df_res["연도"] == f_ret_yr].iloc[0]
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 은퇴 자산 배분 (%)")
    s_schd = st.sidebar.slider("SCHD (배당성장)", 0, 100, 25)
    s_jepq = st.sidebar.slider("JEPQ (고배당)", 0, 100, 25)
    s_orig = 100 - s_schd - s_jepq
    st.sidebar.info(f"기존 금융자산 유지: {s_orig}%")

    # 배당 시뮬레이션 차트 생성
    div_data = []
    c_inv_val = ret_row["금융자산_억"]
    for y in range(f_ret_yr, 2096):
        schd_p = c_inv_val * (s_schd/100); jepq_p = c_inv_val * (s_jepq/100)
        # SCHD: 3.5% 배당률, 5% 배당성장 / JEPQ: 9.5% 배당률
        m_div = ((schd_p * 0.035 * (1.05**(y-f_ret_yr))) + (jepq_p * 0.095)) * 10000 / 12
        div_data.append({"연도": y, "월_배당금": m_div, "금융자산": c_inv_val})
        c_inv_val *= (1 + inv_gr) # 주가 성장 반영
    
    df_div = pd.DataFrame(div_data)
    fig_div = go.Figure()
    fig_div.add_trace(go.Scatter(x=df_div["연도"], y=df_div["월_배당금"], fill='tozeroy', name="예상 월 배당금(만)"))
    fig_div.update_layout(title="연도별 배당 현금흐름 성장 추이", height=500, template="plotly_white")
    st.plotly_chart(fig_div, use_container_width=True)
    
    c1, c2, c3 = st.columns(3); c1.metric("은퇴 시 금융자산", f"{ret_row['금융자산_억']:.2f}억"); c2.metric("은퇴 첫해 월 배당", f"{df_div.iloc[0]['월_배당금']:,.0f}만"); c3.metric("은퇴 당시 월 지출", f"{ret_row['월_지출_만']:,.0f}만")

with d_tab:
    st.subheader("📋 전체 시뮬레이션 상세 시트")
    n_cols = ["순자산_억", "총자산_억", "부동산_억", "금융자산_억", "예금_억", "대출_억", "월_지출_만", "월_순현금_만"]
    st.dataframe(df_res.style.format({c: "{:.2f}" if "_억" in c else "{:,.0f}" for c in n_cols}), use_container_width=True)
