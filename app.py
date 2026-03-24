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
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; background-color: #3b82f6; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 우리 가족 통합 재무 시뮬레이터 (2026-2095)")
st.info("💡 모든 입력(왼쪽 레버)은 **'만원'** 단위이며, 모든 결과(오른쪽 차트/표)는 **'억원'** 단위로 자동 표시됩니다.")

# --- 2. 데이터 유지 (세션 스테이트 초기화) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 모든 레버 총망라 (단위: 만원) ---
st.sidebar.header("⚙️ 생애 주기 설정 (단위: 만원)")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 급여 및 은퇴/연금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급(만원)", value=550)
        h_inc = st.number_input("남편 인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55)
        h_p_age = st.number_input("남편 연금수령나이", value=65)
        h_p_amt = st.number_input("남편 예상연금(월/만원)", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급(만원)", value=500)
        w_inc = st.number_input("아내 인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55)
        w_p_age = st.number_input("아내 연금수령나이", value=65)
        w_p_amt = st.number_input("아내 예상연금(월/만원)", value=130)

# (2) 자녀별 시기별 양육비 레버
with st.sidebar.expander("👶 자녀별 시기별 양육비", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 상세 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 탄생년도", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아비(월)", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등비(월)", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등비(월)", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등비(월)", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학비(월)", value=kid['costs'][4], key=f"kc4_{i}")

# (3) 부동산 갈아타기 (자금 출처 직접 입력)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.sidebar.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**갈아타기 시나리오 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", 2025, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"매수가(만원) {i}", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융자산활용 {i}", value=tr['use_inv'], key=f"tr_i_{i}")
        tr['use_debt'] = c2.number_input(f"추가대출 {i}", value=tr['use_debt'], key=f"tr_d_{i}")
        tr['use_cash'] = c3.number_input(f"예금활용 {i}", value=tr['use_cash'], key=f"tr_c_{i}")

# (4) 특별 이벤트 레버 (누락 방지)
with st.sidebar.expander("🚀 특별 이벤트 추가/수정", expanded=True):
    if st.sidebar.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "새 이벤트", "year": 2025, "cost": 0})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"이벤트명 {i}", ev['name'], key=f"ev_n_{i}")
        col_y, col_c = st.columns(2)
        ev['year'] = col_y.number_input(f"발생년도 {i}", 2025, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = col_c.number_input(f"비용(만원) {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

# (5) 자산 및 세금 기본 가정
with st.sidebar.expander("📈 자산/세금 기본 가정", expanded=False):
    re_init = st.number_input("현재 부동산(만원)", value=140000)
    re_gr = st.number_input("부동산 상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자자산(만원)", value=10000)
    inv_gr = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액(만원)", value=60000)
    debt_r = st.number_input("대출 금리(%)", value=3.9) / 100
    tax_base_ratio = st.number_input("공시지가비율(%)", value=60.0) / 100
    tax_rate = st.number_input("보유세율(%)", value=0.2) / 100

# --- 4. 시뮬레이션 엔진 (만원 단위 계산 -> 억원 저장) ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 500, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        events_this_year = []

        # (1) 수입 (연봉 세후 + 연금)
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0 # 상여포함 약 13회분
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pension = 0
        if h_age >= h_p_age: pension += (h_p_amt * 12)
        if w_age >= w_p_age: pension += (w_p_amt * 12)
        # 중요: 이 변수명이 '연수입'으로 저장되어야 에러가 안 납니다.
        yearly_total_income = inc_h + inc_w + pension

        # (2) 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']
                c_debt += tr['use_debt']
                c_cash -= tr['use_cash']
                c_re = tr['new_price']
                events_this_year.append(f"🏠{tr['new_price']//10000}억 매수")

        # (3) 양육비 계산
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: events_this_year.append(f"👶{kid['name']} 탄생")
            if 0 <= ka <= 7: k_total += kid['costs'][0]*12
            elif 8 <= ka <= 13: k_total += kid['costs'][1]*12
            elif 14 <= ka <= 16: k_total += kid['costs'][2]*12
            elif 17 <= ka <= 19: k_total += kid['costs'][3]*12
            elif 20 <= ka <= 23: k_total += kid['costs'][4]*12

        # (4) 지출 (생활비4.8천 + 보유세 + 이자 + 이벤트)
        tax = (c_re * tax_base_ratio) * tax_rate
        interest = c_debt * debt_r
        ev_cost = 0
        for ev in st.session_state.events:
            if year == ev['year']:
                ev_cost += ev['cost']
                events_this_year.append(f"🚀{ev['name']}")

        # (5) 자산 업데이트
        net_flow = yearly_total_income - (4800 + k_total + tax + interest + ev_cost)
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_flow) * (1 + inv_gr)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "총자산": round(total_asset / 10000, 2),
            "순자산": round((total_asset - c_debt) / 10000, 2),
            "부동산": round(c_re / 10000, 2),
            "금융자산": round(c_inv / 10000, 2),
            "예금": round(c_cash / 10000, 2),
            "부채": round(c_debt / 10000, 2),
            "연수입": round(yearly_total_income / 10000, 2),
            "이벤트": " ".join(events_this_year)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    
    return pd.DataFrame(res)

df = run_simulation()

# --- 5. 결과 시각화 (억 단위 출력) ---
tabs = st.tabs(["📊 자산 시뮬레이션", "📋 상세 데이터 표"])

with tabs[0]:
    # 기간 필터
    p_choice = st.radio("시뮬레이션 조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True)
    p_val = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}[p_choice]
    sub_df = df.head(p_val)

    # [메인 그래프] 총자산 & 순자산 & 부채
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산(억)", fill='tozeroy', 
                             line=dict(color='#10b981', width=5), hovertemplate='%{y:.2f}억'))
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산(억)", 
                             line=dict(color='#3b82f6', width=2, dash='dot'), hovertemplate='%{y:.2f}억'))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="대출(억)", 
                         marker_color='#ef4444', opacity=0.3, hovertemplate='%{y:.2f}억'))
    
    # 이벤트 Annotation (차트 위에 표시)
    for _, row in sub_df.iterrows():
        if row["이벤트"]:
            fig.add_annotation(x=row["연도"], y=row["총자산"], text=f"<b>{row['이벤트']}</b>", 
                               showarrow=True, arrowhead=2, bgcolor="#fbbf24", bordercolor="#d97706", font=dict(size=12))

    fig.update_layout(title=f"우리 가족 자산 로드맵 ({p_choice})", hovermode="x unified", height=550, 
                      template="plotly_white", margin=dict(l=20, r=20, t=80, b=20),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # [4분할 상세 막대 그래프] 1/4 크기
    st.markdown("### 🔍 항목별 세부 추이 (단위: 억원)")
    c1, c2, c3, c4 = st.columns(4)
    
    def draw_bar(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], name=title, marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=15, color="#475569")), 
                        height=280, template="plotly_white", margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        return f

    c1.plotly_chart(draw_bar(sub_df, "부동산", "🏠 부동산", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub_df, "금융자산", "📈 금융자산", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub_df, "부채", "📉 대출부채", "#f43f5e"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub_df, "연수입", "💵 연수입", "#10b981"), use_container_width=True)

with tabs[1]:
    st.subheader("📋 전체 시뮬레이션 상세 시트 (단위: 억원)")
    # 요청하신 연도별 총자산/순자산/부채/수입/이벤트 총망라 표
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
