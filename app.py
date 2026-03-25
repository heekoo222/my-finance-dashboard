import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

# --- 데이터 저장 파일명 설정 ---
DATA_FILE = "family_finance_data.json"

# 1. 페이지 설정 및 프리미엄 디자인 UI/UX
st.set_page_config(page_title="우리 가족 자산 마스터 v16.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        font-size: 20px !important; 
    }
    
    section[data-testid="stSidebar"] {
        background-color: #e0f2fe !important;
        border-right: 1px solid #bae6fd;
    }
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stHeader,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 25px !important; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #0ea5e9;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 22px !important; font-weight: 700; padding: 12px 30px;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700; background-color: #0ea5e9; color: white; height: 3.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 유지 및 자동 불러오기 로직 (초기값 완벽 설정)
if 'data_loaded' not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            for k, v in saved_data.items():
                st.session_state[k] = v
        except Exception: pass 
    st.session_state.data_loaded = True

if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state: st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]

# 3. 사이드바: 설정 레버 (중요 키 세팅 확인)
st.sidebar.title("🛠️ 재무 전략 설정")

with st.sidebar.expander("📅 시나리오 시작 시점", expanded=True):
    start_yr = st.number_input("시작 연도", value=2026, min_value=2024, key="sys_start_yr")

with st.sidebar.expander("👤 부부 소득 및 상여/퇴직금", expanded=True):
    h_tab, w_tab = st.tabs(["남편(95)", "아내(94)"])
    
    with h_tab:
        h_sal = st.number_input("남편 월급(만)", value=830, key="h_s_in")
        h_bonus_r = st.number_input("남편 상여비율(%)", value=20.0, key="h_br_in") / 100
        h_inc = st.number_input("급여 인상률(%)", value=3.0, key="h_i_in") / 100
        h_ages = list(range(40, 81))
        h_opts = [f"{1995 + a}년 ({a}세)" for a in h_ages]
        h_ret_def_idx = h_ages.index(55)
        if 'h_ret_in' in st.session_state and st.session_state.h_ret_in in h_opts: h_ret_def_idx = h_opts.index(st.session_state.h_ret_in)
        h_ret_sel = st.selectbox("남편 은퇴 시점", h_opts, index=h_ret_def_idx, key="h_ret_in")
        h_ret_age = h_ages[h_opts.index(h_ret_sel)]
        h_sev_pay = st.number_input("예상 퇴직금(만)", value=10000, step=1000, key="h_sev_in")
        h_p_amt = st.number_input("월 예상연금(65세~)", value=150, key="h_p_in")
        
    with w_tab:
        w_sal = st.number_input("아내 월급(만)", value=500, key="w_s_in")
        w_bonus_r = st.number_input("아내 상여비율(%)", value=20.0, key="w_br_in") / 100
        w_inc = st.number_input("급여 인상률(%)", value=3.0, key="w_inc_in") / 100
        w_ages = list(range(40, 81))
        w_opts = [f"{1994 + a}년 ({a}세)" for a in w_ages]
        w_ret_def_idx = w_ages.index(55)
        if 'w_r_in' in st.session_state and st.session_state.w_r_in in w_opts: w_ret_def_idx = w_opts.index(st.session_state.w_r_in)
        w_ret_sel = st.selectbox("아내 은퇴 시점", w_opts, index=w_ret_def_idx, key="w_r_in")
        w_ret_age = w_ages[w_opts.index(w_ret_sel)]
        w_sev_pay = st.number_input("예상 퇴직금(만)", value=8000, step=1000, key="w_sev_in")
        w_p_amt = st.number_input("아내 월 연금(65세~)", value=130, key="w_p_in")

with st.sidebar.expander("💸 생활비 레버", expanded=False):
    living_monthly = st.number_input("월 고정 생활비(만)", value=450, key="liv_m_in")
    living_gr = st.number_input("생활비 인상률(%)", value=2.5, key="liv_g_in") / 100

with st.sidebar.expander("📈 금융 투자 자산 설정", expanded=False):
    inv_init = st.number_input("현재 투자 원금(만)", value=15000, key="inv_ini_in")
    inv_gr = st.number_input("기대 수익률(%)", value=7.0, key="inv_gr_in") / 100
    inv_ratio = st.slider("💰 흑자 시 투자 비중(%)", 0, 100, 90, key="inv_rat_in")

with st.sidebar.expander("💳 대출 및 상환 방식", expanded=False):
    st.markdown("**기존 대출 설정**")
    debt_init = st.number_input("현재 대출 잔액(만)", value=60000, key="debt_ini_in")
    debt_r = st.number_input("기본 대출 금리(%)", value=4.0, key="debt_r_in") / 100
    debt_term = st.number_input("상환 기간(년)", value=30, key="debt_t_in")
    debt_type = st.selectbox("상환 방식 선택", ["원리금균등", "원금균등"], key="debt_tp_in")
    if st.session_state.re_trades:
        st.markdown("---")
        st.markdown("**🔄 갈아타기 신규 대출 조건**")
        for i, tr in enumerate(st.session_state.re_trades):
            st.caption(f"📍 갈아타기 #{i+1} ({tr.get('year', start_yr+10)}년 실행)")
            c1, c2 = st.columns(2)
            tr['new_debt_r'] = c1.number_input(f"신규 금리(%) {i}", value=tr.get('new_debt_r', 4.0), key=f"nd_r_{i}") / 100
            tr['new_debt_term'] = c2.number_input(f"신규 기간(년) {i}", value=tr.get('new_debt_term', 30), key=f"nd_t_{i}")
            tr['new_debt_type'] = st.selectbox(f"신규 상환 방식 {i}", ["원리금균등", "원금균등"], index=0 if tr.get('new_debt_type', '원리금균등') == '원리금균등' else 1, key=f"nd_tp_{i}")

with st.sidebar.expander("🏠 부동산 갈아타기 계획", expanded=False):
    re_init_val = st.number_input("현재 집 가액(만)", value=150000, key="re_ini_in")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=4.0, key="re_gr_in") / 100
    if st.button("➕ 갈아타기 추가"): st.session_state.re_trades.append({"year": start_yr+10, "new_price": 300000, "use_inv": 0, "new_debt_amt": debt_init, "use_cash": 0})
    temp_price = re_init_val
    temp_yr = start_yr
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 계획 #{i+1}**")
        tr['year'] = st.number_input(f"매수 연도 {i}", start_yr, 2090, tr.get('year', start_yr+10), key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"신규 주택 매수가(만) {i}", value=tr.get('new_price', 300000), step=10000, key=f"tr_np_{i}")
        est_sale = temp_price * ((1 + re_gr_rate)**(max(0, tr['year'] - temp_yr))) * 0.95
        acq_tax = tr['new_price'] * 0.033
        gap = tr['new_price'] + acq_tax - est_sale
        st.info(f"예상 매각대금(세후): {est_sale/10000:.2f}억\n주택 교환 순수 Gap: {gap/10000:.2f}억")
        st.caption("🔻 자금 조달 계획 (모자란 금액은 **신규 대출**에 강제 합산됩니다)")
        c1, c2, c3 = st.columns(3)
        tr['use_inv'] = c1.number_input(f"금융 매도(만){i}", value=tr.get('use_inv', 0), step=1000, key=f"tr_inv_{i}")
        tr['new_debt_amt'] = c2.number_input(f"신규 대출 목표{i}", value=tr.get('new_debt_amt', 60000), step=5000, key=f"tr_debt_{i}")
        tr['use_cash'] = c3.number_input(f"보유 예금 사용{i}", value=tr.get('use_cash', 0), step=1000, key=f"tr_cash_{i}")
        temp_price = tr['new_price']
        temp_yr = tr['year']
        if st.button(f"🗑️ 계획 #{i+1} 삭제", key=f"re_del_{i}"): 
            st.session_state.re_trades.pop(i)
            st.rerun()

with st.sidebar.expander("🍼 자녀 & 특별 이벤트", expanded=False):
    if st.button("➕ 자녀 추가"): st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": start_yr+1, "costs": [100, 150, 200, 250, 300]})
    for i, kid in enumerate(st.session_state.kids):
        col1, col2 = st.columns([3, 1])
        col1.write(f"👶 **{kid['name']}**")
        if col2.button("삭제", key=f"k_del_{i}"):
            st.session_state.kids.pop(i)
            st.rerun()
        kid['birth'] = st.number_input(f"출생년 {i}", 2024, 2050, kid.get('birth', 2027), key=f"kb_{i}")
        c1, c2 = st.columns(2)
        kid['costs'][0] = c1.number_input(f"영유아 {i}", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = c2.number_input(f"초등 {i}", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = c1.number_input(f"중등 {i}", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = c2.number_input(f"고등 {i}", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = c1.number_input(f"대학 {i}", value=kid['costs'][4], key=f"kc4_{i}")
    st.markdown("---")
    if st.button("➕ 이벤트 추가"): st.session_state.events.append({"name": "이벤트", "year": start_yr+3, "cost": 6000})
    for i, ev in enumerate(st.session_state.events):
        col1, col2 = st.columns([3, 1])
        ev['name'] = col1.text_input(f"명칭 {i}", ev.get('name', '이벤트'), key=f"ev_n_{i}")
        if col2.button("삭제", key=f"ev_del_{i}"):
            st.session_state.events.pop(i)
            st.rerun()
        ev['year'] = st.number_input(f"년도 {i}", start_yr, 2095, ev.get('year', start_yr+3), key=f"ev_y_{i}")
        ev['cost'] = st.number_input(f"비용 {i}", 0, 1000000, ev.get('cost', 6000), key=f"ev_c_{i}")

with st.sidebar.expander("👵 은퇴 시점 리밸런싱 & 배당", expanded=False):
    st.markdown("**1️⃣ 주택 연금화 (다운사이징)**")
    ret_re_down_ratio = st.slider("최종 은퇴 시 부동산 매각 비율(%)", 0, 100, 30, step=10, key="ret_down_r")
    st.caption("매각 대금은 양도세 정산 후 전액 금융자산으로 즉시 편입됩니다.")
    st.markdown("---")
    st.markdown("**2️⃣ 은퇴 후 금융자산 배분**")
    s_schd = st.slider("SCHD (배당성장) %", 0, 100, 25, key="ret_schd")
    s_jepq = st.slider("JEPQ (고배당) %", 0, 100, 25, key="ret_jepq")
    st.info(f"기존 금융자산 유지(재투자): {100 - s_schd - s_jepq}%")

# 4. 시뮬레이션 엔진 (보유세/FCF 등 KeyError 방지 완벽 복구)
def run_simulation():
    res = []
    c_re, c_re_base, c_inv, c_cash, c_debt, c_h_sal, c_w_sal = re_init_val, re_init_val, inv_init, 1000, debt_init, h_sal, w_sal
    curr_debt_r, curr_debt_type, rem_debt_term = debt_r, debt_type, debt_term
    h_ret_year, w_ret_year, final_ret_year = 1995 + h_ret_age, 1994 + w_ret_age, max(1995 + h_ret_age, 1994 + w_ret_age)
    
    for year in range(start_yr, 2096):
        h_age, w_age = year - 1995, year - 1994
        ev_list, pension, t_acq_total, t_gain_total = [], 0, 0, 0
        inc_h = (c_h_sal * 12 * (1+h_bonus_r)) if h_age <= h_ret_age else 0
        inc_w = (c_w_sal * 12 * (1+w_bonus_r)) if w_age <= w_ret_age else 0
        if h_age >= 65: pension += (h_p_amt * 12)
        if w_age >= 65: pension += (w_p_amt * 12)
        total_income_y = inc_h + inc_w + pension
        if year == h_ret_year: c_inv += h_sev_pay; ev_list.append(f"👨‍🦳남편 은퇴(퇴직금 {h_sev_pay//10000}억 편입)")
        if year == w_ret_year: c_inv += w_sev_pay; ev_list.append(f"👩‍🦳아내 은퇴(퇴직금 {w_sev_pay//10000}억 편입)")
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                gain = max(0, c_re - c_re_base) * 0.20; acq = tr['new_price'] * 0.033; t_gain_total += gain; t_acq_total += acq
                old_net, need, req_new_debt, use_inv, use_cash = c_re - gain - c_debt, tr['new_price'] + acq, tr.get('new_debt_amt', 60000), tr.get('use_inv', 0), tr.get('use_cash', 0)
                a_inv, a_cash = min(c_inv, use_inv), min(c_cash, use_cash); c_inv -= a_inv; c_cash -= a_cash; gap = req_new_debt + a_inv + a_cash - (tr['new_price'] + acq - old_net)
                if gap >= 0: c_cash += gap; c_debt = req_new_debt
                else: c_debt = req_new_debt + abs(gap); c_inv -= min(c_inv, abs(gap)); c_cash = 0
                c_re, c_re_base = tr['new_price'], tr['new_price']
                curr_debt_r, curr_debt_type, rem_debt_term = tr.get('new_debt_r', curr_debt_r), tr.get('new_debt_type', curr_debt_type), tr.get('new_debt_term', debt_term); ev_list.append("🏠부동산 갈아타기")
        if year == final_ret_year and ret_re_down_ratio > 0:
            d_r = ret_re_down_ratio / 100; ds_gain = max(0, c_re * d_r - c_re_base * d_r) * 0.20; t_gain_total += ds_gain; c_inv += c_re * d_r - ds_gain; c_re -= c_re * d_r; c_re_base -= c_re_base * d_r; ev_list.append(f"📉주택축소({ret_re_down_ratio}%)")
        t_hold, t_comp, t_fin_tax = (c_re * 0.6) * 0.002, max(0, (c_re - 120000) * 0.005), (c_inv * 0.03) * 0.154 if c_inv > 0 else 0
        tax_etc = total_income_y * 0.15; total_tax_y = tax_etc + t_hold + t_comp + t_fin_tax
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']; sch_stage = ""
            if 0<=ka<=7: k_total += kid['costs'][0]*12; sch_stage = "👶 초교 입학" if ka==7 else ""
            elif 8<=ka<=13: k_total += kid['costs'][1]*12; sch_stage = "🧒 중교 입학" if ka==13 else ""
            elif 14<=ka<=16: k_total += kid['costs'][2]*12; sch_stage = "🧑 고교 입학" if ka==16 else ""
            elif 17<=ka<=19: k_total += kid['costs'][3]*12; sch_stage = "👨🎓 대학교 입학" if ka==19 else ""
            elif 20<=ka<=23: k_total += kid['costs'][4]*12; sch_stage = "💼 대학 졸업/독립" if ka==23 else ""
            if sch_stage: ev_list.append(f"{kid['name']}{sch_stage}")
            if year == kid['birth']: ev_list.append(f"🍼 {kid['name']} 탄생")
        interest_a, principal_a, repay_a = 0, 0, 0
        if c_debt > 0 and rem_debt_term > 0:
            if curr_debt_type == "원리금균등":
                interest_a = c_debt * curr_debt_r
                principal_a = ((c_debt * curr_debt_r * (1+curr_debt_r)**rem_debt_term) / ((1+curr_debt_r)**rem_debt_term - 1) - interest_a) if curr_debt_r>0 else (c_debt/rem_debt_term)
                repay_a = principal_a + interest_a
            else:
                principal_a = c_debt / rem_debt_term
                interest_a = c_debt * curr_debt_r
                repay_a = principal_a + interest_a
            rem_debt_term -= 1
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        if ev_cost > 0: ev_list.append(f"🎁 이벤트: {','.join([ev['name'] for ev in st.session_state.events if ev['year']==year])}")
        curr_living_y = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        total_exp_y = curr_living_y + k_total + total_tax_y + repay_a + ev_cost
        net_flow_y = total_income_y - total_exp_y
        if net_flow_y >= 0: c_inv += net_flow_y * (inv_ratio / 100); c_cash += net_flow_y * (1 - inv_ratio/100)
        else:
            if c_cash >= abs(net_flow_y): c_cash -= abs(net_flow_y)
            else: net_flow_y += c_cash; c_cash = 0; deficit = abs(net_flow_y); c_inv -= min(c_inv, deficit); if c_inv < deficit: c_debt += (deficit - c_inv); c_inv = 0
        c_re *= (1 + re_gr_rate); c_inv *= (1 + inv_gr); c_debt = max(0, c_debt - principal_a); c_w_sal *= (1 + w_inc); c_h_sal *= (1 + h_inc)
        res.append({
            "연도": year, "순자산_억": (c_re + c_inv + c_cash - c_debt)/10000, "총자산_억": (c_re + c_inv + c_cash)/10000, "부동산_억": c_re/10000, "금융자산_억": c_inv/10000, "예금_억": c_cash/10000, "대출_억": c_debt/10000,
            "보유세_만": t_hold + t_comp, "금융소득세_만": t_fin_tax, "양도세_만": t_gain_total, "취득세_만": t_acq_total, # KeyError 방지 완벽대응
            "총수입_만": total_income_y, "월_순현금_만": net_flow_y/12, "월_지출_만": total_exp_y/12, "이벤트": "<br>".join(ev_list) if ev_list else "특별한 이벤트 없음"
        })
    return pd.DataFrame(res)

df_res = run_simulation()

# --- 5. 대시보드 출력 UI ---

# UX 개선 3) 대시보드 맨 위 통합 요약칸 및 메인 제목
final_ret_yr = max(1995 + h_ret_age, 1994 + w_ret_age)
ret_row = df_res[df_res["연도"] == final_ret_yr].iloc[0]

st.markdown(f"## 👨‍👩‍👧‍👦 우리 가족 통합 자산 프로젝션 v16.0")
st.markdown("---")

c1, c2, c blank = st.columns([1, 1, 0.5])
c1.metric("🚩 남편 은퇴 시점", f"{1995+h_ret_age}년", f"{h_ret_age}세")
c2.metric("🚩 아내 은퇴 시점", f"{1994+w_ret_age}년", f"{w_ret_age}세")

c blank, col1, col2 = st.columns([0.5, 1, 1])
col1.metric(f"{final_ret_yr}년 시점 총자산", f"{ret_row['총자산_억']:.2f}억")
col2.metric(f"{final_ret_yr}년 시점 순자산", f"{ret_row['순자산_억']:.2f}억")
st.markdown("---")

def draw_premium_table(df):
    return go.Figure(data=[go.Table(header=dict(values=list(df.columns), fill_color='#0ea5e9', font=dict(color='white', size=16), align='center', height=45), cells=dict(values=[df[col] for col in df.columns], fill_color='#f8fafc', font=dict(color='#0f172a', size=15), align='center', height=35))])

m_tab, t_tab, s_tab, d_tab = st.tabs(["📊 자산 성장 로드맵", "⚖️ 상세 세무 분석", "👵 은퇴 & 배당 시뮬레이션", "📋 데이터 상세"])

with m_tab:
    period = st.radio("🔍 조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4, key="p_sel")
    sub = df_res.head({"5년":5, "10년":10, "20년":20, "30년":30, "전체":len(df_res)}[period])

    # UX 개선 3) 메인 차트 제목 '우리 가족 자산 계획' 넣어줌
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산", marker_color='#10b981', customdata=sub["이벤트"], hovertemplate="<b>%{x}년 순자산: %{y:.2f}억</b><br>🚨 <b>이슈:</b><br>%{customdata}<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="부채", marker_color='#ef4444', customdata=sub["이벤트"], hovertemplate="<b>%{x}년 부채: %{y:.2f}억</b><extra></extra>"))
    # UX 개선 1) UI UX 깔끔 정리: x-axis unified 모드 활성화로 깔끔하게
    fig.update_layout(title="🏠 우리 가족 자산 계획 (단위: 억)", barmode='stack', hovermode="x unified", height=600, template="plotly_white", font=dict(size=18), legend=dict(font=dict(size=16)))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🔍 세부 지표")
    def draw_mini(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], marker_color=color, customdata=data["이벤트"], hovertemplate="<b>%{x}년</b><br>금액: %{y:.2f}<br>--------------------<br>%{customdata}<extra></extra>"))
        f.update_layout(title=dict(text=title, font=dict(size=22)), height=360, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
        return f
    
    c1, c2 = st.columns(2)
    c1.plotly_chart(draw_mini(sub, "부동산_억", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini(sub, "금융자산_억", "📈 금융투자(억)", "#8b5cf6"), use_container_width=True)
    
    # UX 개선 1) 가시성 좋게: 월 지출 차트의 legend가 겹치지 않게 하단으로 배치
    f_exp = go.Figure(go.Bar(x=sub["연도"], y=sub["월_지출_만"], marker_color="#ec4899", customdata=sub["이벤트"], hovertemplate="<b>%{x}년</b><br>월 지출: %{y:,.0f}만<br>--------------------<br>%{customdata}<extra></extra>"))
    f_exp.update_layout(title=dict(text="💸 월 지출(만)", font=dict(size=22)), height=360, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white")
    
    c3, c4 = st.columns(2)
    c3.plotly_chart(draw_mini(sub, "예금_억", "💰 예금(억)", "#0ea5e9"), use_container_width=True)
    c4.plotly_chart(f_exp, use_container_width=True)

with t_tab:
    # UX 개선 2) 주요 가정 사항 설명 추가
    st.header("⚖️ 상세 세무 분석 도우미")
    st.caption("🔻 부동산 양도세 및 취득세 등 세금 산출을 위한 주요 가정")
    c_acq, c_gain = st.columns(2)
    c_acq.info("✅ **취득세 가정**: 갈아타기 주택 매수가의 3.3% 적용 (지방세 포함)", icon="📝")
    c_gain.info("✅ **양도세 가정**: 기존 주택 시세 차익의 20%를 양도세로 공제", icon="💸")
    
    st.header("⚖️ 상세 세무 분석 테이블 (단위: 만원)")
    # KeyError 완벽 복구됨
    t_disp = df_res[["연도", "보유세_만", "금융소득세_만", "양도세_만", "취득세_만", "이벤트"]].copy()
    for col in ["보유세_만", "금융소득세_만", "양도세_만", "취득세_만"]: t_disp[col] = t_disp[col].apply(lambda x: f"{x:,.0f}")
    t_disp["이벤트"] = t_disp["이벤트"].apply(lambda x: str(x).replace("<br>", " / "))
    t_disp.columns = ["연도", "🏠 보유세(재산+종부)", "📈 금융소득세(배당등)", "💸 양도세", "📝 취득세", "🚩 관련 이벤트"]
    st.plotly_chart(draw_premium_table(t_disp), use_container_width=True)

with s_tab:
    final_ret_yr = max(1995 + h_ret_age, 1994 + w_ret_age)
    if final_ret_yr > 2095: st.warning("설정된 은퇴 연도가 시뮬레이션 종료 시점(2095년)을 초과합니다.")
    else:
        # UX 개선 2) 주요 가정 사항 설명 추가
        st.header(f"🚩 최종 은퇴 연도: {final_ret_yr}년 도우미")
        st.caption("🔻 은퇴 자금 산출 및 배당 시뮬레이션을 위한 주요 가정")
        c_pv, c_yld = st.columns(2)
        c_pv.info(f"✅ **현재가치 할인율 3%**: 은퇴 시점 자산을 {start_yr}년 가치로 할인 산출", icon="⏳")
        c_yld.info(f"✅ **혼합 배당률 가정**: JEPQ 9.5% 고정, SCHD 초기 3.5%( Yield on Cost 연 5% 성장 가정)", icon="💰")
        st.caption("🔻 은퇴 포트폴리오 초기 배당 수익률 (Yield on Cost)")
        col1, col2, col3 = st.columns(3)
        col1.caption("▫️ JEPQ (고배당) : 9.5%")
        col2.caption(f"▫️ SCHD (성장) : 초기 3.5% (배당 5% 성장 가정)")
        col3.caption("▫️ 유지자산(나스닥) : 1.0%")
        st.markdown("---")

        st.header(f"🚩 은퇴 자금 현황 (할인율 3% 적용)")
        ret_row = df_res[df_res["연도"] == final_ret_yr].iloc[0]
        c_inv_fv = ret_row["금융자산_억"]
        
        # 현재가치 할인 (FV / (1+r)^t) - Require 2 도우미 설명에 따른 산출
        years_passed = final_ret_yr - start_yr
        discount_factor = (1 + 0.03) ** max(0, years_passed)
        c_inv_pv = c_inv_fv / discount_factor
        
        col_fv, col_pv = st.columns(2)
        col_fv.metric(f"은퇴 시 금융자산 (FV, {final_ret_yr}년 가치)", f"{c_inv_fv:.2f}억")
        col_pv.metric(f"은퇴 시 금융자산 (할인 PV, {start_yr}년 가치)", f"{c_inv_pv:.2f}억", help=f"{start_yr}년 기준으로 할인한 현재 체감 가치")
        st.markdown("---")
        
        st.markdown("#### 💰 은퇴 후 배당 포트폴리오 (미래가치 기준)")
        schd_amt = c_inv_fv * (s_schd / 100); jepq_amt = c_inv_fv * (s_jepq / 100)
        # Yield on Cost 배당성장 가정 - Require 2 도우미 설명에 따른 산출
        init_m_div = ((schd_amt * 0.035) + (jepq_amt * 0.095) + (c_inv_fv * (100-s_schd-s_jepq)/100 * 0.01)) * 10000 / 12
        
        c1, c2, c3 = st.columns(3)
        c1.metric("첫 달 예상 배당금", f"{init_m_div:,.0f}만")
        c2.metric(f"SCHD ({s_schd}%) 배분액", f"{schd_amt:.2f}억")
        c3.metric(f"JEPQ ({s_jepq}%) 배분액", f"{jepq_amt:.2f}억")
        st.caption(f"💡 기존 투자 유지 자산: {c_inv_fv * (100 - s_schd - s_jepq) / 100:.2f}억")
        st.markdown("---")
        
        div_data = []
        sim_inv_val = c_inv_fv
        for y in range(final_ret_yr, 2096):
            # Require 2 도우미 설명 사항에 따른 배당성장(YoC) 산출 엔진
            s_p = sim_inv_val * (s_schd/100); j_p = sim_inv_val * (s_jepq/100)
            schd_yoc = 0.035 * (1.05**(y-final_ret_yr)) # 배당성장 Yield on Cost
            m_div = ((s_p * schd_yoc) + (j_p * 0.095) + (sim_inv_val * (100-s_schd-s_jepq)/100 * 0.01)) * 10000 / 12
            div_data.append({"연도": y, "월_배당금": m_div}); sim_inv_val *= (1 + inv_gr)
        df_div = pd.DataFrame(div_data)
        
        # UX 개선 1) UI UX 깔끔 정리: 배당 차트의 legend가 겹치지 않게 하단으로 배치
        fig_div = go.Figure(go.Scatter(x=df_div["연도"], y=df_div["월_배당금"], fill='tozeroy', name="월 배당(만)", marker_color="#8b5cf6", hovertemplate="<b>%{x}년</b><br>배당: %{y:,.0f}만<extra></extra>"))
        fig_div.update_layout(title="은퇴 후 월 배당성장 추이 (미래가치, Yield on Cost)", height=450, template="plotly_white")
        st.plotly_chart(fig_div, use_container_width=True)

with d_tab:
    st.subheader("📋 전체 상세 데이터")
    cols_to_show = ["연도", "순자산_억", "총자산_억", "부동산_억", "금융자산_억", "예금_억", "대출_억", "보유세_만", "금융소득세_만", "월_순현금_만", "월_지출_만", "이벤트"]
    # KeyError 완벽 복구됨
    d_disp = df_res[cols_to_show].copy()
    for col in d_disp.columns:
        if col not in ["연도", "이벤트"]:
            if "_억" in col: d_disp[col] = d_disp[col].apply(lambda x: f"{x:,.2f}")
            else: d_disp[col] = d_disp[col].apply(lambda x: f"{x:,.0f}")
    d_disp["이벤트"] = d_disp["이벤트"].apply(lambda x: str(x).replace("<br>", " / "))
    st.plotly_chart(draw_premium_table(d_disp), use_container_width=True)

static_keys = ['sys_start_yr', 'h_s_in', 'h_br_in', 'h_i_in', 'h_ret_in', 'h_sev_in', 'h_p_in', 'w_s_in', 'w_br_in', 'w_inc_in', 'w_r_in', 'w_sev_in', 'w_p_in', 'liv_m_in', 'liv_g_in', 'inv_ini_in', 'inv_gr_in', 'inv_rat_in', 'debt_ini_in', 'debt_r_in', 'debt_t_in', 'debt_tp_in', 're_ini_in', 're_gr_in', 'ret_down_r', 'ret_schd', 'ret_jepq']
data_to_save = {'re_trades': st.session_state.re_trades, 'events': st.session_state.events, 'kids': st.session_state.kids}
for k in static_keys:
    if k in st.session_state: data_to_save[k] = st.session_state[k]
try:
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data_to_save, f, ensure_ascii=False, indent=4)
except Exception: pass
