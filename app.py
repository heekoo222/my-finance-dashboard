import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="부부 통합 자산 관리 시스템", layout="wide")

st.title("👨‍👩‍👧‍👦 부부 통합 자산 관리 & 부동산 갈아타기 시뮬레이터")
st.markdown("남편(95년생) & 아내(94년생)의 100세 인생 재무 설계")

# 2. 세션 스테이트 초기화 (이벤트 및 갈아타기 리스트 관리)
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "priority": ["금융자산", "대출", "예금"]}]

# --- 사이드바: 모든 제어 항목 ---
st.sidebar.header("⚙️ 상세 설정")

# (1) 부부 정보 및 소득
with st.sidebar.expander("👤 부부별 수입 & 은퇴", expanded=True):
    col_h, col_w = st.tabs(["남편(95)", "아내(94)"])
    with col_h:
        h_sal = st.number_input("남편 월급 (세후, 만원)", value=550)
        h_inc = st.number_input("남편 급여 인상률 (%)", value=3.0, step=0.1) / 100
        h_bon = st.number_input("남편 상여 비율 (%)", value=15.0) / 100
        h_ret = st.number_input("남편 은퇴 나이", value=55)
        h_p_age = st.number_input("남편 연금 시작", value=65)
        h_p_amt = st.number_input("남편 연금 (월/만)", value=150)
    with col_w:
        w_sal = st.number_input("아내 월급 (세후, 만원)", value=500)
        w_inc = st.number_input("아내 급여 인상률 (%)", value=3.0, step=0.1) / 100
        w_bon = st.number_input("아내 상여 비율 (%)", value=15.0) / 100
        w_ret = st.number_input("아내 은퇴 나이", value=55)
        w_p_age = st.number_input("아내 연금 시작", value=65)
        w_p_amt = st.number_input("아내 연금 (월/만)", value=130)

# (2) 부동산 & 대출 초기값
with st.sidebar.expander("🏠 초기 자산 및 대출", expanded=True):
    re_init = st.number_input("현재 부동산 가액 (억)", value=14.0, step=0.1)
    re_growth = st.number_input("부동산 상승률 (%)", value=4.0, step=0.1) / 100
    debt_init = st.number_input("현재 대출 잔액 (억)", value=6.0, step=0.1)
    debt_rate = st.number_input("대출 이자율 (%)", value=4.0, step=0.1) / 100
    debt_term = st.number_input("대출 상환 기간 (년)", value=30)
    debt_method = st.selectbox("상환 방식", ["원리금 균등 상환", "원금 균등 상환", "만기 일시 (이자만)"])

# (3) 금융자산 & 세금
with st.sidebar.expander("💰 투자 및 세금 설정", expanded=False):
    inv_init = st.number_input("금융투자 시작 (억)", value=1.0, step=0.1)
    inv_growth = st.number_input("투자 수익률 (%)", value=7.0, step=0.1) / 100
    cash_init = st.number_input("예금 시작 (억)", value=0.5, step=0.1)
    tax_base_rate = st.number_input("공시지가 비율 (보수적 %)", value=60.0) / 100
    holding_tax_rate = st.number_input("보유세율 (연/%)", value=0.2) / 100
    inv_tax_rate = st.number_input("금융소득세 (%)", value=15.4) / 100

# (4) 자녀 양육비
with st.sidebar.expander("👶 자녀 계획", expanded=False):
    kid_count = st.number_input("자녀 수", 0, 3, 1)
    kid_births = [st.number_input(f"{i+1}번 자녀 출산년도", 2024, 2045, 2027+i*2) for i in range(kid_count)]
    st.info("연령대별 월 양육비(만): 0~7세(100), 8~13세(120), 14~19세(180), 20~23세(250)")

# (5) 부동산 갈아타기 (멀티 추가)
st.sidebar.subheader("🔄 갈아타기 시나리오")
def add_trade(): st.session_state.re_trades.append({"year": 2035, "new_price": 25.0, "priority": ["금융자산", "대출", "예금"]})
st.sidebar.button("➕ 갈아타기 추가", on_click=add_trade)

for i, trade in enumerate(st.session_state.re_trades):
    with st.sidebar.expander(f"갈아타기 #{i+1}", expanded=True):
        trade['year'] = st.number_input(f"매수년도", 2025, 2095, trade['year'], key=f"tr_y_{i}")
        trade['new_price'] = st.number_input(f"매수가(억)", 0.0, 100.0, trade['new_price'], key=f"tr_p_{i}")
        trade['priority'] = st.multiselect(f"자금조달 순위", ["금융자산", "예금", "대출"], default=trade['priority'], key=f"tr_pr_{i}")

# (6) 특별 이벤트
st.sidebar.subheader("🚀 특별 이벤트")
def add_event(): st.session_state.events.append({"name": "신규", "year": 2025, "cost": 0.0})
st.sidebar.button("➕ 이벤트 추가", on_click=add_event)
for i, ev in enumerate(st.session_state.events):
    c1, c2, c3 = st.sidebar.columns([2,1,1])
    ev['name'] = c1.text_input(f"명", ev['name'], key=f"ev_n_{i}")
    ev['year'] = c2.number_input(f"년", 2025, 2095, ev['year'], key=f"ev_y_{i}")
    ev['cost'] = c3.number_input(f"억", 0.0, 50.0, ev['cost'], key=f"ev_c_{i}")

# --- 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re = re_init; c_inv = inv_init; c_cash = cash_init; c_debt = debt_init
    c_h_sal = h_sal; c_w_sal = w_sal
    living_cost = 400 # 월 기본 생활비

    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        
        # 1. 수입 (급여 + 연금)
        inc_h = (c_h_sal * 12 * (1 + h_bon)) / 10000 if h_age <= h_ret else 0
        inc_w = (c_w_sal * 12 * (1 + w_bon)) / 10000 if w_age <= w_ret else 0
        pen = 0
        if h_age >= h_p_age: pen += (h_p_amt * 12) / 10000
        if w_age >= w_p_age: pen += (w_p_amt * 12) / 10000
        total_inc = inc_h + inc_w + pen
        
        # 2. 부동산 갈아타기 처리
        for trade in st.session_state.re_trades:
            if year == trade['year']:
                gap = trade['new_price'] - (c_re * 0.98) # 매도비용 등 감안 98% 회수
                for source in trade['priority']:
                    if gap <= 0: break
                    if source == "금융자산":
                        use = min(c_inv, gap); c_inv -= use; gap -= use
                    elif source == "예금":
                        use = min(c_cash, gap); c_cash -= use; gap -= use
                    elif source == "대출":
                        c_debt += gap; gap = 0
                c_re = trade['new_price']

        # 3. 지출 계산 (양육비/대출이자/세금/이벤트)
        k_cost = 0
        for b_year in kid_births:
            ka = year - b_year
            if 0<=ka<=7: k_cost += 100*12/10000
            elif 8<=ka<=13: k_cost += 120*12/10000
            elif 14<=ka<=19: k_cost += 180*12/10000
            elif 20<=ka<=23: k_cost += 250*12/10000
        
        tax_re = (c_re * tax_base_rate) * holding_tax_rate
        tax_inv = (c_inv * inv_growth) * inv_tax_rate if c_inv > 0 else 0
        interest = c_debt * debt_rate
        ev_cost = sum(e['cost'] for e in st.session_state.events if e['year'] == year)
        
        # 4. 자산 업데이트
        c_re *= (1 + re_growth)
        inv_return = c_inv * inv_growth if c_inv > 0 else 0
        
        # 여유자금(Net Cashflow) 계산
        net_cf = total_inc - ((living_cost*12/10000) + interest + tax_re + tax_inv + k_cost + ev_cost)
        
        # 대출 상환 로직 (원리금 균등 대략치 반영)
        if c_debt > 0 and year < 2025 + debt_term:
            repayment = (debt_init / debt_term) # 단순 원금균등 시뮬레이션
            c_debt = max(0, c_debt - repayment)
        
        c_inv += (inv_return + net_cf)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "순자산": round(total_asset - c_debt, 2), "총자산": round(total_asset, 2), "부채": round(c_debt, 2),
            "부동산": round(c_re, 2), "금융자산": round(c_inv, 2), "예금": round(c_cash, 2),
            "연수입": round(total_inc, 2), "연지출": round(interest + tax_re + tax_inv + k_cost + ev_cost + (living_cost*12/10000), 2)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 대시보드 출력 ---
st.subheader("📊 자산 시뮬레이션 분석")
tab_res, tab_chart, tab_data = st.tabs(["💡 요약 및 차트", "📈 자산군별 추이", "📋 상세 데이터"])

with tab_res:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("60세 순자산", f"{df.iloc[35]['순자산']} 억")
    c2.metric("최종 순자산(95세)", f"{df.iloc[-1]['순자산']} 억")
    c3.metric("최대 부채 규모", f"{df['부채'].max()} 억")
    c4.metric("연평균 지출", f"{round(df['연지출'].mean(), 1)} 억")
    
    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(x=df["연도"], y=df["순자산"], name="순자산", fill='tozeroy', line=dict(color='green')))
    fig_main.add_trace(go.Scatter(x=df["연도"], y=df["총자산"], name="총자산", line=dict(dash='dot', color='blue')))
    fig_main.add_trace(go.Bar(x=df["연도"], y=df["부채"], name="부채", marker_color='red', opacity=0.4))
    fig_main.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig_main, use_container_width=True)

with tab_chart:
    st.write("기간별 자산 구성 변화 (부동산/금융/예금)")
    period = st.radio("기간 선택", ["10년", "30년", "전체"], horizontal=True)
    p_map = {"10년": 10, "30년": 30, "전체": 71}
    sub_df = df.head(p_map[period])
    
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부동산"], name="부동산"))
    fig_stack.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["금융자산"], name="금융자산"))
    fig_stack.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["예금"], name="예금"))
    fig_stack.update_layout(barmode='stack', height=500)
    st.plotly_chart(fig_stack, use_container_width=True)

with tab_data:
    st.dataframe(df, use_container_width=True, hide_index=True)
