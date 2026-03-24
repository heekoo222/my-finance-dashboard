import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 프리미엄 디자인 UI/UX
st.set_page_config(page_title="우리 가족 자산 로드맵 v8.0", layout="wide")

# 가독성을 극대화한 CSS (폰트 확대, 배경색, 카드 디자인)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 전체 기본 폰트 크기 및 배경 */
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 21px !important; 
        background-color: #f1f5f9;
    }
    
    .stApp { background-color: #f8fafc; }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown p { font-size: 20px; color: #cbd5e1; }

    /* 메트릭 및 컨테이너 디자인 */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 25px !important;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 10px solid #3b82f6;
    }
    
    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 700;
        height: 60px;
        padding: 10px 30px;
    }
    
    /* 버튼 디자인 */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 700;
        background-color: #3b82f6;
        color: white;
        height: 4rem;
        font-size: 22px !important;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 가족 통합 재무 로드맵 v8.0")
st.markdown("---")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# --- 3. 사이드바: 한글 중심 레버 설정 ---
st.sidebar.header("📋 재무 설정 (단위: 만원)")

# (1) 기본 정보
with st.sidebar.expander("📅 기본 정보 & 시작 시점", expanded=True):
    start_yr = st.number_input("시뮬레이션 시작 연도", value=2026, min_value=2024, key="conf_start_yr")
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830, key="h_sal_val")
        h_inc = st.number_input("남편 급여 인상률(%)", value=3.0, key="h_inc_val") / 100
        h_ret = st.number_input("은퇴 나이", value=55, key="h_ret_val")
        h_p_amt = st.number_input("월 예상연금", value=150, key="h_p_val")
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500, key="w_sal_val")
        w_inc = st.number_input("아내 급여 인상률(%)", value=3.0, key="w_inc_val") / 100
        w_ret = st.number_input("아내 은퇴 나이", value=55, key="w_ret_val")
        w_p_amt = st.number_input("월 예상연금", value=130, key="w_p_val")

# (2) 생활비 설정 (요청 사항: 별도 탭 분리)
with st.sidebar.expander("💸 생활비 레버", expanded=True):
    living_monthly = st.number_input(f"{start_yr}년 기준 월 생활비", value=450, key="living_m_val")
    living_gr = st.number_input("매년 생활비 인상률(%)", value=2.5, key="living_g_val") / 100
    st.caption("※ 식비, 공과금, 보험료 등 가계 고정 지출을 의미합니다.")

# (3) 금융 투자 및 잉여 배분
with st.sidebar.expander("📈 금융 투자 & 수익 배분", expanded=False):
    inv_init = st.number_input("현재 투자 자산", value=15000, key="inv_i_val")
    inv_gr = st.number_input("연간 기대 수익률(%)", value=7.0, key="inv_g_val") / 100
    st.write("💰 **흑자 발생 시 저축 비중**")
    inv_ratio = st.slider("투자 비중(%)", 0, 100, 90, key="inv_r_val")
    cash_ratio = 100 - inv_ratio
    st.caption(f"나머지 {cash_ratio}%는 예금으로 적립됩니다.")

# (4) 대출 상세
with st.sidebar.expander("💳 대출 및 상환 방식", expanded=False):
    debt_init = st.number_input("현재 대출 잔액", value=60000, key="debt_i_val")
    debt_r = st.number_input("대출 금리(%)", value=4.0, key="debt_r_val") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="debt_t_val")
    debt_type = st.selectbox("상환 방식 선택", ["원리금균등", "원금균등"], key="debt_tp_val")

# (5) 부동산 갈아타기 (Gap 로직 유지)
with st.sidebar.expander("🏠 부동산 갈아타기 시나리오", expanded=False):
    re_init_val = st.number_input("현재 집 가액", value=150000, key="re_i_val")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="re_g_val") / 100
    if st.button("➕ 갈아타기 계획 추가"):
        st.session_state.re_trades.append({"year": start_yr+7, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 계획 #{i+1}**")
        tr['year'] = st.number_input(f"매수 연도", start_yr, 2090, tr['year'], key=f"tr_y_{i}")
        est_sale = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_yr))) * 0.95
        st.write(f"👉 예상 매각 대금(세후): **{est_sale/10000:.2f} 억원**")
        tr['new_price'] = st.number_input(f"새 아파트 매수가", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        gap = tr['new_price'] - est_sale
        st.warning(f"⚠️ Gap: **{gap/10000:.2f} 억원** 조달 필요")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input("금융자산", value=tr['use_inv'], key=f"tr_inv_{i}")
        tr['use_debt'] = c2.number_input("대출", value=tr['use_debt'], key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input("예금", value=tr['use_cash'], key=f"tr_cash_{i}")
        if st.button(f"🗑️ #{i+1} 삭제", key=f"del_re_{i}"): st.session_state.re_trades.pop(i); st.rerun()

# (6) 특별 이벤트 & 자녀
with st.sidebar.expander("🚀 특별 이벤트 & 자녀", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 150, 200, 250, 300]})
    for i, kid in enumerate(st.session_state.kids):
        st.write(f"👶 **{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"출생년", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input("영유아(월)", value=kid['costs'][0], key=f"kc0_{i}")
    st.markdown("---")
    if st.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "새 이벤트", "year": start_yr+3, "cost": 6000})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input("명칭", ev['name'], key=f"ev_n_{i}")
        c_y, c_c = st.columns(2)
        ev['year'] = c_y.number_input("년도", start_yr, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = c_c.number_input("비용", 0, 1000000, ev['cost'], key=f"ev_c_{i}")
        if st.button(f"🗑️ 삭제", key=f"del_ev_{i}"): st.session_state.events.pop(i); st.rerun()

# --- 4. 시뮬레이션 엔진 (요청 로직 반영) ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        
        # 1. 수입 (연봉 + 연금)
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        p_amt = (h_p_amt * 12 if h_age >= 65 else 0) + (w_p_amt * 12 if w_age >= 65 else 0)
        total_income = inc_h + inc_w + p_amt
        
        # 2. 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 갈아타기")

        # 3. 세금 (요청 사항: 부동산 가액의 60% 기준으로 보유세 산정)
        t_inc = total_income * 0.15
        t_hold = (c_re * 0.6) * 0.0015 # 과세표준 60% 반영
        t_comp = max(0, (c_re - 120000) * 0.005) if c_re > 120000 else 0
        t_total = t_inc + t_hold + t_comp

        # 4. 지출 (생활비 + 양육비 + 원리금 + 이벤트)
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_total += kid['costs'][0]*12
            elif 8<=ka<=13: k_total += kid['costs'][0]*1.5*12
            elif 14<=ka<=19: k_total += kid['costs'][0]*2.2*12
            elif 20<=ka<=23: k_total += kid['costs'][0]*3.0*12
        
        # 원리금 계산
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

        # 5. 자산 배분 (요청 사항: 월 현금흐름 적자 시 금융자산에서 차감)
        total_exp = curr_living + k_total + t_total + repay_a + ev_cost
        net_flow = total_income - total_exp
        
        if net_flow >= 0:
            c_inv += net_flow * (inv_ratio / 100)
            c_cash += net_flow * (cash_ratio / 100)
        else:
            # 적자 발생 시 금융투자 자산에서 우선 차감
            c_inv += net_flow 
            
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "순자산_억": (c_re + c_inv + c_cash - c_debt)/10000,
            "총자산_억": (c_re + c_inv + c_cash)/10000,
            "부동산_억": c_re/10000, "금융자산_억": c_inv/10000, "대출_억": c_debt/10000,
            "월지출_만": total_exp/12, "월순현금_만": net_flow/12,
            "보유세_만": t_hold/12, "소득세_만": t_inc/12, "이벤트": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 대시보드 출력 (UI/UX 강화) ---
roadmap_tab, tax_tab, data_tab = st.tabs(["📊 자산 로드맵", "⚖️ 세금 분석", "📋 데이터 시트"])

with roadmap_tab:
    period = st.radio("조회 기간 선택", ["10년", "20년", "30년", "전체"], horizontal=True, index=3)
    sub = df.head({"10년":10, "20년":20, "30년":30, "전체":len(df)}[period])

    # 메인 자산 차트
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산(억)", marker_color='#10b981',
                         customdata=sub[["나이", "월순현금_만", "이벤트"]],
                         hovertemplate="<b>%{x}년 (%{customdata[0]})</b><br>순자산: %{y:.2f}억<br>순현금: %{customdata[1]:,.0f}만<br>이벤트: %{customdata[2]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=18))
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 요약 지표
    c1, c2, c3, c4 = st.columns(4)
    def draw_bar(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=22)), height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_bar(sub, "부동산_억", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub, "금융자산_억", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub, "월지출_만", "💸 월 지출(만)", "#f43f5e"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub, "월순현금_만", "💰 월 순현금(만)", "#10b981"), use_container_width=True)

with tax_tab:
    st.header("⚖️ 연도별 세금 상세 분석")
    fig_tax = go.Figure()
    fig_tax.add_trace(go.Scatter(x=sub["연도"], y=sub["소득세_만"], name="소득세(월)", fill='tonexty'))
    fig_tax.add_trace(go.Scatter(x=sub["연도"], y=sub["보유세_만"], name="보유세(월)", fill='tonexty'))
    fig_tax.update_layout(height=500, template="plotly_white", title="월간 세금 지출 추이 (만원)", font=dict(size=18))
    st.plotly_chart(fig_tax, use_container_width=True)
    st.info("💡 보유세는 요청하신 로직에 따라 부동산 가액의 60%를 과세표준으로 산정되었습니다.")

with data_tab:
    st.subheader("📋 전체 시뮬레이션 상세 수치 데이터")
    # 요청 사항: 데이터 시트 컬럼명 한글화 완벽 적용
    st.dataframe(df.style.format({
        "순자산_억": "{:.2f}", "총자산_억": "{:.2f}", "부동산_억": "{:.2f}", 
        "금융자산_억": "{:.2f}", "대출_억": "{:.2f}", "월지출_만": "{:,.0f}", 
        "월순현금_만": "{:,.0f}", "보유세_만": "{:,.0f}", "소득세_만": "{:,.0f}"
    }), use_container_width=True)
