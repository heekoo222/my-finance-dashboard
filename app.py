import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="통합 재무 대시보드", layout="wide")
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

st.title("📊 우리 가족 자산 관리 최종 시뮬레이터")

# --- 세션 스테이트 초기화 (데이터 누락 방지 및 레버 유지) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "use_inv": 5.0, "use_debt": 5.0, "use_cash": 1.0}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]

# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 설정")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 수입 & 은퇴/연금", expanded=True):
    t1, t2 = st.tabs(["남편(95)", "아내(94)"])
    with t1:
        h_sal = st.number_input("남편 월급(만)", value=550)
        h_inc = st.number_input("남편 인상률(%)", value=3.0) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55)
        h_p_age = st.number_input("남편 연금시작", value=65)
        h_p_amt = st.number_input("남편 연금액(월/만)", value=150)
    with t2:
        w_sal = st.number_input("아내 월급(만)", value=500)
        w_inc = st.number_input("아내 인상률(%)", value=3.0) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55)
        w_p_age = st.number_input("아내 연금시작", value=65)
        w_p_amt = st.number_input("아내 연금액(월/만)", value=130)

# (2) 자녀별 개별 양육비
with st.sidebar.expander("👶 자녀별 맞춤 양육비", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 출생년도", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아비(만)", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등비(만)", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등비(만)", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등비(만)", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학비(만)", value=kid['costs'][4], key=f"kc4_{i}")

# (3) 부동산 갈아타기 (자금 출처 직접 입력)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.sidebar.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2040, "new_price": 35.0, "use_inv": 0.0, "use_debt": 0.0, "use_cash": 0.0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**갈아타기 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", 2025, 2095, tr['year'], key=f"try_{i}")
        tr['new_price'] = st.number_input(f"매수가(억) {i}", 0.0, 100.0, tr['new_price'], key=f"trp_{i}")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융자산활용(억) {i}", value=tr['use_inv'], key=f"tri_{i}")
        tr['use_debt'] = c2.number_input(f"추가대출(억) {i}", value=tr['use_debt'], key=f"trd_{i}")
        tr['use_cash'] = c3.number_input(f"예금활용(억) {i}", value=tr['use_cash'], key=f"trc_{i}")

# (4) 특별 이벤트 레버
with st.sidebar.expander("🚀 특별 이벤트 추가/수정", expanded=True):
    if st.sidebar.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "이벤트", "year": 2025, "cost": 0.0})
    for i, ev in enumerate(st.session_state.events):
        e_c1, e_c2, e_c3 = st.columns([2,1,1])
        ev['name'] = e_c1.text_input(f"명칭 {i}", ev['name'], key=f"evn_{i}")
        ev['year'] = e_c2.number_input(f"년도 {i}", 2025, 2095, ev['year'], key=f"evy_{i}")
        ev['cost'] = e_c3.number_input(f"비용(억) {i}", 0.0, 50.0, ev['cost'], key=f"evc_{i}")

# (5) 자산 및 세금 기본값
with st.sidebar.expander("📈 자산/세금 기본 가정", expanded=False):
    re_init, re_gr = st.number_input("현재 부동산(억)", value=14.0), st.number_input("부동산상승률(%)", value=4.0)/100
    inv_init, inv_gr = st.number_input("현재 투자(억)", value=1.0), st.number_input("투자수익률(%)", value=7.0)/100
    debt_init, debt_r = st.number_input("현재 대출(억)", value=6.0), st.number_input("대출금리(%)", value=4.0)/100
    tax_base, tax_rate = st.number_input("공시지가비율(%)", value=60.0)/100, st.number_input("보유세율(%)", value=0.2)/100

# --- 시뮬레이션 엔진 ---
def run_sim():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        events_text = []

        # 1. 수입 계산
        inc_h = (c_h_sal * 13) / 10000 if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) / 10000 if w_age <= w_ret else 0
        pension = 0
        if h_age >= h_p_age: pension += (h_p_amt * 12) / 10000
        if w_age >= w_p_age: pension += (w_p_amt * 12) / 10000
        y_income = inc_h + inc_w + pension

        # 2. 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']
                c_debt += tr['use_debt']
                c_cash -= tr['use_cash']
                c_re = tr['new_price']
                events_text.append(f"🏠{tr['new_price']}억 매수")

        # 3. 양육비 계산
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: events_text.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_total += kid['costs'][0]*12/10000
            elif 8<=ka<=13: k_total += kid['costs'][1]*12/10000
            elif 14<=ka<=16: k_total += kid['costs'][2]*12/10000
            elif 17<=ka<=19: k_total += kid['costs'][3]*12/10000
            elif 20<=ka<=23: k_total += kid['costs'][4]*12/10000

        # 4. 세금 및 특별 이벤트
        tax = (c_re * tax_base) * tax_rate
        interest = c_debt * debt_r
        ev_total = 0
        for ev in st.session_state.events:
            if year == ev['year']:
                ev_total += ev['cost']
                events_text.append(f"🚀{ev['name']}")

        # 5. 자산 흐름 업데이트
        net_flow = y_income - (4.0 + k_total + tax + interest + ev_total) 
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_flow) * (1 + inv_gr)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}", "총자산": total_asset, "순자산": total_asset - c_debt,
            "부동산": c_re, "금융자산": c_inv, "예금": c_cash, "부채": c_debt, "연수입": y_income,
            "이벤트": " ".join(events_text)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_sim()

# --- 시각화 UI ---
tab_main, tab_data = st.tabs(["📊 자산 시뮬레이션", "📑 상세 데이터"])

with tab_main:
    p_choice = st.radio("조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True)
    p_val = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}[p_choice]
    sub_df = df.head(p_val)

    # 메인 그래프
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산", fill='tozeroy', line=dict(color='#27ae60', width=4)))
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산", line=dict(color='#2980b9', width=2, dash='dot')))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채", marker_color='#c0392b', opacity=0.3))
    
    for _, row in sub_df.iterrows():
        if row["이벤트"]:
            fig.add_annotation(x=row["연도"], y=row["총자산"], text=f"<b>{row['이벤트']}</b>", 
                               showarrow=True, arrowhead=2, bgcolor="#f1c40f", font=dict(size=12))

    fig.update_layout(title=f"자산 성장 추이 ({p_choice})", hovermode="x unified", height=550, font=dict(size=14))
    st.plotly_chart(fig, use_container_width=True)

    # 4분할 세부 막대 그래프
    st.markdown("### 🔍 자산군별 세부 추이 (막대)")
    c1, c2, c3, c4 = st.columns(4)
    
    def make_bar_chart(col, title, color):
        f = go.Figure(go.Bar(x=sub_df["연도"], y=sub_df[col], name=title, marker_color=color))
        f.update_layout(title=title, height=250, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
        return f

    c1.plotly_chart(make_bar_chart("부동산", "🏠 부동산", "#e67e22"), use_container_width=True)
    c2.plotly_chart(make_bar_chart("금융자산", "📈 금융자산", "#9b59b6"), use_container_width=True)
    c3.plotly_chart(make_bar_chart("부채", "📉 부채", "#e74c3c"), use_container_width=True)
    c4.plotly_chart(make_bar_chart("연수입", "💵 연수입", "#16a085"), use_container_width=True)

with tab_data:
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
