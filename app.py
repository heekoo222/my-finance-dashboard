import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인 UI/UX
st.set_page_config(page_title="우리 가족 자산 마스터 v9.0", layout="wide")

# CSS: 사이드바 색상 변경 및 폰트 가독성 강화
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 20px !important; 
    }
    
    /* 왼쪽 사이드바: 연한 하늘색 바탕 + 검정 글씨 */
    section[data-testid="stSidebar"] {
        background-color: #e0f2fe !important;
        border-right: 1px solid #bae6fd;
    }
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stHeader {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 25px !important;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 6px solid #0ea5e9;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 22px !important;
        font-weight: 700;
        padding: 12px 30px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Master Plan v9.0")
st.markdown("---")

# --- 2. 데이터 영속성 ---
if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# --- 3. 사이드바: 시뮬레이션 레버 ---

# (0) 시작 연도 (별도 탭/섹션)
with st.sidebar.expander("📅 시뮬레이션 시작 시점", expanded=True):
    start_yr = st.number_input("시뮬레이션 시작 연도", value=2026, min_value=2024, key="sys_start_yr")

# (1) 급여 탭: 상여금 비율 추가
with st.sidebar.expander("👤 부부 소득 및 상여금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("월급(만)", value=830, key="h_s")
        h_bonus_rate = st.number_input("상여비율(%)", value=20.0, key="h_br") / 100
        h_inc = st.number_input("인상률(%)", value=3.0, key="h_i") / 100
        h_ret = st.number_input("은퇴나이", value=55, key="h_r")
        h_p_amt = st.number_input("월 연금", value=150, key="h_p")
    with w_tab:
        w_sal = st.number_input("월급(만)", value=500, key="w_s")
        w_bonus_rate = st.number_input("상여비율(%)", value=20.0, key="w_br") / 100
        w_inc = st.number_input("인상률(%)", value=3.0, key="w_i") / 100
        w_ret = st.number_input("은퇴나이", value=55, key="w_r")
        w_p_amt = st.number_input("월 연금", value=130, key="w_p")
    st.caption("※ 연간 상여금 = 월 급여 × 상여비율 × 12로 계산됩니다.")

# (2) 생활비 & 투자 배분
with st.sidebar.expander("💸 지출 및 투자 배분", expanded=False):
    living_monthly = st.number_input("월 고정 생활비", value=450, key="liv_m")
    living_gr = st.number_input("생활비 인상률(%)", value=2.5, key="liv_g") / 100
    st.markdown("---")
    inv_ratio = st.slider("💰 흑자 시 투자 비중(%)", 0, 100, 90, key="inv_r")
    cash_ratio = 100 - inv_ratio

# (3) 기타 금융/부동산/이벤트
with st.sidebar.expander("📈 자산 및 대출 정보", expanded=False):
    inv_init = st.number_input("현재 투자금", value=15000, key="inv_ini")
    inv_gr = st.number_input("투자 수익률(%)", value=7.0, key="inv_gr") / 100
    debt_init = st.number_input("현재 대출", value=60000, key="debt_ini")
    debt_r = st.number_input("대출 금리(%)", value=4.0, key="debt_r_val") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="debt_t_val")
    debt_type = st.selectbox("상환 방식", ["원리금균등", "원금균등"], key="debt_tp")

with st.sidebar.expander("🏠 부동산 갈아타기", expanded=False):
    re_init_val = st.number_input("현재 집 가액", value=150000, key="re_ini")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="re_gr") / 100
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": start_yr+10, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        tr['year'] = st.number_input(f"매수년도 {i}", start_yr, 2090, tr['year'], key=f"try_{i}")
        tr['new_price'] = st.number_input(f"매수가 {i}", 0, 1000000, tr['new_price'], key=f"trp_{i}")
        if st.button(f"🗑️ #{i+1} 삭제", key=f"re_del_{i}"): st.session_state.re_trades.pop(i); st.rerun()

# --- 4. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []
        
        # 1. 수입 (기본급 + 연간 상여금 + 연금)
        inc_h_base = (c_h_sal * 12) if h_age <= h_ret else 0
        inc_h_bonus = (c_h_sal * h_bonus_rate * 12) if h_age <= h_ret else 0
        inc_w_base = (c_w_sal * 12) if w_age <= w_ret else 0
        inc_w_bonus = (c_w_sal * w_bonus_rate * 12) if w_age <= w_ret else 0
        p_amt = (h_p_amt * 12 if h_age >= 65 else 0) + (w_p_amt * 12 if w_age >= 65 else 0)
        
        total_income_annual = inc_h_base + inc_h_bonus + inc_w_base + inc_w_bonus + p_amt
        
        # 2. 지출 및 세금
        t_hold = (c_re * 0.6) * 0.002
        t_comp = max(0, (c_re - 120000) * 0.005)
        t_total = (total_income_annual * 0.15) + t_hold + t_comp
        
        curr_living = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        
        # 원리금 계산
        interest_a = c_debt * debt_r
        if c_debt > 0 and (year < start_yr + debt_term):
            if debt_type == "원리금균등":
                repay_a = (debt_init * debt_r * (1+debt_r)**debt_term) / ((1+debt_r)**debt_term - 1)
                principal_a = repay_a - interest_a
            else:
                principal_a = debt_init / debt_term; repay_a = principal_a + interest_a
        else: principal_a, repay_a = 0, 0

        # 3. 부동산 거래
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠갈아타기")

        # 4. 순현금흐름 및 자산배분
        total_exp = curr_living + t_total + repay_a
        net_flow = total_income_annual - total_exp
        
        if net_flow >= 0:
            c_inv += net_flow * (inv_ratio / 100); c_cash += net_flow * (cash_ratio / 100)
        else:
            c_inv += net_flow # 적자 시 금융자산 차감
            
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a)
        
        res.append({
            "연도": year, "남편나이": h_age, "아내나이": w_age,
            "순자산_억": (c_re + c_inv + c_cash - c_debt)/10000,
            "총자산_억": (c_re + c_inv + c_cash)/10000,
            "부동산_억": c_re/10000, "금융자산_억": c_inv/10000, "예금_억": c_cash/10000, "대출_억": c_debt/10000,
            "월_순현금_만": net_flow/12, "월_지출_만": total_exp/12, "연_상여금_만": (inc_h_bonus + inc_w_bonus),
            "이벤트": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 대시보드 탭 구성 ---
roadmap_tab, silver_tab, data_tab = st.tabs(["📊 자산 성장 로드맵", "👵 은퇴 & 배당 시뮬레이션", "📋 데이터 상세"])

with roadmap_tab:
    period = st.radio("🔍 기간 선택", ["10년", "20년", "30년", "전체"], horizontal=True, index=3)
    sub = df.head({"10년":10, "20년":20, "30년":30, "전체":len(df)}[period])

    # 메인 그래프
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산(억)", marker_color='#10b981'))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="대출(억)", marker_color='#ef4444'))
    fig.update_layout(barmode='stack', hovermode="x unified", height=600, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # 5분할 지표 (예금 추가)
    c1, c2, c3, c4, c5 = st.columns(5)
    def draw_bar(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color))
        f.update_layout(title=title, height=250, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
        return f
    c1.plotly_chart(draw_bar(sub, "부동산_억", "🏠 부동산", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub, "금융자산_억", "📈 금융자산", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub, "예금_억", "💰 예금", "#0ea5e9"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub, "월_지출_만", "💸 월지출", "#f43f5e"), use_container_width=True)
    c5.plotly_chart(draw_bar(sub, "월_순현금_만", "💵 순현금", "#10b981"), use_container_width=True)

with silver_tab:
    st.header("👵 은퇴 후 배당 소득 시뮬레이션")
    st.markdown("금융자산의 50%를 **SCHD(배당성장)와 JEPQ(고배당)에 5:5**로 투자했을 때의 결과입니다.")
    
    # 두 명 중 나중 은퇴 시점 찾기
    final_ret_yr = start_yr + max((h_ret - (start_yr-1995)), (w_ret - (start_yr-1994)))
    ret_row = df[df["연도"] == final_ret_yr].iloc[0]
    
    col_a, col_b = st.columns(2)
    col_a.metric("은퇴 시점 총자산", f"{ret_row['총자산_억']:.2f} 억원")
    col_b.metric("은퇴 시점 순자산", f"{ret_row['순자산_억']:.2f} 억원")
    
    st.write(f"📍 **{final_ret_yr}년 은퇴 시점 자산 배분 전략**")
    
    # 배당 시뮬레이션 로직
    # 금융자산의 50%를 배당주에 투자
    div_invest_amt = ret_row["금융자산_억"] * 0.5
    schd_amt = div_invest_amt * 0.5
    jepq_amt = div_invest_amt * 0.5
    
    # 배당수익률 가정 (SCHD: 3.5%, JEPQ: 9.5%)
    schd_div = schd_amt * 0.035
    jepq_div = jepq_amt * 0.095
    monthly_dividend = (schd_div + jepq_div) * 10000 / 12
    
    c_div1, c_div2, c_div3 = st.columns(3)
    c_div1.metric("배당 투자 원금", f"{div_invest_amt:.2f} 억원")
    c_div2.metric("예상 월 배당금", f"{monthly_dividend:,.0f} 만원")
    c_div3.metric("기존 월 지출", f"{ret_row['월_지출_만']:,.0f} 만원")
    
    # 배당 소득 그래프
    div_years = range(final_ret_yr, 2096)
    div_flow = []
    temp_div_asset = div_invest_amt
    for yr in div_years:
        # 배당금은 연 5% 성장 가정 (SCHD 영향)
        y_div = temp_div_asset * 0.065 # 가중평균 배당률 6.5%
        div_flow.append({"연도": yr, "월_배당금_만": (y_div * 10000 / 12)})
        temp_div_asset *= 1.04 # 자산 가치 연 4% 성장 가정
        
    div_df = pd.DataFrame(div_flow)
    fig_div = go.Figure()
    fig_div.add_trace(go.Scatter(x=div_df["연도"], y=div_df["월_배당금_만"], fill='tozeroy', name="월 예상 배당금"))
    fig_div.update_layout(title="은퇴 후 연도별 월 배당 소득 추이", height=450, template="plotly_white")
    st.plotly_chart(fig_div, use_container_width=True)

with data_tab:
    st.subheader("📋 전체 시뮬레이션 데이터 시트")
    # 한글화된 컬럼으로 표시
    num_cols = ["순자산_억", "총자산_억", "부동산_억", "금융자산_억", "예금_억", "대출_억", "월_순현금_만", "월_지출_만", "연_상여금_만"]
    st.dataframe(df.style.format({c: "{:.2f}" if "_억" in c else "{:,.0f}" for c in num_cols}), use_container_width=True)
