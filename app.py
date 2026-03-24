import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 전문가용 UI 테마
st.set_page_config(page_title="Family Wealth Roadmap", layout="wide")

# UI 스타일 커스텀 (폰트 크기 및 색상 강조)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
    .main { background-color: #fcfcfc; }
    .stMetric { border-radius: 15px; border: 1px solid #eee; padding: 15px; background: white; }
    .stSidebar { background-color: #f8f9fa; border-right: 1px solid #eee; }
    h1 { color: #1e293b; font-weight: 800; letter-spacing: -1px; }
    div[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset Roadmap (2026-2095)")
st.markdown("남편(95) & 아내(94)의 전 생애 자산 흐름 시뮬레이션")

# --- 2. 데이터 영속성 (세션 스테이트) ---
# 기존에 요청하신 모든 레버(갈아타기, 자녀, 이벤트) 초기화
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "use_inv": 5.0, "use_debt": 5.0, "use_cash": 1.0}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]

# --- 3. 사이드바: 모든 레버 총망라 ---
st.sidebar.header("📋 생애 주기 설정")

# (1) 부부 소득 및 은퇴 (수치 직접 입력)
with st.sidebar.expander("👤 부부 급여 & 은퇴/연금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급(만)", value=550)
        h_inc = st.number_input("남편 인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55)
        h_p_age = st.number_input("남편 연금시작나이", value=65)
        h_p_amt = st.number_input("남편 연금액(월/만)", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급(만)", value=500)
        w_inc = st.number_input("아내 인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55)
        w_p_age = st.number_input("아내 연금시작나이", value=65)
        w_p_amt = st.number_input("아내 연금액(월/만)", value=130)

# (2) 자녀별 개별 양육비 레버
with st.sidebar.expander("👶 자녀별 시기별 양육비", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 상세 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 출생년도", 2024, 2050, kid['birth'], key=f"k_b_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아", value=kid['costs'][0], key=f"k0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등", value=kid['costs'][1], key=f"k1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등", value=kid['costs'][2], key=f"k2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등", value=kid['costs'][3], key=f"k3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학", value=kid['costs'][4], key=f"k4_{i}")

# (3) 부동산 갈아타기 (자금 출처 직접 입력)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 30.0, "use_inv": 0.0, "use_debt": 0.0, "use_cash": 0.0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**갈아타기 시나리오 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", 2025, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"매수가(억) {i}", 0.0, 100.0, tr['new_price'], key=f"tr_p_{i}")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융자산 활용 {i}", value=tr['use_inv'], key=f"tr_i_{i}")
        tr['use_debt'] = c2.number_input(f"대출 추가 {i}", value=tr['use_debt'], key=f"tr_d_{i}")
        tr['use_cash'] = c3.number_input(f"예금 활용 {i}", value=tr['use_cash'], key=f"tr_c_{i}")

# (4) 특별 이벤트 레버 (누락 방지)
with st.sidebar.expander("🚀 특별 이벤트 추가/수정", expanded=True):
    if st.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "신규 이벤트", "year": 2025, "cost": 0.0})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"이벤트명 {i}", ev['name'], key=f"ev_n_{i}")
        col_y, col_c = st.columns(2)
        ev['year'] = col_y.number_input(f"년도 {i}", 2025, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = col_c.number_input(f"비용(억) {i}", 0.0, 50.0, ev['cost'], key=f"ev_c_{i}")

# (5) 자산 및 세금 기본값
with st.sidebar.expander("📈 자산/세금 기본 가정", expanded=False):
    re_init = st.number_input("현재 부동산(억)", value=14.0)
    re_gr = st.number_input("부동산상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자(억)", value=1.0)
    inv_gr = st.number_input("투자수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액(억)", value=6.0)
    debt_r = st.number_input("대출 금리(%)", value=4.0) / 100
    tax_base_ratio = st.number_input("공시지가비율(%)", value=60.0) / 100
    holding_tax = st.number_input("보유세율(%)", value=0.2) / 100

# --- 4. 시뮬레이션 엔진 (에러 차단형) ---
def run_sim():
    results = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        current_event_text = []

        # (1) 수입 (급여 + 연금)
        inc_h = (c_h_sal * 12 * 1.15) / 10000 if h_age <= h_ret else 0
        inc_w = (c_w_sal * 12 * 1.15) / 10000 if w_age <= w_ret else 0
        pension = 0
        if h_age >= h_p_age: pension += (h_p_amt * 12) / 10000
        if w_age >= w_p_age: pension += (w_p_amt * 12) / 10000
        # 이 변수가 반드시 데이터프레임의 '연수입'이 됩니다.
        yearly_total_income = inc_h + inc_w + pension

        # (2) 부동산 갈아타기
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']
                c_debt += tr['use_debt']
                c_cash -= tr['use_cash']
                c_re = tr['new_price']
                current_event_text.append(f"🏠{tr['new_price']}억 갈아타기")

        # (3) 양육비 계산
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: current_event_text.append(f"👶{kid['name']} 탄생")
            if 0 <= ka <= 7: k_total += kid['costs'][0]*12/10000
            elif 8 <= ka <= 13: k_total += kid['costs'][1]*12/10000
            elif 14 <= ka <= 16: k_total += kid['costs'][2]*12/10000
            elif 17 <= ka <= 19: k_total += kid['costs'][3]*12/10000
            elif 20 <= ka <= 23: k_total += kid['costs'][4]*12/10000

        # (4) 지출 및 세금/이벤트
        tax = (c_re * tax_base_ratio) * holding_tax
        interest = c_debt * debt_r
        ev_cost = 0
        for ev in st.session_state.events:
            if year == ev['year']:
                ev_cost += ev['cost']
                current_event_text.append(f"🚀{ev['name']}")

        # (5) 최종 자산 반영
        net_cf = yearly_total_income - (4.5 + k_total + tax + interest + ev_cost) # 4.5억: 연생활비
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_cf) * (1 + inv_gr)
        
        total_a = c_re + c_inv + c_cash
        # 데이터프레임 컬럼명을 여기서 확정합니다.
        results.append({
            "연도": year, "나이": f"{h_age}/{w_age}", "총자산": total_a, "순자산": total_a - c_debt,
            "부동산": c_re, "금융자산": c_inv, "예금": c_cash, "부채": c_debt, 
            "연수입": yearly_total_income, "이벤트": " ".join(current_event_text)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(results)

df = run_sim()

# --- 5. 시각화 UI (디자이너급) ---
tabs = st.tabs(["📊 자산 시뮬레이션", "📋 상세 데이터 시트"])

with tabs[0]:
    # 기간 선택 (탭 위 상단 배치)
    p_choice = st.radio("시뮬레이션 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True)
    p_len = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}[p_choice]
    sub_df = df.head(p_len)

    # [메인 그래프] 총자산 & 순자산 & 부채
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산(Net)", fill='tozeroy', 
                             line=dict(color='#10b981', width=5), hovertemplate='%{y:.2f}억'))
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산(Total)", 
                             line=dict(color='#3b82f6', width=2, dash='dot'), hovertemplate='%{y:.2f}억'))
    fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="대출부채(Debt)", 
                         marker_color='#ef4444', opacity=0.3, hovertemplate='%{y:.2f}억'))
    
    # 이벤트 Annotation (눈에 띄게)
    for _, row in sub_df.iterrows():
        if row["이벤트"]:
            fig.add_annotation(x=row["연도"], y=row["총자산"], text=f"<b>{row['이벤트']}</b>", 
                               showarrow=True, arrowhead=2, bgcolor="#fbbf24", bordercolor="#d97706", font=dict(size=12))

    fig.update_layout(title=f"우리 가족 자산 로드맵 ({p_choice})", hovermode="x unified", height=550, 
                      template="plotly_white", font=dict(size=14, color="#334155"),
                      margin=dict(l=20, r=20, t=80, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # [4분할 상세 막대 그래프] 1/4 크기
    st.markdown("### 🔍 항목별 세부 추이 (막대)")
    c1, c2, c3, c4 = st.columns(4)
    
    def draw_bar(data, col_name, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col_name], name=title, marker_color=color))
        f.update_layout(title=dict(text=title, font=dict(size=15, color="#475569")), 
                        height=280, template="plotly_white", margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        return f

    # 여기서 '연수입' 컬럼을 안전하게 호출합니다.
    c1.plotly_chart(draw_bar(sub_df, "부동산", "🏠 부동산", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub_df, "금융자산", "📈 금융자산", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_bar(sub_df, "부채", "📉 부채", "#f43f5e"), use_container_width=True)
    c4.plotly_chart(draw_bar(sub_df, "연수입", "💵 연수입", "#10b981"), use_container_width=True)

with tabs[1]:
    st.subheader("📋 전체 시뮬레이션 상세 수치 (단위: 억원)")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
