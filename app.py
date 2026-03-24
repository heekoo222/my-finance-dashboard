import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="우리집 통합 재무 시뮬레이터", layout="wide")

st.title("👨‍👩‍👧‍👦 우리 가족 통합 재무 시뮬레이터 v2.2")
st.markdown("남편(95년생) & 아내(94년생)의 생애 주기별 자산 시뮬레이션")

# --- 세션 스테이트 초기화 (데이터 유지 및 에러 방지) ---
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "priority": ["금융자산", "대출", "예금"]}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]

# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 상세 설정")

# (1) 부부 정보
with st.sidebar.expander("👤 부부 수입 & 은퇴", expanded=False):
    col_h, col_w = st.tabs(["남편(95)", "아내(94)"])
    with col_h:
        h_sal = st.number_input("월급(만)", value=550, key="h_sal_input")
        h_inc = st.number_input("인상률(%)", value=3.0, key="h_inc_input") / 100
        h_ret = st.number_input("남편 은퇴나이", value=55, key="h_ret_input")
        h_p_age = st.number_input("남편 연금시작", value=65, key="h_page_input")
        h_p_amt = st.number_input("남편 연금(월/만)", value=150, key="h_pamt_input")
    with col_w:
        w_sal = st.number_input("월급(만)", value=500, key="w_sal_input")
        w_inc = st.number_input("인상률(%)", value=3.0, key="w_inc_input") / 100
        w_ret = st.number_input("아내 은퇴나이", value=55, key="w_ret_input")
        w_p_age = st.number_input("아내 연금시작", value=65, key="w_page_input")
        w_p_amt = st.number_input("아내 연금(월/만)", value=130, key="w_pamt_input")

# (2) 자녀별 개별 양육비 설정
with st.sidebar.expander("👶 자녀별 양육비 상세", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 출생년도", 2024, 2050, kid['birth'], key=f"k_birth_{i}")
        kid['costs'][0] = st.number_input(f"{kid['name']} 영유아비", value=kid['costs'][0], key=f"k_c0_{i}")
        kid['costs'][1] = st.number_input(f"{kid['name']} 초등비", value=kid['costs'][1], key=f"k_c1_{i}")
        kid['costs'][2] = st.number_input(f"{kid['name']} 중등비", value=kid['costs'][2], key=f"k_c2_{i}")
        kid['costs'][3] = st.number_input(f"{kid['name']} 고등비", value=kid['costs'][3], key=f"k_c3_{i}")
        kid['costs'][4] = st.number_input(f"{kid['name']} 대학비", value=kid['costs'][4], key=f"k_c4_{i}")

# (3) 부동산 갈아타기
with st.sidebar.expander("🔄 부동산 갈아타기 계획", expanded=True):
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2040, "new_price": 35.0, "priority": ["금융자산", "대출", "예금"]})
    for i, trade in enumerate(st.session_state.re_trades):
        trade['year'] = st.number_input(f"매수년도 {i+1}", 2025, 2095, trade['year'], key=f"trade_y_{i}")
        trade['new_price'] = st.number_input(f"매수가(억) {i+1}", 0.0, 100.0, trade['new_price'], key=f"trade_p_{i}")
        trade['priority'] = st.multiselect(f"자금순위 {i+1}", ["금융자산", "예금", "대출"], default=trade['priority'], key=f"trade_pr_{i}")

# (4) 초기 자산 & 세금
with st.sidebar.expander("📈 기본 자산 & 세금", expanded=False):
    re_init = st.number_input("초기부동산(억)", value=14.0)
    re_growth = st.number_input("부동산상승률(%)", value=4.0) / 100
    inv_init = st.number_input("초기투자(억)", value=1.0)
    inv_growth = st.number_input("투자수익률(%)", value=7.0) / 100
    debt_init = st.number_input("초기대출(억)", value=6.0)
    debt_rate = st.number_input("대출금리(%)", value=4.0) / 100
    tax_ratio = st.number_input("공시지가비율(%)", value=60.0) / 100
    tax_rate = st.number_input("보유세율(%)", value=0.2) / 100

# --- 시뮬레이션 엔진 ---
def run_sim():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        
        # 이벤트 텍스트 수집
        events_this_year = []
        for kid in st.session_state.kids:
            if year == kid['birth']: events_this_year.append(f"👶{kid['name']} 탄생")
        for trade in st.session_state.re_trades:
            if year == trade['year']: events_this_year.append(f"🏠{trade['new_price']}억 매수")
        
        # 1. 수입 (급여 + 연금)
        inc_h = (c_h_sal * 12 * 1.15) / 10000 if h_age <= h_ret else 0
        inc_w = (c_w_sal * 12 * 1.15) / 10000 if w_age <= w_ret else 0
        pension = 0
        if h_age >= h_p_age: pension += (h_p_amt * 12) / 10000
        if w_age >= w_p_age: pension += (w_p_amt * 12) / 10000
        total_inc = inc_h + inc_w + pension
        
        # 2. 갈아타기 처리
        for trade in st.session_state.re_trades:
            if year == trade['year']:
                gap = trade['new_price'] - (c_re * 0.98)
                for src in trade['priority']:
                    if gap <= 0: break
                    if src == "금융자산": use = min(c_inv, gap); c_inv -= use; gap -= use
                    elif src == "예금": use = min(c_cash, gap); c_cash -= use; gap -= use
                    elif src == "대출": c_debt += gap; gap = 0
                c_re = trade['new_price']

        # 3. 양육비 계산
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if 0 <= ka <= 7: k_total += kid['costs'][0]*12/10000
            elif 8 <= ka <= 13: k_total += kid['costs'][1]*12/10000
            elif 14 <= ka <= 16: k_total += kid['costs'][2]*12/10000
            elif 17 <= ka <= 19: k_total += kid['costs'][3]*12/10000
            elif 20 <= ka <= 23: k_total += kid['costs'][4]*12/10000

        # 4. 지출 및 세금
        tax_h = (c_re * tax_ratio) * tax_rate
        interest = c_debt * debt_rate
        # 여유자금(투자금) = 수입 - (생활비400만 + 양육비 + 보유세 + 대출이자)
        net_flow = total_inc - (400*12/10000 + k_total + tax_h + interest)
        
        c_re *= (1 + re_growth)
        # 금융자산 성장 (여유자금 투입 후 수익률 반영)
        c_inv = (c_inv + net_flow) * (1 + inv_growth)
        
        total_asset = c_re + c_inv + c_cash
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}", "순자산": total_asset - c_debt,
            "총자산": total_asset, "부채": c_debt, "부동산": c_re, "금융자산": c_inv, 
            "예금": c_cash, "연수입": total_inc, "이벤트": ", ".join(events_this_year)
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
    return pd.DataFrame(res)

# 데이터 생성
df = run_sim()

# --- 대시보드 출력 ---
tabs = st.tabs(["5년", "10년", "20년", "30년", "전체"])
p_list = [5, 10, 20, 30, 71]

for i, tab in enumerate(tabs):
    with tab:
        sub_df = df.head(p_list[i])
        
        # [메인 그래프]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산", fill='tozeroy', line=dict(color='green', width=3)))
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산", line=dict(color='blue', dash='dot')))
        fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채", marker_color='red', opacity=0.3))
        
        # 어노테이션 추가
        for _, row in sub_df.iterrows():
            if row["이벤트"]:
                fig.add_annotation(x=row["연도"], y=row["총자산"], text=row["이벤트"], showarrow=True, arrowhead=1)
        
        fig.update_layout(title="총자산/순자산 추이", hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # [4분할 세부 그래프]
        st.markdown("#### 🔍 자산군별 세부 추이 (1/4 크기)")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            f1 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["부동산"], fill='tozeroy', name="부동산"))
            f1.update_layout(title="부동산", height=200, margin=dict(l=10, r=10, t=30, b=10)); st.plotly_chart(f1, use_container_width=True)
        with c2:
            f2 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["금융자산"], fill='tozeroy', name="금융자산", line=dict(color='orange')))
            f2.update_layout(title="금융자산", height=200, margin=dict(l=10, r=10, t=30, b=10)); st.plotly_chart(f2, use_container_width=True)
        with c3:
            f3 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["부채"], fill='tozeroy', name="부채", line=dict(color='red')))
            f3.update_layout(title="부채", height=200, margin=dict(l=10, r=10, t=30, b=10)); st.plotly_chart(f3, use_container_width=True)
        with c4:
            f4 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["연수입"], fill='tozeroy', name="연수입", line=dict(color='purple')))
            f4.update_layout(title="연수입", height=200, margin=dict(l=10, r=10, t=30, b=10)); st.plotly_chart(f4, use_container_width=True)

st.divider()
st.subheader("📋 상세 시뮬레이션 데이터 (억원)")
st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
