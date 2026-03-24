import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 프리미엄 테마
st.set_page_config(page_title="Family Wealth Roadmap", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; margin-bottom: 10px; border: 1px solid #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; background-color: #3b82f6; color: white; border: none; height: 3rem;}
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset Roadmap (2025-2095)")
st.info("💡 **입력(왼쪽)**: 만원 단위 | **결과(차트)**: 자산은 '억원', 월 지출은 '만원' 단위입니다.")

# --- 2. 데이터 유지 (세션 스테이트) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 모든 레버 통합 (단위: 만원) ---
st.sidebar.header("⚙️ 시뮬레이션 설정 (만원)")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 급여 및 은퇴/연금", expanded=False):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830); h_inc = st.number_input("남편 인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55); h_p_age = st.number_input("남편 연금나이", value=65); h_p_amt = st.number_input("남편 예상연금", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500); w_inc = st.number_input("아내 인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55); w_p_age = st.number_input("아내 연금나이", value=65); w_p_amt = st.number_input("아내 예상연금", value=130)

# (2) 생활비 가정 (신규 오더)
with st.sidebar.expander("💸 연간 생활비 설정", expanded=True):
    living_monthly_2025 = st.number_input("2025년 월 생활비(만원)", value=400)
    living_growth = st.number_input("생활비 연간 인상률(%)", value=2.0, step=0.1) / 100

# (3) 자녀별 양육비
with st.sidebar.expander("👶 자녀별 양육비 상세", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 탄생년도", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학", value=kid['costs'][4], key=f"kc4_{i}")

# (4) 부동산 갈아타기 (자금 출처별 상세)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.sidebar.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        tr['year'] = st.number_input(f"매수년 {i}", 2025, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"매수가 {i}", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        tr['use_inv'] = st.number_input(f"금융자산활용 {i}", value=tr['use_inv'], key=f"tr_i_{i}")
        tr['use_debt'] = st.number_input(f"추가대출 {i}", value=tr['use_debt'], key=f"tr_d_{i}")
        tr['use_cash'] = st.number_input(f"예금활용 {i}", value=tr['use_cash'], key=f"tr_c_{i}")

# (5) 특별 이벤트 레버
with st.sidebar.expander("🚀 특별 이벤트 레버", expanded=False):
    if st.sidebar.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "이벤트", "year": 2025, "cost": 0})
    for i, ev in enumerate(st.session_state.events):
        e1, e2, e3 = st.columns([2,1,1])
        ev['name'] = e1.text_input(f"명칭 {i}", ev['name'], key=f"ev_n_{i}")
        ev['year'] = e2.number_input(f"년도 {i}", 2025, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = e3.number_input(f"비용 {i}", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

# (6) 기본 자산 & 세금
with st.sidebar.expander("📈 기본 자산 & 세금 가정", expanded=False):
    re_init = st.number_input("현재 부동산", value=140000); re_gr = st.number_input("부동산 상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자자산", value=10000); inv_gr = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액", value=60000); debt_r = st.number_input("대출 금리(%)", value=3.9) / 100
    debt_term = st.number_input("상환 기간(년)", value=30)
    tax_base = st.number_input("공시지가비율(%)", value=60.0) / 100; tax_r = st.number_input("보유세율(%)", value=0.2) / 100

# --- 4. 시뮬레이션 엔진 (KeyError 방지형) ---
def run_sim():
    rows = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []

        # (1) 수입
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pen = (h_p_amt * 12 if h_age >= h_p_age else 0) + (w_p_amt * 12 if w_age >= w_p_age else 0)
        total_income = inc_h + inc_w + pen

        # (2) 부동산 거래
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 매수")

        # (3) 양육비
        k_cost = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_cost += kid['costs'][0]*12
            elif 8<=ka<=13: k_cost += kid['costs'][1]*12
            elif 14<=ka<=16: k_cost += kid['costs'][2]*12
            elif 17<=ka<=19: k_cost += kid['costs'][3]*12
            elif 20<=ka<=23: k_cost += kid['costs'][4]*12

        # (4) 지출 (생활비 + 세금 + 원리금 + 이벤트)
        curr_living = (living_monthly_2025 * 12) * ((1 + living_growth)**(year - 2025))
        tax = (c_re * tax_base) * tax_r
        interest = c_debt * debt_r
        principal = (debt_init / debt_term) if (c_debt > 0 and year < 2025 + debt_term) else 0
        loan_pay = interest + principal
        
        ev_cost = 0
        for ev in st.session_state.events:
            if year == ev['year']:
                ev_cost += ev['cost']
                ev_list.append(f"🚀{ev['name']} ({ev['cost']}만)")

        # (5) 자산 업데이트
        net_cf = total_income - (curr_living + k_cost + tax + loan_pay + ev_cost)
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_cf) * (1 + inv_gr)
        c_debt = max(0, c_debt - principal)
        
        total_asset = c_re + c_inv + c_cash
        rows.append({
            "year": year, "age": f"{h_age}/{w_age}",
            "net": round((total_asset - c_debt)/10000, 2), 
            "debt": round(c_debt/10000, 2), 
            "total": round(total_asset/10000, 2),
            "re": round(c_re/10000, 2), 
            "inv": round(c_inv/10000, 2), 
            "income": round(total_income/10000, 2),
            "spend": round((curr_living + k_cost + tax + loan_pay + ev_cost)/12, 0),
            "event": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(rows)

df = run_sim()

# --- 5. 시각화 (프리미엄 UI) ---
st.subheader("📊 자산 성장 로드맵")
t1, t2 = st.tabs(["📉 자산 차트", "📑 데이터 상세"])

with t1:
    p = st.radio("기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4)
    p_len = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}[p]
    sub = df.head(p_len)

    # [메인 누적 막대]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net"], name="순자산(억)", marker_color='#10b981', 
                         customdata=sub[["total", "age", "spend", "event"]],
                         hovertemplate="<b>%{x}년 (%{customdata[1]})</b><br>순자산: %{y}억<br>총자산: %{customdata[0]}억<br>월평균지출: %{customdata[2]:,}만<br>이벤트: %{customdata[3]}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt"], name="부채(억)", marker_color='#ef4444', 
                         customdata=sub[["total", "age", "spend", "event"]],
                         hovertemplate="부채: %{y}억<extra></extra>"))
    
    fig.update_layout(barmode='stack', hovermode="x unified", height=500, template="plotly_white", 
                      hoverlabel=dict(bgcolor="white", font_size=16),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # [4분할 막대]
    st.markdown("#### 🔍 세부 지표 추이")
    c1, c2, c3, c4 = st.columns(4)
    def draw(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color, customdata=data["event"],
                             hovertemplate=f"값: %{{y}} {unit}<br>이벤트: %{{customdata}}<extra></extra>"))
        f.update_layout(title=title, height=250, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white", hoverlabel=dict(font_size=14))
        return f
    
    c1.plotly_chart(draw(sub, "re", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw(sub, "inv", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw(sub, "spend", "💸 월 지출(만)", "#f43f5e", "만"), use_container_width=True)
    c4.plotly_chart(draw(sub, "income", "💵 연 수입(억)", "#10b981"), use_container_width=True)

with t2:
    st.subheader("📋 전체 기간 재무 데이터 (단위: 억/만)")
    # 한글 컬럼으로 변환하여 표 출력
    final_table = df.rename(columns={
        "year": "연도", "age": "나이(남/여)", "net": "순자산(억)", "debt": "부채(억)", "total": "총자산(억)",
        "re": "부동산(억)", "inv": "금융자산(억)", "income": "연수입(억)", "spend": "월지출(만)", "event": "이벤트"
    })
    st.dataframe(final_table.style.format({
        "순자산(억)": "{:.2f}", "부채(억)": "{:.2f}", "총자산(억)": "{:.2f}",
        "부동산(억)": "{:.2f}", "금융자산(억)": "{:.2f}", "연수입(억)": "{:.2f}", "월지출(만)": "{:,.0f}"
    }), use_container_width=True)
