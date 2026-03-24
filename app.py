import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정 및 전문적인 UI 테마 적용
st.set_page_config(page_title="Family Financial Plan 2026", layout="wide", initial_sidebar_state="expanded")

# 사용자 정의 CSS (디자인 강화)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #f4f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; border: 1px solid #e1e4e8; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Asset Roadmap")
st.markdown("남편(95년생) & 아내(94년생)를 위한 **최종 통합 재무 대시보드**")

# --- 세션 스테이트 초기화 (데이터 무결성 유지) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "use_inv": 5.0, "use_debt": 5.0, "use_cash": 1.0}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]

# --- 사이드바: 모든 오더를 총망라한 설정창 ---
st.sidebar.header("📋 가정 사항 설정")

# (1) 부부 정보 (수치 직접 입력)
with st.sidebar.expander("👤 부부 급여 및 은퇴", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("월급(세후/만)", value=550)
        h_inc = st.number_input("인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("은퇴나이", value=55)
        h_p_age = st.number_input("연금시작나이", value=65)
        h_p_amt = st.number_input("연금액(월/만)", value=150)
    with w_tab:
        w_sal = st.number_input("월급(세후/만)", value=500)
        w_inc = st.number_input("인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55)
        w_p_age = st.number_input("아내 연금시작나이", value=65)
        w_p_amt = st.number_input("아내 연금액(월/만)", value=130)

# (2) 자녀별 개별 양육비 레버
with st.sidebar.expander("👶 자녀별 시기별 양육비", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 상세 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 출생년도", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아비", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등비", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등비", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등비", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학비", value=kid['costs'][4], key=f"kc4_{i}")

# (3) 부동산 갈아타기 (자금 출처 직접 입력)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=False):
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 30.0, "use_inv": 0.0, "use_debt": 0.0, "use_cash": 0.0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**갈아타기 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도 {i}", 2025, 2090, tr['year'], key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"목표가(억) {i}", 0.0, 100.0, tr['new_price'], key=f"tr_p_{i}")
        tr['use_inv'] = st.number_input(f"금융자산활용(억) {i}", value=tr['use_inv'], key=f"tr_inv_{i}")
        tr['use_debt'] = st.number_input(f"추가대출(억) {i}", value=tr['use_debt'], key=f"tr_debt_{i}")
        tr['use_cash'] = st.number_input(f"예금활용(억) {i}", value=tr['use_cash'], key=f"tr_cash_{i}")

# (4) 특별 이벤트 레버 (누락 없이 포함)
with st.sidebar.expander("🚀 특별 이벤트 설정", expanded=False):
    if st.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "새 이벤트", "year": 2025, "cost": 0.0})
    for i, ev in enumerate(st.session_state.events):
        ev['name'] = st.text_input(f"이벤트명 {i}", ev['name'], key=f"ev_n_{i}")
        c1, c2 = st.columns(2)
        ev['year'] = c1.number_input(f"연도 {i}", 2025, 2095, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = c2.number_input(f"비용(억) {i}", 0.0, 100.0, ev['cost'], key=f"ev_c_{i}")

# (5) 기본 자산 및 세금 가정
with st.sidebar.expander("📈 기본 자산 & 세금 가정", expanded=False):
    re_init = st.number_input("현재 부동산(억)", value=14.0)
    re_gr = st.number_input("부동산 상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자자산(억)", value=1.0)
    inv_gr = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액(억)", value=6.0)
    debt_r = st.number_input("대출 금리(%)", value=4.0) / 100
    tax_base_ratio = st.number_input("공시지가 반영률(%)", value=60.0) / 100
    holding_tax_rate = st.number_input("보유세율(%)", value=0.2) / 100

# --- 시뮬레이션 엔진 (에러 방지용 데이터 구조 확립) ---
def run_simulation():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        events_this_year = []

        # 1. 수입 (급여 + 상여15% + 연금)
        inc_h = (c_h_sal * 12 * 1.15) / 10000 if h_age <= h_ret else 0
        inc_w = (c_w_sal * 12 * 1.15) / 10000 if w_age <= w_ret else 0
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
                events_this_year.append(f"🏠{tr['new_price']}억 매수")

        # 3. 양육비 계산 (자녀별 독립 루프)
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: events_this_year.append(f"👶{kid['name']} 탄생")
            if 0 <= ka <= 7: k_total += kid['costs'][0]*12/10000
            elif 8 <= ka <= 13: k_total += kid['costs'][1]*12/10000
            elif 14 <= ka <= 16: k_total += kid['costs'][2]*12/10000
            elif 17 <= ka <= 19: k_total += kid['costs'][3]*12/10000
            elif 20 <= ka <= 23: k_total += kid['costs'][4]*12/10000

        # 4. 지출 (세금 + 대출이자 + 특별이벤트)
        tax = (c_re * tax_base_ratio) * holding_tax_rate
        interest = c_debt * debt_r
        ev_total = 0
        for ev in st.session_state.events:
            if year == ev['year']:
                ev_total += ev['cost']
                events_text = f"🚀{ev['name']}"
                if events_text not in events_this_year: events_this_year.append(events_text)

        # 5. 자산 흐름 업데이트 (잉여금은 금융자산으로)
        net_cashflow = y_income - (4.2 + k_total + tax + interest + ev_total) # 4.2억: 연간기본생활비 가정
        c_re *= (1 + re_gr)
        c_inv = (c_inv + net_cashflow) * (1 + inv_gr)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "총자산": total_asset, "순자산": total_asset - c_debt,
            "부동산": c_re, "금융자산": c_inv, "예금": c_cash, "부채": c_debt,
            "연수입": y_income, "이벤트": " ".join(events_this_year)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_simulation()

# --- 대시보드 메인 화면 ---
st.subheader("📈 자산 성장 시뮬레이션")
period_tab = st.tabs(["5년", "10년", "20년", "30년", "전체"])
p_map = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}

for i, tab in enumerate(period_tab):
    with tab:
        p_key = list(p_map.keys())[i]
        sub_df = df.head(p_map[p_key])
        
        # [메인 그래프] 총자산, 순자산, 부채
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산(억원)", fill='tozeroy', 
                                 line=dict(color='#00b894', width=4), hovertemplate='%{y:.2f}억'))
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산(억원)", 
                                 line=dict(color='#0984e3', width=2, dash='dot'), hovertemplate='%{y:.2f}억'))
        fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="대출부채(억원)", 
                             marker_color='#d63031', opacity=0.3, hovertemplate='%{y:.2f}억'))
        
        # 이벤트 Annotation (텍스트 크게)
        for _, row in sub_df.iterrows():
            if row["이벤트"]:
                fig.add_annotation(x=row["연도"], y=row["총자산"], text=f"<b>{row['이벤트']}</b>", 
                                   showarrow=True, arrowhead=2, bgcolor="#ffeaa7", font=dict(size=12))

        fig.update_layout(hovermode="x unified", height=500, margin=dict(l=20, r=20, t=50, b=20),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        # [4분할 상세 막대 그래프] 1/4 크기
        st.markdown("#### 🔍 항목별 세부 추이 분석")
        c1, c2, c3, c4 = st.columns(4)
        
        def make_bar(data, col, title, color):
            f = go.Figure(go.Bar(x=data["연도"], y=data[col], name=title, marker_color=color))
            f.update_layout(title=dict(text=title, font=dict(size=14)), height=250, 
                            margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
            return f

        c1.plotly_chart(make_bar(sub_df, "부동산", "🏠 부동산 가액", "#e17055"), use_container_width=True)
        c2.plotly_chart(make_bar(sub_df, "금융자산", "📈 금융투자 잔액", "#6c5ce7"), use_container_width=True)
        c3.plotly_chart(make_bar(sub_df, "부채", "📉 대출 잔액", "#d63031"), use_container_width=True)
        c4.plotly_chart(make_bar(sub_df, "연수입", "💵 연간 총수입", "#00b894"), use_container_width=True)

st.divider()
st.subheader("📋 연도별 상세 데이터 시트")
st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
