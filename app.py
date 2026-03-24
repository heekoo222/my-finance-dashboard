import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="부부 통합 자산 관리", layout="wide")

st.title("👨‍👩‍👧‍👦 우리 가족 통합 재무 시뮬레이터")
st.markdown("95년생 남편 & 94년생 아내의 100세 인생 설계")

# --- 사이드바: 주요 가정 사항 ---
st.sidebar.header("📍 기본 설정")
start_year = 2025
end_year = 2095

# 1. 부부 개별 설정 탭
with st.sidebar.expander("👤 부부별 정보 설정", expanded=True):
    tab_h, tab_w = st.tabs(["남편(95)", "아내(94)"])
    
    with tab_h:
        h_salary = st.number_input("남편 월급 (세후, 만원)", value=500)
        h_sal_growth = st.slider("남편 급여 인상률 (%)", 0.0, 10.0, 3.0, key="h_sg") / 100
        h_bonus_rate = st.slider("남편 상여금 비율 (%)", 0.0, 100.0, 20.0, key="h_br") / 100
        h_retire_age = st.slider("남편 은퇴 나이", 40, 70, 55, key="h_ra")
        h_pension_age = st.slider("남편 연금수령 나이", 60, 70, 65, key="h_pa")
        h_pension_amt = st.number_input("남편 예상 연금 (월/만원)", value=150, key="h_pam")
        
    with tab_w:
        w_salary = st.number_input("아내 월급 (세후, 만원)", value=450)
        w_sal_growth = st.slider("아내 급여 인상률 (%)", 0.0, 10.0, 3.0, key="w_sg") / 100
        w_bonus_rate = st.slider("아내 상여금 비율 (%)", 0.0, 100.0, 20.0, key="w_br") / 100
        w_retire_age = st.slider("아내 은퇴 나이", 40, 70, 55, key="w_ra")
        w_pension_age = st.slider("아내 연금수령 나이", 60, 70, 65, key="w_pa")
        w_pension_amt = st.number_input("아내 예상 연금 (월/만원)", value=130, key="w_pam")

# 2. 자산 및 수익률
with st.sidebar.expander("💰 초기 자산 및 수익률", expanded=False):
    re_init = st.number_input("부동산 (억원)", value=14.0)
    re_rate = st.slider("부동산 상승률 (%)", 0.0, 10.0, 4.0) / 100
    inv_init = st.number_input("금융투자 (억원)", value=0.6)
    inv_rate = st.slider("투자 수익률 (%)", 0.0, 15.0, 8.0) / 100
    debt_init = st.number_input("부채 (억원)", value=6.0)
    debt_rate = st.slider("대출 이자율 (%)", 0.0, 10.0, 4.0) / 100

# 3. 자녀 설정
with st.sidebar.expander("👶 자녀 및 양육비", expanded=False):
    kid_count = st.number_input("자녀 수", 0, 3, 1)
    kid_births = [st.number_input(f"{i+1}번 자녀 출산년도", 2024, 2040, 2027+i*2) for i in range(kid_count)]
    st.info("연령대별 월 양육비 (만원)")
    k_costs = [st.number_input("0~7세", 100), st.number_input("8~13세", 120), st.number_input("14~19세", 180), st.number_input("20~23세", 250)]

# 4. 특별 이벤트 (멀티 추가 가능하게 세션 스테이트 활용)
st.sidebar.subheader("🚀 특별 이벤트")
if 'events' not in st.session_state:
    st.session_state.events = [{"name": "차량 구매", "year": 2030, "cost": 0.5}]

def add_event():
    st.session_state.events.append({"name": "새 이벤트", "year": 2025, "cost": 0.0})

for i, event in enumerate(st.session_state.events):
    cols = st.sidebar.columns([2, 1, 1])
    event['name'] = cols[0].text_input(f"명칭", event['name'], key=f"ev_n_{i}")
    event['year'] = cols[1].number_input(f"년도", 2025, 2095, event['year'], key=f"ev_y_{i}")
    event['cost'] = cols[2].number_input(f"억", 0.0, 100.0, event['cost'], key=f"ev_c_{i}")

st.sidebar.button("➕ 이벤트 추가", on_click=add_event)

# --- 시뮬레이션 계산 ---
def run_simulation():
    data = []
    curr_re = re_init
    curr_inv = inv_init
    curr_debt = debt_init
    curr_h_sal = h_salary
    curr_w_sal = w_salary
    living_cost_base = 350 # 부부 기본 생활비 (월/만원)

    for year in range(start_year, end_year + 1):
        h_age = year - 1995
        w_age = year - 1994
        
        # 1. 수입 계산 (급여 & 상여)
        inc_h = (curr_h_sal * 12 * (1 + h_bonus_rate)) / 10000 if h_age <= h_retire_age else 0
        inc_w = (curr_w_sal * 12 * (1 + w_bonus_rate)) / 10000 if w_age <= w_retire_age else 0
        
        # 2. 국민연금 계산
        p_h = (h_pension_amt * 12) / 10000 if h_age >= h_pension_age else 0
        p_w = (w_pension_amt * 12) / 10000 if w_age >= w_pension_age else 0
        
        # 3. 지출 계산 (양육비)
        kid_cost = 0
        for b_year in kid_births:
            k_age = year - b_year
            if 0 <= k_age <= 7: kid_cost += (k_costs[0]*12)/10000
            elif 8 <= k_age <= 13: kid_cost += (k_costs[1]*12)/10000
            elif 14 <= k_age <= 19: kid_cost += (k_costs[2]*12)/10000
            elif 20 <= k_age <= 23: kid_cost += (k_costs[3]*12)/10000
        
        # 4. 자산 변동 (수익률 & 이자)
        curr_re *= (1 + re_rate)
        curr_inv *= (1 + inv_rate)
        int_debt = curr_debt * debt_rate
        
        # 이벤트 지출
        ev_total = sum([e['cost'] for e in st.session_state.events if e['year'] == year])
        
        # 여유자금 저축 (단순화: 수입 - (기본생활비 + 양육비 + 이자 + 이벤트))
        annual_living = (living_cost_base * 12) / 10000
        savings = (inc_h + inc_w + p_h + p_w) - (annual_living + kid_cost + int_debt + ev_total)
        curr_inv += savings
        
        # 대출 상환 로직 (여유자금이 있으면 부채부터 갚는다고 가정, 혹은 투자로 유지)
        # 여기서는 여유자금이 금융투자로 들어가는 것으로 설정
        
        total_asset = curr_re + curr_inv + 0.1 # 예금 등 기타 0.1억 고정
        net_asset = total_asset - curr_debt
        
        data.append({
            "연도": f"{year}년",
            "남편/아내나이": f"{h_age}/{w_age}세",
            "총자산": round(total_asset, 2),
            "순자산": round(net_asset, 2),
            "부채": round(curr_debt, 2),
            "부동산": round(curr_re, 2),
            "금융투자": round(curr_inv, 2),
            "남편급여(연)": round(inc_h, 2),
            "아내급여(연)": round(inc_w, 2),
            "합계연금(연)": round(p_h + p_w, 2)
        })
        
        # 다음해 급여 상승
        curr_h_sal *= (1 + h_sal_growth)
        curr_w_sal *= (1 + w_sal_growth)

    return pd.DataFrame(data)

df_res = run_simulation()

# --- 대시보드 출력 ---
# 상단 요약 지표
c1, c2, c3 = st.columns(3)
c1.metric("60세 시점 예상 순자산", f"{df_res.iloc[2025+35-start_year]['순자산']} 억")
c2.metric("최종 자산 (95세)", f"{df_res.iloc[-1]['순자산']} 억")
c3.metric("총 부채", f"{debt_init} 억")

# 그래프 섹션
st.subheader("📈 자산 추이 시뮬레이션")
tab_10, tab_30, tab_full = st.tabs(["근기 (10년)", "중기 (30년)", "전체 (100세)"])

def draw_res_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["연도"], y=data["총자산"], name="총자산", line=dict(color='royalblue', width=2)))
    fig.add_trace(go.Bar(x=data["연도"], y=data["순자산"], name="순자산", marker_color='lightgreen'))
    fig.add_trace(go.Bar(x=data["연도"], y=data["부채"], name="부채", marker_color='indianred'))
    fig.update_layout(barmode='group', hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab_10: draw_res_chart(df_res.head(10))
with tab_30: draw_res_chart(df_res.head(30))
with tab_full: draw_res_chart(df_res)

# 데이터 상세 테이블
st.subheader("📋 연도별 자산/수입 상세 내역")
st.dataframe(
    df_res,
    column_config={
        "총자산": st.column_config.NumberColumn(format="%.2f 억"),
        "순자산": st.column_config.NumberColumn(format="%.2f 억"),
        "부채": st.column_config.NumberColumn(format="%.2f 억"),
        "부동산": st.column_config.NumberColumn(format="%.2f 억"),
        "금융투자": st.column_config.NumberColumn(format="%.2f 억"),
    },
    use_container_width=True,
    hide_index=True
)
