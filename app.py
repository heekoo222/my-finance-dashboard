import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 프리미엄 스타일링
st.set_page_config(page_title="Family Wealth Roadmap", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 기본 폰트 크기 및 시각적 요소 대폭 확대 */
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 21px !important; 
    }
    
    .main { background-color: #f8fafc; }

    /* 사이드바 UIUX 개선: 가독성 중심 */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #f1f5f9;
        font-weight: 700;
        font-size: 22px;
    }
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border-radius: 15px;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* 입력창 디자인 */
    .stNumberInput, .stSlider {
        margin-bottom: 5px;
    }

    /* 메트릭 카드 프리미엄 디자인 */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 30px !important;
        border-radius: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border-top: 6px solid #3b82f6;
    }

    /* 탭 가독성 */
    .stTabs [data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 700;
        padding: 15px 40px;
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 700;
        background-color: #3b82f6;
        color: white;
        height: 4.5rem;
        font-size: 24px !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 우리 가족 통합 재무 마스터 플랜")
st.write("---")

# --- 2. 데이터 관리 (세션 스테이트) ---
if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# --- 3. 사이드바: 한눈에 들어오는 레버 탭 (UIUX 개선) ---
st.sidebar.title("🛠️ 재무 시뮬레이션 설정")

# (1) 시점 및 수입
with st.sidebar.expander("👤 기본 정보 & 소득 (만원)", expanded=True):
    start_yr = st.number_input("📅 시뮬레이션 시작 연도", value=2026, min_value=2024, key="conf_start_yr")
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("현재 월급", value=830, key="h_sal_in")
        h_inc = st.number_input("급여 인상률(%)", value=3.0, key="h_inc_in") / 100
        h_ret = st.number_input("은퇴 나이", value=55, key="h_ret_in")
        h_p_amt = st.number_input("월 예상연금", value=150, key="h_p_in")
    with w_tab:
        w_sal = st.number_input("현재 월급", value=500, key="w_sal_in")
        w_inc = st.number_input("급여 인상률(%)", value=3.0, key="w_inc_in") / 100
        w_ret = st.number_input("은퇴 나이", value=55, key="w_ret_in")
        w_p_amt = st.number_input("월 예상연금", value=130, key="w_p_in")

# (2) 생활비 레버 (별도 탭)
with st.sidebar.expander("💸 생활비 레버 (만원)", expanded=True):
    living_monthly = st.number_input("매월 고정 생활비", value=450, key="living_m")
    living_gr = st.number_input("연간 물가상승률(%)", value=2.5, key="living_g") / 100

# (3) 금융 투자 및 배분
with st.sidebar.expander("📈 금융 투자 & 배분", expanded=False):
    inv_init = st.number_input("현재 투자 원금", value=15000, key="inv_i")
    inv_gr = st.number_input("기대 투자수익률(%)", value=7.0, key="inv_g") / 100
    st.markdown("---")
    inv_ratio = st.slider("💰 흑자 발생 시 투자 비중(%)", 0, 100, 90, key="inv_r")
    cash_ratio = 100 - inv_ratio
    st.caption(f"나머지 {cash_ratio}%는 예금으로 적립됩니다.")

# (4) 대출 관리
with st.sidebar.expander("💳 대출 및 상환 방식", expanded=False):
    debt_init = st.number_input("현재 대출 잔액", value=60000, key="debt_i")
    debt_r = st.number_input("대출 금리(%)", value=4.0, key="debt_r") / 100
    debt_term = st.number_input("남은 상환기간(년)", value=30, key="debt_t")
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"], key="debt_tp")

# (5) 부동산 갈아타기
with st.sidebar.expander("🏠 부동산 갈아타기 (만원)", expanded=False):
    re_init_val = st.number_input("현재 부동산 가액", value=150000, key="re_i")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="re_g") / 100
    st.markdown("---")
    if st.button("➕ 갈아타기 계획 추가"):
        st.session_state.re_trades.append({"year": start_yr+7, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 시나리오 #{i+1}**")
        tr['year'] = st.number_input(f"매수 연도 {i}", start_yr, 2090, tr['year'], key=f"tr_y_{i}")
        est_sale = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_yr))) * 0.95
        st.info(f"예상 매각 대금: {est_sale/10000:.2f} 억원")
        tr['new_price'] = st.number_input(f"새 아파트 매수가 {i}", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        gap = tr['new_price'] - est_sale
        st.warning(f"조달 필요 Gap: {gap/10000:.2f} 억원")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융자산{i}", value=tr['use_inv'], key=f"tr_inv_{i}")
        tr['use_debt'] = c2.number_input(f"대출{i}", value=tr['use_debt'], key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input(f"예금{i}", value=tr['use_cash'], key=f"tr_cash_{i}")
        if st.button(f"🗑️ #{i+1} 삭제", key=f"del_re_{i}"): st.session_state.re_trades.pop(i); st.rerun()

# (6) 특별 이벤트 & 자녀
with st.sidebar.expander("🚀 이벤트 & 자녀", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 150, 200, 250, 300]})
    for i, kid in enumerate(st.session_state.kids):
        st.write(f"👶 **{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"출생년 {i}", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"영유아 월비용 {i}", value=kid['costs'][0], key=f"kc0_{i}")
    st.markdown("---")
    if st.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "새 이벤트", "year": start_yr+3, "cost": 6000})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"명칭 {i}", ev['name'], key=f"ev_n_{i}")
        cy, cc = st.columns(2)
        ev['year'] = cy.number_input(f"연도 {i}", start_yr, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = cc.number_input(f"비용 {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")
        if st.button(f"🗑️ #{i+1} 삭제", key=f"del_ev_{i}"): st.session_state.events.pop(i); st.rerun()

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        p_amt = (h_p_amt * 12 if h_age >= 65 else 0) + (w_p_amt * 12 if w_age >= 65 else 0)
        t_income = (c_h_sal * 13 if h_age <= h_ret else 0) + (c_w_sal * 13 if w_age <= w_ret else 0) + p_amt
        
        # 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠갈아타기({tr['new_price']//10000}억)")

        # 세금 로직 (요청 사항: 가액 60%에 0.2% 적용)
        t_inc = t_income * 0.15 
        t_hold = (c_re * 0.6) * 0.002 # ✅ 정밀 수정: 0.2% 보유세
        t_comp = max(0, (c_re - 120000) * 0.005) if c_re > 120000 else 0
        t_total = t_inc + t_hold + t_comp

        # 지출 (생활비 + 양육비 + 원리금 + 이벤트)
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if 0<=ka<=7: k_total += kid['costs'][0]*12
            elif 8<=ka<=13: k_total += kid['costs'][0]*1.5*12
            elif 14<=ka<=19: k_total += kid['costs'][0]*2.2*12
            elif 20<=ka<=23: k_total += kid['costs'][0]*3.0*12
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")
        
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

        # 자산 업데이트 (요청 사항: 적자 시 금융자산 차감)
        total_exp = curr_living + k_total + t_total + repay_a + ev_cost
        net_flow = t_income - total_exp
        
        if net_flow >= 0:
            c_inv += net_flow * (inv_ratio / 100); c_cash += net_flow * (cash_ratio / 100)
        else:
            c_inv += net_flow # ✅ 적자 시 금융자산 우선 소진
            
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "순자산_억": (c_re + c_inv + c_cash - c_debt)/10000,
            "총자산_억": (c_re + c_inv + c_cash)/10000,
            "부동산_억": c_re/10000, "금융자산_억": c_inv/10000, "대출_억": c_debt/10000,
            "월_지출_만": total_exp/12, "월_순현금_만": net_flow/12,
            "소득세_만": t_inc/12, "보유세_만": t_hold/12, "종부세_만": t_comp/12, "세금합계_만": t_total/12,
            "이벤트": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df_final = run_simulation()

# --- 5. 대시보드 출력 (UIUX 강화) ---
roadmap_tab, tax_tab, data_tab = st.tabs(["📊 자산 성장 로드맵", "⚖️ 상세 세금 분석 표", "📋 데이터 시트"])

with roadmap_tab:
    # 조회 기간 선택
    period = st.radio("🔍 시뮬레이션 기간", ["10년", "20년", "30년", "전체"], horizontal=True, index=3)
    sub = df_final.head({"10년":10, "20년":20, "30년":30, "전체":len(df_final)}[period])

    # 메인 차트
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산(억)", marker_color='#10b981',
                         customdata=sub[["나이", "월_순현금_만", "이벤트"]],
                         hovertemplate="<span style='font-size:24px'><b>%{x}년 (%{customdata[0]})</b></span><br>" + 
                                       "순자산: <span style='color:#10b981; font-size:22px'><b>%{y:.2f}억</b></span><br>" + 
                                       "월 순현금: <span style='color:#3b82f6'><b>%{customdata[1]:,.0f}만</b></span><br>" + 
                                       "이벤트: %{customdata[2]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="대출부채(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=650, template="plotly_white", 
                      font=dict(size=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 지표
    cols = st.columns(4)
    def draw_bar(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=22)), height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    cols[0].plotly_chart(draw_bar(sub, "부동산_억", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    cols[1].plotly_chart(draw_bar(sub, "금융자산_억", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    cols[2].plotly_chart(draw_bar(sub, "월_지출_만", "💸 월 지출(만)", "#f43f5e"), use_container_width=True)
    cols[3].plotly_chart(draw_bar(sub, "월_순현금_만", "💰 월 순현금(만)", "#10b981"), use_container_width=True)

with tax_tab:
    # [요청 사항 3] 세금은 표로만 가독성 있게 표시
    st.header("⚖️ 연도별 상세 세무 리포트 (만원/월)")
    st.markdown("매월 지출되는 세금의 상세 내역입니다.")
    tax_cols = ["연도", "나이", "소득세_만", "보유세_만", "종부세_만", "세금합계_만"]
    tax_display = sub[tax_cols].copy()
    tax_display.columns = ["연도", "나이", "근로/연금소득세", "재산보유세(0.2%)", "종부세", "총 세금"]
    st.dataframe(tax_display.style.format({c: "{:,.0f}" for c in ["근로/연금소득세", "재산보유세(0.2%)", "종부세", "총 세금"]}), 
                 use_container_width=True, height=600)
    st.info("💡 보유세는 부동산 가액의 60%를 과세표준으로 하여 연 0.2%로 계산되었습니다.")

with data_tab:
    st.subheader("📋 전체 시뮬레이션 상세 수치 데이터")
    # 모든 숫자 컬럼 한글화 및 포맷팅
    num_cols = ["순자산_억", "총자산_억", "부동산_억", "금융자산_억", "대출_억", "월_지출_만", "월_순현금_만", "세금합계_만"]
    st.dataframe(df_final.style.format({c: "{:.2f}" if "_억" in c else "{:,.0f}" for c in num_cols}), 
                 use_container_width=True)
