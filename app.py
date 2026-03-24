import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인 고도화
st.set_page_config(page_title="Family Wealth Master", layout="wide")

# 가독성을 위한 CSS 주입 (글씨체 확대 및 카드 디자인)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 18px !important; }
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 700; background-color: #3b82f6; color: white; height: 3.5rem; font-size: 20px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 20px !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Family Financial Master Plan")
st.markdown("남편(95) & 아내(94)를 위한 **최고급 통합 자산 시뮬레이터**")
st.info("💡 **좌측 설정**: 만원 단위 | **우측 결과**: 자산(억원), 월 지출/흐름(만원)")

# --- 2. 데이터 영속성 (세션 스테이트 초기화) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 250000, "use_inv": 50000, "use_debt": 50000, "use_cash": 10000}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 6000}]

# --- 3. 사이드바: 정밀 레버 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 환경 설정")

with st.sidebar.expander("📅 시뮬레이션 기간", expanded=True):
    start_year = st.number_input("시작 연도", value=2026, min_value=2024, max_value=2050)
    end_year = 2095

with st.sidebar.expander("👤 부부 소득 & 은퇴/연금", expanded=False):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    with h_tab:
        h_sal = st.number_input("남편 월급", value=830); h_inc = st.number_input("남편 인상률(%)", value=3.0, step=0.1) / 100
        h_ret = st.number_input("남편 은퇴나이", value=55); h_p_age = st.number_input("남편 연금나이", value=65); h_p_amt = st.number_input("예상연금", value=150)
    with w_tab:
        w_sal = st.number_input("아내 월급", value=500); w_inc = st.number_input("아내 인상률(%)", value=3.0, step=0.1) / 100
        w_ret = st.number_input("아내 은퇴나이", value=55); w_p_age = st.number_input("아내 연금나이", value=65); w_p_amt = st.number_input("예상연금", value=130)

with st.sidebar.expander("💸 생활비 및 인상률", expanded=True):
    living_monthly_start = st.number_input(f"{start_year}년 기준 월 생활비", value=400)
    living_growth = st.number_input("생활비 연간 인상률(%)", value=2.0, step=0.1) / 100

with st.sidebar.expander("👶 자녀별 양육비 상세", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 탄생년", 2024, 2050, kid['birth'], key=f"kb_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학", value=kid['costs'][4], key=f"kc4_{i}")

with st.sidebar.expander("🔄 부동산 갈아타기 전략", expanded=False):
    re_init_val = st.sidebar.number_input("현재 부동산", value=140000, key="re_init_s")
    re_gr_rate = st.sidebar.number_input("부동산 상승률(%)", value=4.0, key="re_gr_s") / 100
    if st.button("➕ 갈아타기 계획 추가"):
        st.session_state.re_trades.append({"year": 2035, "new_price": 300000, "use_inv": 0, "use_debt": 0, "use_cash": 0})
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**🏠 시나리오 #{i+1}**")
        tr['year'] = st.number_input(f"매수년도", start_year, end_year, tr['year'], key=f"tr_y_{i}")
        est_sale = re_init_val * ((1 + re_gr_rate)**(max(0, tr['year'] - start_year))) * 0.95
        st.write(f"👉 예상 매각 대금(세후): **{est_sale/10000:.2f} 억원**")
        tr['new_price'] = st.number_input(f"새 아파트 매수가", 0, 1000000, tr['new_price'], key=f"tr_p_{i}")
        gap = tr['new_price'] - est_sale
        st.warning(f"⚠️ 추가 Gap: **{gap/10000:.2f} 억원**")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융자산 활용", value=tr['use_inv'], key=f"tr_i_{i}")
        tr['use_debt'] = c2.number_input(f"대출 활용", value=tr['use_debt'], key=f"tr_d_{i}")
        tr['use_cash'] = c3.number_input(f"예금 활용", value=tr['use_cash'], key=f"tr_c_{i}")

with st.sidebar.expander("🚀 특별 이벤트 설정", expanded=False):
    if st.button("➕ 이벤트 추가"):
        st.session_state.events.append({"name": "이벤트", "year": 2030, "cost": 0})
    for i, ev in enumerate(st.session_state.events):
        e1, e2, e3 = st.columns([2,1,1])
        ev['name'] = e1.text_input(f"명칭", ev['name'], key=f"ev_n_{i}")
        ev['year'] = e2.number_input(f"년도", start_year, end_year, ev['year'], key=f"ev_y_{i}")
        ev['cost'] = e3.number_input(f"비용", 0, 1000000, ev['cost'], key=f"ev_c_{i}")

with st.sidebar.expander("📈 기타 기본 가정", expanded=False):
    inv_init = st.number_input("현재 투자자산", value=10000); inv_gr = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액", value=60000); debt_r = st.number_input("대출 금리(%)", value=3.9) / 100
    debt_term = st.number_input("대출 상환 기간(년)", value=30)
    tax_base = st.number_input("공시지가비율(%)", value=60.0) / 100; tax_r = st.number_input("보유세율(%)", value=0.2) / 100

# --- 4. 시뮬레이션 엔진 ---
def run_sim():
    rows = []
    c_re, c_inv, c_cash, c_debt = re_init_val, inv_init, 1000, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(start_year, end_year + 1):
        h_age, w_age = year - 1995, year - 1994
        ev_list = []

        # (1) 수입
        inc_h = (c_h_sal * 13) if h_age <= h_ret else 0
        inc_w = (c_w_sal * 13) if w_age <= w_ret else 0
        pen = (h_p_amt * 12 if h_age >= h_p_age else 0) + (w_p_amt * 12 if w_age >= w_p_age else 0)
        total_income_annual = inc_h + inc_w + pension

        # (2) 부동산 거래
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                c_inv -= tr['use_inv']; c_debt += tr['use_debt']; c_cash -= tr['use_cash']; c_re = tr['new_price']
                ev_list.append(f"🏠{tr['new_price']//10000}억 갈아타기")

        # (3) 양육비
        k_cost_annual = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if year == kid['birth']: ev_list.append(f"👶{kid['name']} 탄생")
            if 0<=ka<=7: k_cost_annual += kid['costs'][0]*12
            elif 8<=ka<=13: k_cost_annual += kid['costs'][1]*12
            elif 14<=ka<=16: k_cost_annual += kid['costs'][2]*12
            elif 17<=ka<=19: k_cost_annual += kid['costs'][3]*12
            elif 20<=ka<=23: k_cost_annual += kid['costs'][4]*12

        # (4) 지출 상세 (월 단위)
        curr_living_monthly = living_monthly_start * ((1 + living_growth)**(year - start_year))
        tax_monthly = ((c_re * tax_base) * tax_r) / 12
        principal_annual = (debt_init / debt_term) if (c_debt > 0 and year < start_year + debt_term) else 0
        loan_pay_monthly = (c_debt * debt_r + principal_annual) / 12
        
        ev_cost_annual = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        for ev in st.session_state.events:
            if year == ev['year']: ev_list.append(f"🚀{ev['name']}")

        # (5) 자산 업데이트 및 순현금흐름
        total_expense_annual = (curr_living_monthly * 12) + k_cost_annual + (tax_monthly * 12) + (loan_pay_monthly * 12) + ev_cost_annual
        net_cf_annual = total_income_annual - total_expense_annual
        
        c_re *= (1 + re_gr_rate)
        c_inv = (c_inv + net_cf_annual) * (1 + inv_gr)
        c_debt = max(0, c_debt - principal_annual)
        savings_rate = (net_cf_annual / total_income_annual * 100) if total_income_annual > 0 else 0
        
        total_asset = c_re + c_inv + c_cash
        
        # 에러 방지: 모든 컬럼명을 영어로 정의
        rows.append({
            "year": year, "age": f"{h_age}/{w_age}",
            "net_asset": round((total_asset - c_debt)/10000, 2), 
            "debt_asset": round(c_debt/10000, 2), 
            "total_asset": round(total_asset/10000, 2),
            "re_asset": round(c_re/10000, 2), 
            "inv_asset": round(c_inv/10000, 2), 
            "income_annual": round(total_income_annual/10000, 2),
            "m_living": round(curr_living_monthly, 0),
            "m_loan": round(loan_pay_monthly, 0),
            "m_tax": round(tax_monthly, 0),
            "m_kid": round(k_cost_annual/12, 0),
            "m_event": round(ev_cost_annual/12, 0),
            "m_net_flow": round(net_cf_annual/12, 0),
            "savings_rate": round(savings_rate, 1),
            "event_summary": ", ".join(ev_list) if ev_list else "없음"
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(rows)

df = run_sim()

# --- 5. 시각화 (Hover UI 및 큰 글씨 디자인) ---
st.subheader("📈 자산 및 지출 성장 로드맵")
t1, t2 = st.tabs(["📉 자산 차트 분석", "📑 상세 데이터 총망라"])

with t1:
    p = st.radio("시뮬레이션 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4)
    p_len = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":len(df)}[p]
    sub = df.head(p_len)

    # [메인] 누적 막대 차트
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["year"], y=sub["net_asset"], name="순자산(억)", marker_color='#10b981', 
                         customdata=sub[["total_asset", "age", "m_net_flow", "event_summary", "m_living", "m_loan", "m_tax", "m_kid", "savings_rate"]],
                         hovertemplate="<span style='font-size:22px'><b>%{x}년 (%{customdata[1]})</b></span><br>" + 
                                       "순자산: <span style='color:#10b981; font-size:20px'><b>%{y}억</b></span> | " + 
                                       "총자산: <b>%{customdata[0]}억</b><br>" + 
                                       "월 순현금: <span style='color:#3b82f6'><b>%{customdata[2]:,}만</b></span> (저축률 %{customdata[8]}%)<br><br>" +
                                       "<b>[월 지출 상세]</b><br>" +
                                       "• 생활비: %{customdata[4]:,}만<br>• 원리금: %{customdata[5]:,}만<br>• 세금: %{customdata[6]:,}만<br>• 양육비: %{customdata[7]:,}만<br>" +
                                       "• 이벤트: <b>%{customdata[3]}</b><extra></extra>"))
    fig.add_trace(go.Bar(x=sub["year"], y=sub["debt_asset"], name="부채(억)", marker_color='#ef4444', 
                         customdata=sub[["total_asset", "age", "m_net_flow", "event_summary"]],
                         hovertemplate="부채 잔액: %{y}억<extra></extra>"))
    
    fig.update_layout(barmode='stack', hovermode="x unified", height=650, template="plotly_white", 
                      hoverlabel=dict(bgcolor="white", font_size=18, font_family="Noto Sans KR"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=16)))
    st.plotly_chart(fig, use_container_width=True)

    # [하단 4분할 막대]
    st.markdown("### 🔍 항목별 지표 상세 (1/4)")
    c1, c2, c3, c4 = st.columns(4)
    def draw_bar(data, col, title, color, unit="억"):
        f = go.Figure(go.Bar(x=data["year"], y=data[col], marker_color=color, customdata=data["event_summary"],
                             hovertemplate=f"<b>%{{x}}년</b><br>수치: %{{y}} {unit}<br>이벤트: %{{customdata}}<extra></extra>"))
        f.update_layout(title=dict(text=title, font=dict(size=20)), height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    
    c1.plotly_chart(draw_bar(sub, "re_asset", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_bar(sub, "inv_asset", "📈 금융자산(억)", "#8b5cf6"), use_container_width=True)
    
    # 지출 상세 (누적 막대)
    fig_spend = go.Figure()
    for col, name, color in [("m_living", "생활비", "#3498db"), ("m_loan", "원리금", "#e67e22"), ("m_tax", "세금", "#95a5a6"), ("m_kid", "양육비", "#f1c40f"), ("m_event", "이벤트", "#9b59b6")]:
        fig_spend.add_trace(go.Bar(x=sub["year"], y=sub[col], name=name, marker_color=color))
    fig_spend.update_layout(title=dict(text="💸 월 지출 상세(만)", font=dict(size=20)), barmode='stack', height=320, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white", showlegend=False)
    c3.plotly_chart(fig_spend, use_container_width=True)
    
    c4.plotly_chart(draw_bar(sub, "m_net_flow", "💰 월 순현금흐름(만)", "#10b981", "만"), use_container_width=True)

with t2:
    st.subheader("📋 전 생애 재무 데이터 시트 (총망라)")
    final_table = df.rename(columns={
        "year": "연도", "age": "나이(남/여)", "net_asset": "순자산(억)", "debt_asset": "부채(억)", "total_asset": "총자산(억)",
        "re_asset": "부동산(억)", "inv_asset": "금융자산(억)", "income_annual": "연수입(억)", 
        "m_living": "생활비(만)", "m_loan": "원리금(만)", "m_net_flow": "월순현금흐름(만)", "savings_rate": "저축률(%)", "event_summary": "이벤트"
    })
    st.dataframe(final_table.style.format({
        "순자산(억)": "{:.2f}", "부채(억)": "{:.2f}", "총자산(억)": "{:.2f}",
        "부동산(억)": "{:.2f}", "금융자산(억)": "{:.2f}", "연수입(억)": "{:.2f}",
        "생활비(만)": "{:,.0f}", "원리금(만)": "{:,.0f}", "월순현금흐름(만)": "{:,.0f}", "저축률(%)": "{:.1f}"
    }), use_container_width=True)
