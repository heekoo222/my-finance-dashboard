import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="우리집 통합 재무 시뮬레이터", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 우리 가족 통합 재무 시뮬레이터")
st.info("💡 사이드바에서 가정을 수정하면 차트가 즉시 업데이트됩니다.")

# --- 세션 스테이트 (데이터 유지) ---
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "use_inv": 5.0, "use_debt": 5.0, "use_cash": 1.0}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]

# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 시뮬레이션 설정")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 수입 & 은퇴", expanded=False):
    h_sal = st.number_input("남편 월급(만)", value=550)
    h_inc = st.number_input("남편 인상률(%)", value=3.0) / 100
    h_ret = st.number_input("남편 은퇴나이", value=55)
    w_sal = st.number_input("아내 월급(만)", value=500)
    w_inc = st.number_input("아내 인상률(%)", value=3.0) / 100
    w_ret = st.number_input("아내 은퇴나이", value=55)

# (2) 부동산 갈아타기 (자금 출처 직접 입력)
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=True):
    if st.sidebar.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2040, "new_price": 35.0, "use_inv": 0.0, "use_debt": 0.0, "use_cash": 0.0})
    
    for i, trade in enumerate(st.session_state.re_trades):
        st.markdown(f"**갈아타기 #{i+1}**")
        trade['year'] = st.number_input(f"매수년도", 2025, 2095, trade['year'], key=f"tr_y_{i}")
        trade['new_price'] = st.number_input(f"목표가(억)", 0.0, 100.0, trade['new_price'], key=f"tr_p_{i}")
        c1, c2, c3 = st.columns(3)
        trade['use_inv'] = c1.number_input("금융자산 활용(억)", value=trade['use_inv'], key=f"tr_inv_{i}")
        trade['use_debt'] = c2.number_input("추가대출(억)", value=trade['use_debt'], key=f"tr_debt_{i}")
        trade['use_cash'] = c3.number_input("예금활용(억)", value=trade['use_cash'], key=f"tr_cash_{i}")

# (3) 자산 & 세금 초기값
with st.sidebar.expander("📈 자산 및 세금 기본값", expanded=False):
    re_init = st.number_input("현재 부동산(억)", value=14.0)
    re_growth = st.number_input("부동산 상승률(%)", value=4.0) / 100
    inv_init = st.number_input("현재 투자자산(억)", value=1.0)
    inv_growth = st.number_input("투자 수익률(%)", value=7.0) / 100
    debt_init = st.number_input("현재 대출잔액(억)", value=6.0)
    debt_rate = st.number_input("대출 금리(%)", value=4.0) / 100
    tax_base = st.number_input("공시지가 반영률(%)", value=60.0) / 100

# --- 시뮬레이션 엔진 ---
def run_sim():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        events = []

        # 1. 수입 (급여)
        inc = ((c_h_sal if h_age <= h_ret else 0) + (c_w_sal if w_age <= w_ret else 0)) * 13 / 10000 
        
        # 2. 갈아타기 처리
        for trade in st.session_state.re_trades:
            if year == trade['year']:
                c_inv -= trade['use_inv']
                c_debt += trade['use_debt']
                c_cash -= trade['use_cash']
                c_re = trade['new_price']
                events.append(f"🏠{trade['new_price']}억 매수")

        # 3. 지출
        tax = (c_re * tax_base) * 0.002 # 보유세 0.2% 가정
        interest = c_debt * debt_rate
        net_flow = inc - (4.0 + tax + interest) # 4.0은 연간 기본 생활비
        
        c_re *= (1 + re_growth)
        c_inv = (c_inv + net_flow) * (1 + inv_growth)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}",
            "순자산": total_asset - c_debt, "총자산": total_asset,
            "부채": c_debt, "부동산": c_re, "금융자산": c_inv, "예금": c_cash,
            "이벤트": " ".join(events)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

df = run_sim()

# --- 메인 대시보드 UI ---
tabs = st.tabs(["📊 통합 시뮬레이션", "📑 상세 데이터"])

with tabs[0]:
    # 기간 선택
    p_choice = st.radio("보기 기간 설정", ["5년", "10년", "20년", "30년", "전체"], horizontal=True)
    p_map = {"5년":5, "10년":10, "20년":20, "30년":30, "전체":71}
    sub_df = df.head(p_map[p_choice])

    # [메인 그래프] 총자산 & 순자산
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산(Net)", fill='tozeroy', 
                             line=dict(color='#2ecc71', width=4)))
    fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산(Total)", 
                             line=dict(color='#3498db', width=2, dash='dot')))
    
    # 이벤트 어노테이션 (가독성 증대)
    for _, row in sub_df.iterrows():
        if row["이벤트"]:
            fig.add_annotation(x=row["연도"], y=row["총자산"], text=f"<b>{row['이벤트']}</b>", 
                               showarrow=True, arrowhead=2, bgcolor="#ffeb3b", font=dict(size=14))

    fig.update_layout(title="연도별 자산 성장 추이 (단위: 억원)", hovermode="x unified",
                      font=dict(size=15), height=550, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # [세부 자산 막대 그래프]
    st.markdown("### 🔍 항목별 상세 분석 (부동산 / 금융자산 / 부채)")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        f1 = go.Figure(go.Bar(x=sub_df["연도"], y=sub_df["부동산"], name="부동산", marker_color='#e67e22'))
        f1.update_layout(title="부동산 가액", height=300, font=dict(size=12)); st.plotly_chart(f1, use_container_width=True)
    with c2:
        f2 = go.Figure(go.Bar(x=sub_df["연도"], y=sub_df["금융자산"], name="금융자산", marker_color='#9b59b6'))
        f2.update_layout(title="금융자산 잔액", height=300, font=dict(size=12)); st.plotly_chart(f2, use_container_width=True)
    with c3:
        f3 = go.Figure(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채", marker_color='#e74c3c'))
        f3.update_layout(title="대출 잔액", height=300, font=dict(size=12)); st.plotly_chart(f3, use_container_width=True)

with tabs[1]:
    st.subheader("📋 시뮬레이션 상세 수치 테이블")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
