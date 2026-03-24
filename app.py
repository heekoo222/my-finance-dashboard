import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="우리집 통합 재무 시뮬레이터", layout="wide")

st.title("👨‍👩‍👧‍👦 우리 가족 자산 통합 관리 시스템")
st.markdown("95년생 남편 & 94년생 아내의 생애 주기별 자산 추뮬레이션")

# --- 세션 스테이트 초기화 ---
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.6}]
if 're_trades' not in st.session_state:
    st.session_state.re_trades = [{"year": 2033, "new_price": 25.0, "priority": ["금융자산", "대출", "예금"]}]
if 'kids' not in st.session_state:
    st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 120, 150, 180, 250]}]

# --- 사이드바: 정밀 설정 ---
st.sidebar.header("⚙️ 상세 설정")

# (1) 부부 소득 및 은퇴
with st.sidebar.expander("👤 부부 수입 & 은퇴", expanded=False):
    col_h, col_w = st.tabs(["남편(95)", "아내(94)"])
    with col_h:
        h_sal = st.number_input("월급(만)", value=550); h_inc = st.number_input("인상률(%)", value=3.0) / 100
        h_ret = st.number_input("은퇴나이", value=55); h_p_age = st.number_input("연금시작", value=65)
    with col_w:
        w_sal = st.number_input("월급(만)", value=500); w_inc = st.number_input("인상률(%)", value=3.0) / 100
        w_ret = st.number_input("은퇴나이", value=55); w_p_age = st.number_input("연금시작", value=65)

# (2) 자녀별 개별 양육비 설정
with st.sidebar.expander("👶 자녀별 양육비 상세", expanded=False):
    if st.button("➕ 자녀 추가"):
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": 2028, "costs": [100, 120, 150, 180, 250]})
    
    for i, kid in enumerate(st.session_state.kids):
        st.markdown(f"**{kid['name']} 설정**")
        kid['birth'] = st.number_input(f"{kid['name']} 출생년도", 2024, 2050, kid['birth'], key=f"k_b_{i}")
        c1, c2, c3 = st.columns(3)
        kid['costs'][0] = c1.number_input("영유아", value=kid['costs'][0], key=f"k_c0_{i}")
        kid['costs'][1] = c2.number_input("초등", value=kid['costs'][1], key=f"k_c1_{i}")
        kid['costs'][2] = c3.number_input("중등", value=kid['costs'][2], key=f"k_c2_{i}")
        kid['costs'][3], kid['costs'][4] = st.columns(2)[0].number_input("고등", value=kid['costs'][3], key=f"k_c3_{i}"), st.columns(2)[1].number_input("대학", value=kid['costs'][4], key=f"k_c4_{i}")

# (3) 부동산 갈아타기 & 대출/세금
with st.sidebar.expander("🔄 부동산 갈아타기 시나리오", expanded=True):
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": 2040, "new_price": 30.0, "priority": ["금융자산", "대출", "예금"]})
    for i, trade in enumerate(st.session_state.re_trades):
        trade['year'] = st.number_input(f"매수년도", 2025, 2095, trade['year'], key=f"tr_y_{i}")
        trade['new_price'] = st.number_input(f"매수가(억)", 0.0, 100.0, trade['new_price'], key=f"tr_p_{i}")
        trade['priority'] = st.multiselect(f"자금순위", ["금융자산", "예금", "대출"], default=trade['priority'], key=f"tr_pr_{i}")

with st.sidebar.expander("📈 기본 자산 & 세금", expanded=False):
    re_init = st.number_input("초기부동산(억)", value=14.0); re_growth = st.number_input("부동산상승률(%)", value=4.0)/100
    inv_init = st.number_input("초기투자(억)", value=1.0); inv_growth = st.number_input("투자수익률(%)", value=7.0)/100
    debt_init = st.number_input("초기대출(억)", value=6.0); debt_rate = st.number_input("대출금리(%)", value=4.0)/100
    tax_ratio = st.number_input("공시지가비율(%)", value=60.0)/100
    tax_rate = st.number_input("보유세율(%)", value=0.2)/100

# --- 시뮬레이션 엔진 ---
def run_sim():
    res = []
    c_re, c_inv, c_cash, c_debt = re_init, inv_init, 0.5, debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    for year in range(2025, 2096):
        h_age, w_age = year - 1995, year - 1994
        
        # [이벤트 텍스트 수집]
        current_events = []
        for kid in st.session_state.kids:
            if year == kid['birth']: current_events.append(f"👶{kid['name']} 탄생")
        for trade in st.session_state.re_trades:
            if year == trade['year']: current_events.append(f"🏠{trade['new_price']}억 갈아타기")
        for ev in st.session_state.events:
            if year == ev['year']: current_events.append(f"🚀{ev['name']}")
        
        # 1. 수입
        inc = ((c_h_sal if h_age <= h_ret else 0) + (c_w_sal if w_age <= w_ret else 0)) * 14 / 10000 
        
        # 2. 갈아타기 실행
        for trade in st.session_state.re_trades:
            if year == trade['year']:
                gap = trade['new_price'] - (c_re * 0.98)
                for src in trade['priority']:
                    if gap <= 0: break
                    if src == "금융자산": use = min(c_inv, gap); c_inv -= use; gap -= use
                    elif src == "대출": c_debt += gap; gap = 0
                c_re = trade['new_price']

        # 3. 지출 (양육비 합산)
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if 0<=ka<=7: k_total += kid['costs'][0]*12/10000
            elif 8<=ka<=13: k_total += kid['costs'][1]*12/10000
            elif 14<=ka<=16: k_total += kid['costs'][2]*12/10000
            elif 17<=ka<=19: k_total += kid['costs'][3]*12/10000
            elif 20<=ka<=23: k_total += kid['costs'][4]*12/10000

        tax_holding = (c_re * tax_ratio) * tax_rate
        net_flow = inc - (400*12/10000 + k_total + tax_holding + c_debt*debt_rate)
        
        c_re *= (1+re_growth); c_inv = (c_inv + net_flow) * (1+inv_growth)
        
        res.append({
            "연도": year, "나이": f"{h_age}/{w_age}", "총자산": c_re+c_inv, "순자산": c_re+c_inv-c_debt,
            "부채": c_debt, "부동산": c_re, "금융자산": c_inv, "이벤트": ", ".join(current_events)
        })
        c_h_sal *= (1+h_inc); c_w_sal *= (1+w_inc)
    return pd.DataFrame(res)

df = run_sim()

# --- 대시보드 출력 ---
period_tab = st.tabs(["5년", "10년", "20년", "30년", "전체"])
period_map = {"5년": 5, "10년": 10, "20년": 20, "30년": 30, "전체": 71}

for i, tab in enumerate(period_tab):
    with tab:
        p_key = list(period_map.keys())[i]
        sub_df = df.head(period_map[p_key])
        
        # 메인 그래프: 총자산/순자산/부채 + 이벤트 표시
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산", fill='tozeroy', line=dict(color='green', width=3)))
        fig.add_trace(go.Scatter(x=sub_df["연도"], y=sub_df["총자산"], name="총자산", line=dict(color='royalblue', dash='dot')))
        fig.add_trace(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채", marker_color='red', opacity=0.3))
        
        # 이벤트 Annotation 추가
        for idx, row in sub_df.iterrows():
            if row["이벤트"]:
                fig.add_annotation(x=row["연도"], y=row["총자산"], text=row["이벤트"], showarrow=True, arrowhead=1)
        
        fig.update_layout(title=f"{p_key} 자산 추이", hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # 하단 4분할 세부 그래프
        st.markdown("#### 🔍 자산군별 세부 추이")
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            f1 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["부동산"], fill='tozeroy', name="부동산"))
            f1.update_layout(title="부동산", height=250, margin=dict(l=20, r=20, t=40, b=20)); st.plotly_chart(f1, use_container_width=True)
        with c2:
            f2 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["금융자산"], fill='tozeroy', name="금융자산", line=dict(color='orange')))
            f2.update_layout(title="금융자산", height=250, margin=dict(l=20, r=20, t=40, b=20)); st.plotly_chart(f2, use_container_width=True)
        with c3:
            f3 = go.Figure(go.Bar(x=sub_df["연도"], y=sub_df["부채"], name="부채", marker_color='red'))
            f3.update_layout(title="부채 잔액", height=250, margin=dict(l=20, r=20, t=40, b=20)); st.plotly_chart(f3, use_container_width=True)
        with c4:
            sub_df["연수입"] = df["연수입"] if "연수입" in df else 0 # 수입 추이 예시
            f4 = go.Figure(go.Scatter(x=sub_df["연도"], y=sub_df["순자산"], name="순자산"))
            f4.update_layout(title="순자산 변화", height=250, margin=dict(l=20, r=20, t=40, b=20)); st.plotly_chart(f4, use_container_width=True)

st.divider()
st.subheader("📋 전체 연도별 상세 데이터")
st.dataframe(df, use_container_width=True, hide_index=True)
