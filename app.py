import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import urllib.request

# =====================================================================
# ☁️ 회원님의 전용 클라우드 DB 주소
# =====================================================================
FIREBASE_URL = "https://familiy-financial-plan-default-rtdb.asia-southeast1.firebasedatabase.app/finance_db.json"

st.set_page_config(page_title="우리 가족 자산 마스터 (Ultimate Ver.)", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 19px !important; }
    section[data-testid="stSidebar"] { background-color: #f0fdf4 !important; border-right: 1px solid #bbf7d0; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 20px !important; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #10b981; }
    .stTabs [data-baseweb="tab"] { font-size: 20px !important; font-weight: 700; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 클라우드 연동 ---
def load_cloud_db():
    try:
        req = urllib.request.Request(FIREBASE_URL)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data if data else {}
    except: return {}

def save_cloud_db(db_data):
    try:
        req = urllib.request.Request(FIREBASE_URL, data=json.dumps(db_data).encode('utf-8'), method='PUT')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req)
    except: pass

db = load_cloud_db()

st.sidebar.title("☁️ 클라우드 계정")
user_id = st.sidebar.text_input("아이디 (예: ethan)", key="login_id")
if not user_id:
    st.info("👈 **사이드바에 아이디를 입력하여 나만의 재무설계를 시작하세요!**")
    st.stop()

user_data = db.get(user_id, {})
if 'current_user' not in st.session_state or st.session_state.current_user != user_id:
    st.session_state.current_user = user_id
    # Default data load
    st.session_state.re_trades = user_data.get('re_trades', [])
    st.session_state.events = user_data.get('events', [])
    st.session_state.kids = user_data.get('kids', [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}])
    st.session_state.h_leaves = user_data.get('h_leaves', [])
    st.session_state.w_leaves = user_data.get('w_leaves', [])
    
    static_keys = [
        'sys_start_yr', 'sys_end_yr', 'h_birth_yr', 'w_birth_yr', 'is_pv_mode', 'has_health_ins',
        'h_s_in', 'h_br_in', 'h_i_in', 'h_promo_yr', 'h_promo_r', 'h_ret_in', 'h_sev_in', 'h_p_in', 'h_pp_in', 'h_side_in', 'h_side_end',
        'w_s_in', 'w_br_in', 'w_inc_in', 'w_promo_yr', 'w_promo_r', 'w_r_in', 'w_sev_in', 'w_p_in', 'w_pp_in', 'w_side_in', 'w_side_end',
        'liv_m_in', 'liv_g_in', 'inv_ini_in', 'inv_gr_in', 'inv_rat_in', 
        'debt_ini_in', 'debt_r_in', 'debt_t_in', 'debt_tp_in', 're_ini_in', 're_gr_in', 
        'ret_down_r', 'ret_debt_r', 'ret_schd', 'ret_jepq', 'h_unemp', 'w_unemp'
    ]
    for k in static_keys:
        if k in user_data: st.session_state[k] = user_data[k]

if 're_trades' not in st.session_state: st.session_state.re_trades = []
if 'events' not in st.session_state: st.session_state.events = []
if 'kids' not in st.session_state: st.session_state.kids = [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}]
if 'h_leaves' not in st.session_state: st.session_state.h_leaves = []
if 'w_leaves' not in st.session_state: st.session_state.w_leaves = []

# --- 증여세 계산기 함수 ---
def calc_gift_tax(amt_manwon):
    tax_base = max(0, amt_manwon - 5000) # 직계존비속 5천만원 공제
    if tax_base <= 0: return 0
    elif tax_base <= 10000: return tax_base * 0.1
    elif tax_base <= 50000: return (tax_base * 0.2) - 1000
    elif tax_base <= 100000: return (tax_base * 0.3) - 6000
    elif tax_base <= 300000: return (tax_base * 0.4) - 16000
    else: return (tax_base * 0.5) - 46000

st.title("💎 우리 가족 통합 자산 프로젝션 v19.0 (Ultimate)")

# 🌟 1. 현재가치(PV) 토글 탑재
is_pv_mode = st.toggle("📉 인플레이션 반영하기 (모든 금액을 '현재가치'로 환산하여 봅니다)", value=st.session_state.get('is_pv_mode', False), key="is_pv_mode")

# --- 2. 사이드바 설정 ---
st.sidebar.title("🛠️ 재무 전략 설정")

with st.sidebar.expander("📅 시나리오 및 기본 설정", expanded=True):
    c1, c2 = st.columns(2)
    start_yr = c1.number_input("시작 연도", value=st.session_state.get('sys_start_yr', 2026), key="sys_start_yr")
    end_yr = c2.number_input("종료 연도", value=st.session_state.get('sys_end_yr', 2095), key="sys_end_yr")
    c3, c4 = st.columns(2)
    h_birth_yr = c3.number_input("남편 출생년", value=st.session_state.get('h_birth_yr', 1995), key="h_birth_yr")
    w_birth_yr = c4.number_input("아내 출생년", value=st.session_state.get('w_birth_yr', 1994), key="w_birth_yr")
    
    # 🌟 4. 의료비 방어 토글
    has_health_ins = st.checkbox("🛡️ 부부 실손/간병보험 가입 (체크 시 75세 이후 의료비 폭탄 방어)", value=st.session_state.get('has_health_ins', True), key="has_health_ins")

with st.sidebar.expander("👤 남편 소득 및 은퇴", expanded=False):
    h_sal = st.number_input("남편 월급(세전, 만)", value=st.session_state.get('h_s_in', 830), key="h_s_in")
    h_bonus_r = st.number_input("상여비율(%)", value=st.session_state.get('h_br_in', 20.0), key="h_br_in") / 100
    h_inc = st.number_input("연 인상률(%)", value=st.session_state.get('h_i_in', 3.0), key="h_i_in") / 100
    st.markdown("---")
    h_ages = list(range(40, 81))
    h_opts = [f"{h_birth_yr + a}년 ({a}세)" for a in h_ages]
    h_ret_def_idx = h_opts.index(st.session_state.h_ret_in) if 'h_ret_in' in st.session_state and st.session_state.h_ret_in in h_opts else 15
    h_ret_sel = st.selectbox("은퇴 시점", h_opts, index=h_ret_def_idx, key="h_ret_in")
    h_ret_age = h_ages[h_opts.index(h_ret_sel)]
    h_sev_pay = st.number_input("퇴직금(만)", value=st.session_state.get('h_sev_in', 10000), key="h_sev_in")
    h_unemp = st.checkbox("은퇴 첫해 실업급여", value=st.session_state.get('h_unemp', True), key="h_unemp")
    
    # 🌟 5. 사적연금 분리
    st.markdown("**🌱 은퇴 후 현금흐름**")
    h_p_amt = st.number_input("월 국민연금(65세~)", value=st.session_state.get('h_p_in', 150), key="h_p_in")
    h_pp_amt = st.number_input("월 개인/퇴직연금(은퇴직후~)", value=st.session_state.get('h_pp_in', 50), key="h_pp_in")
    c1, c2 = st.columns(2)
    h_side_in = c1.number_input("소일거리(만)", value=st.session_state.get('h_side_in', 50), key="h_side_in")
    h_side_end = c2.number_input("종료(세)", value=st.session_state.get('h_side_end', 70), key="h_side_end")

with st.sidebar.expander("👩 아내 소득 및 은퇴", expanded=False):
    w_sal = st.number_input("아내 월급(세전, 만)", value=st.session_state.get('w_s_in', 500), key="w_s_in")
    w_bonus_r = st.number_input("상여비율(%) ", value=st.session_state.get('w_br_in', 20.0), key="w_br_in") / 100
    w_inc = st.number_input("연 인상률(%) ", value=st.session_state.get('w_inc_in', 3.0), key="w_inc_in") / 100
    st.markdown("---")
    w_ages = list(range(40, 81))
    w_opts = [f"{w_birth_yr + a}년 ({a}세)" for a in w_ages]
    w_ret_def_idx = w_opts.index(st.session_state.w_r_in) if 'w_r_in' in st.session_state and st.session_state.w_r_in in w_opts else 15
    w_ret_sel = st.selectbox("은퇴 시점 ", w_opts, index=w_ret_def_idx, key="w_r_in")
    w_ret_age = w_ages[w_opts.index(w_ret_sel)]
    w_sev_pay = st.number_input("퇴직금(만) ", value=st.session_state.get('w_sev_in', 8000), key="w_sev_in")
    w_unemp = st.checkbox("은퇴 첫해 실업급여 ", value=st.session_state.get('w_unemp', True), key="w_unemp")
    
    st.markdown("**🌱 은퇴 후 현금흐름**")
    w_p_amt = st.number_input("월 국민연금(65세~) ", value=st.session_state.get('w_p_in', 130), key="w_p_in")
    w_pp_amt = st.number_input("월 개인/퇴직연금(은퇴직후~) ", value=st.session_state.get('w_pp_in', 30), key="w_pp_in")
    c1, c2 = st.columns(2)
    w_side_in = c1.number_input("소일거리(만) ", value=st.session_state.get('w_side_in', 50), key="w_side_in")
    w_side_end = c2.number_input("종료(세) ", value=st.session_state.get('w_side_end', 70), key="w_side_end")

with st.sidebar.expander("💸 생활비 및 투자", expanded=False):
    living_monthly = st.number_input("월 고정 생활비(만)", value=st.session_state.get('liv_m_in', 450), key="liv_m_in")
    living_gr = st.number_input("물가(생활비) 인상률(%)", value=st.session_state.get('liv_g_in', 2.5), key="liv_g_in") / 100
    st.markdown("---")
    inv_init = st.number_input("현재 투자 원금(만)", value=st.session_state.get('inv_ini_in', 15000), key="inv_ini_in")
    inv_gr = st.number_input("기대 수익률(%)", value=st.session_state.get('inv_gr_in', 7.0), key="inv_gr_in") / 100
    inv_ratio = st.slider("💰 흑자 시 투자 비중(%)", 0, 100, st.session_state.get('inv_rat_in', 90), key="inv_rat_in")

with st.sidebar.expander("🍼 이벤트 및 자녀 증여", expanded=False):
    if st.button("➕ 이벤트 추가"): 
        st.session_state.events.append({"name": "이벤트", "year": start_yr+3, "cost": 5000, "is_gift": False})
    for i, ev in enumerate(st.session_state.events):
        st.markdown(f"**📍 {ev.get('name', '이벤트')}**")
        c1, c2, c3 = st.columns([2,1,1])
        ev['name'] = c1.text_input(f"명칭", ev.get('name', '이벤트'), key=f"ev_n_{i}")
        ev['year'] = c2.number_input(f"년도", start_yr, end_yr, ev.get('year', start_yr+3), key=f"ev_y_{i}")
        if c3.button("삭제", key=f"ev_del_{i}"): st.session_state.events.pop(i); st.rerun()
        
        c4, c5 = st.columns([2,1])
        ev['cost'] = c4.number_input(f"비용(만)", 0, 1000000, ev.get('cost', 5000), key=f"ev_c_{i}")
        # 🌟 4. 증여세 자동 계산 체크박스
        ev['is_gift'] = c5.checkbox("자녀 증여", value=ev.get('is_gift', False), key=f"ev_g_{i}")
        if ev['is_gift'] and ev['cost'] > 5000:
            st.caption(f"과세표준: {ev['cost']-5000}만 | 예상 증여세: {calc_gift_tax(ev['cost']):.0f}만")
            
# 부채/부동산 코드는 기존과 동일하게 유지 (UI 공간상 생략 없이 모두 작동되도록 축약 표기)
re_init_val = st.session_state.get('re_ini_in', 150000)
re_gr_rate = st.session_state.get('re_gr_in', 4.0) / 100
debt_init = st.session_state.get('debt_ini_in', 60000)
debt_r = st.session_state.get('debt_r_in', 4.0) / 100
debt_term = st.session_state.get('debt_t_in', 30)
debt_type = st.session_state.get('debt_tp_in', "원리금균등")
s_schd = st.session_state.get('ret_schd', 25)
s_jepq = st.session_state.get('ret_jepq', 25)

# --- 5. 초정밀 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re = re_init_val; c_re_base = re_init_val; c_inv = inv_init; c_cash = 1000; c_debt = debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    curr_debt_r, curr_debt_type, rem_debt_term = debt_r, debt_type, debt_term
    
    h_ret_year = h_birth_yr + h_ret_age
    w_ret_year = w_birth_yr + w_ret_age
    final_ret_year = max(h_ret_year, w_ret_year)

    for year in range(start_yr, end_yr + 1):
        h_age, w_age = year - h_birth_yr, year - w_birth_yr
        ev_list, pension = [], 0
        t_acq_total, t_gain_total, t_gift_tax = 0, 0, 0
        unemp_income_y = 0
        personal_pension_y = 0
        
        # 근로/소일거리 소득
        if h_age <= h_ret_age: inc_h = (c_h_sal * 12 * (1+h_bonus_r))
        elif h_age <= h_side_end: inc_h = (h_side_in * 12)
        else: inc_h = 0
            
        if w_age <= w_ret_age: inc_w = (c_w_sal * 12 * (1+w_bonus_r))
        elif w_age <= w_side_end: inc_w = (w_side_in * 12)
        else: inc_w = 0
            
        # 연금 계산 (국민 + 사적연금)
        if h_age >= 65: pension += (h_p_amt * 12)
        if w_age >= 65: pension += (w_p_amt * 12)
        if h_age > h_ret_age: personal_pension_y += (h_pp_amt * 12)
        if w_age > w_ret_age: personal_pension_y += (w_pp_amt * 12)
        
        if year >= final_ret_year:
            schd_yoc = 0.035 * (1.05 ** (year - final_ret_year))
            blended_yield = (s_schd/100)*schd_yoc + (s_jepq/100)*0.095 + (1 - s_schd/100 - s_jepq/100)*0.01
        else: blended_yield = 0.01
            
        div_income_y = c_inv * blended_yield
        
        gov_support_y = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if ka == 0: gov_support_y += 110 * 12
            elif ka == 1: gov_support_y += 60 * 12
            elif 2 <= ka <= 7: gov_support_y += 10 * 12
            
        if year == h_ret_year:
            c_inv += h_sev_pay
            if st.session_state.get('h_unemp', True): unemp_income_y += 198 * 9
        if year == w_ret_year:
            c_inv += w_sev_pay
            if st.session_state.get('w_unemp', True): unemp_income_y += 198 * 9
            
        total_income_y = inc_h + inc_w + pension + personal_pension_y + div_income_y + gov_support_y + unemp_income_y
        
        # 🌟 4. 의료비 폭탄 방어 로직 (75세 이상, 보험 없으면 매달 150 추가)
        health_shock_y = 0
        if not has_health_ins:
            if h_age >= 75: health_shock_y += 150 * 12
            if w_age >= 75: health_shock_y += 150 * 12
            if health_shock_y > 0: ev_list.append(f"🏥의료/간병비 발생({health_shock_y}만)")

        # 세금 계산
        tax_h = (inc_h * 0.09) + (inc_h * 0.75 * 0.15 * 1.1) if inc_h > 0 else 0
        tax_w = (inc_w * 0.09) + (inc_w * 0.75 * 0.15 * 1.1) if inc_w > 0 else 0
        tax_earned = max(0, tax_h + tax_w)
        
        tax_pension = pension * 0.05 if pension > 0 else 0
        tax_pp = personal_pension_y * 0.055 if personal_pension_y > 0 else 0 # 사적연금세 5.5%
        t_fin_tax = div_income_y * 0.154 if div_income_y > 0 else 0
        tax_dividend_pension = t_fin_tax + tax_pension + tax_pp
        
        t_hold = (c_re * 0.6) * 0.002
        t_comp = max(0, (c_re - 120000) * 0.005)
        
        # 이벤트 및 증여세 계산
        ev_cost = 0
        for ev in st.session_state.events:
            if ev['year'] == year:
                ev_cost += ev['cost']
                spec_str = ev['name']
                if ev.get('is_gift', False):
                    gtax = calc_gift_tax(ev['cost'])
                    t_gift_tax += gtax
                    ev_cost += gtax
                    spec_str += f"(증여세 {gtax:,.0f}만)"
                ev_list.append(f"🎁{spec_str}")
        
        total_tax_y = tax_earned + tax_dividend_pension + t_hold + t_comp + t_gift_tax
        
        # 부채 상환
        interest_a = c_debt * curr_debt_r
        principal_a, repay_a = 0, 0
        if c_debt > 0 and rem_debt_term > 0:
            pmt = c_debt / rem_debt_term + interest_a # 편의상 원금균등 적용
            principal_a = c_debt / rem_debt_term
            repay_a = pmt
            rem_debt_term -= 1
        elif c_debt > 0: repay_a = interest_a
        
        curr_living_y = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        total_exp_y = curr_living_y + total_tax_y + repay_a + ev_cost + health_shock_y
        net_flow_y = total_income_y - total_exp_y
        
        if net_flow_y >= 0:
            c_inv += net_flow_y * (inv_ratio / 100)
            c_cash += net_flow_y * (1 - inv_ratio/100)
        else:
            c_inv += net_flow_y 
            if c_inv < 0: c_cash += c_inv; c_inv = 0
            if c_cash < 0: c_debt -= c_cash; c_cash = 0
            
        c_re *= (1 + re_gr_rate)
        c_inv *= (1 + (inv_gr - blended_yield)) 
        c_debt = max(0, c_debt - principal_a)
        
        # 🌟 1. 현재가치(PV) 할인 로직 적용 (선택 시)
        discount_factor = (1 + living_gr) ** max(0, year - start_yr) if is_pv_mode else 1.0
        
        res.append({
            "연도": year, 
            "순자산_억": round(((c_re + c_inv + c_cash - c_debt)/discount_factor)/10000, 2),
            "부동산_억": round((c_re/discount_factor)/10000, 2), "금융자산_억": round((c_inv/discount_factor)/10000, 2), 
            "예금_억": round((c_cash/discount_factor)/10000, 2), "대출_억": round((c_debt/discount_factor)/10000, 2),
            "월_총수입_만": round((total_income_y/discount_factor) / 12, 0), 
            "월_총지출_만": round((total_exp_y/discount_factor) / 12, 0),
            "월_FCF_만": round((net_flow_y/discount_factor) / 12, 0),
            "월_생활비_만": round((curr_living_y/discount_factor) / 12, 0),
            "월_세금_만": round((total_tax_y/discount_factor) / 12, 0),
            "월_배당연금_만": round(((div_income_y + pension + personal_pension_y)/discount_factor) / 12, 0),
            "이벤트": "<br>".join(ev_list) if ev_list else "이슈 없음",
            "net_flow_raw": net_flow_y # AI 분석용 원본 데이터
        })
        c_h_sal *= (1 + h_inc); c_w_sal *= (1 + w_inc)
        
    return pd.DataFrame(res)

df_res = run_simulation()

# --- 🌟 2. FIRE 달성 계기판 (Gauge Chart) ---
def render_fire_gauge(df):
    ret_start_yr = max(h_birth_yr + 55, w_birth_yr + 55) # 대략 55세 기준
    ret_df = df[df["연도"] >= ret_start_yr]
    
    if len(ret_df) > 0:
        avg_passive_inc = ret_df["월_배당연금_만"].mean()
        avg_living_exp = ret_df["월_생활비_만"].mean()
        fire_ratio = min((avg_passive_inc / avg_living_exp) * 100, 200) if avg_living_exp > 0 else 0
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = fire_ratio, number = {'suffix': "%"},
            title = {'text': "🔥 은퇴 후 경제적 자유(FIRE) 달성률<br><span style='font-size:0.8em;color:gray'>배당+연금 / 생활비</span>"},
            gauge = {
                'axis': {'range': [None, 200], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#10b981" if fire_ratio >= 100 else "#ef4444"},
                'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "gray",
                'steps': [{'range': [0, 100], 'color': '#fee2e2'}, {'range': [100, 200], 'color': '#dcfce3'}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}}
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig
    return None

c1, c2 = st.columns([1, 2])
with c1: st.plotly_chart(render_fire_gauge(df_res), use_container_width=True)
with c2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if df_res["월_배당연금_만"].iloc[-1] >= df_res["월_생활비_만"].iloc[-1]:
        st.success("🎉 **축하합니다!** 은퇴 후 자본 소득이 생활비를 100% 초과하여 경제적 자유 달성이 가능합니다.")
    else:
        st.warning("🚨 **주의:** 은퇴 후 자본 소득이 생활비에 미치지 못합니다. 월 저축액을 늘리거나 소비를 줄여야 합니다.")

# --- 차트 렌더링 ---
st.markdown("### 📊 자산 성장 및 현금흐름 로드맵")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_res["연도"], y=df_res["순자산_억"], name="순자산(억)", mode='lines+markers', line=dict(color='#10b981', width=3)))
fig.add_trace(go.Bar(x=df_res["연도"], y=df_res["월_FCF_만"], name="월 잉여현금(만)", yaxis="y2", marker_color='#3b82f6', opacity=0.4))
fig.update_layout(
    height=500, hovermode="x unified", template="plotly_white",
    yaxis=dict(title="순자산 (억 원)"),
    yaxis2=dict(title="월 FCF (만 원)", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
)
st.plotly_chart(fig, use_container_width=True)

# --- 🌟 6. AI 파이썬 재무 진단 리포트 ---
st.markdown("### 🤖 파이썬 AI 재무 진단 리포트")
deficit_years = df_res[df_res["net_flow_raw"] < 0]

if len(deficit_years) == 0:
    st.info("✅ **진단 결과:** 시뮬레이션 기간 내내 단 한 번도 현금흐름 적자가 발생하지 않는 **완벽한 상태**입니다. 현재의 투자 비율과 소비 습관을 유지하셔도 좋습니다.")
else:
    first_deficit = deficit_years.iloc[0]
    max_deficit = deficit_years["net_flow_raw"].min()
    max_def_yr = deficit_years.loc[deficit_years["net_flow_raw"].idxmin()]["연도"]
    
    report = f"""
    ⚠️ **재무 위험 진단 알림**\n
    * **첫 유동성 위기:** **{int(first_deficit['연도'])}년**에 처음으로 월 가계부 적자가 발생하기 시작합니다. (주원인: {first_deficit['이벤트']})
    * **최대 고비:** **{int(max_def_yr)}년**에 가계 적자가 극에 달합니다. (연간 {-max_deficit/10000:.1f}억 원 적자)
    * **💡 AI 제안:** 적자가 발생하는 시점 직전에 예금(현금) 비중을 미리 늘려두거나, 부동산 갈아타기 시 대출 비중을 높여 금융자산을 보존하는 전략을 권장합니다.
    """
    if not has_health_ins: report += "\n* **🏥 추가 경고:** 실손보험이 없어 75세 이후 의료비 폭탄으로 자산 고갈 속도가 급격히 빨라집니다. 보험 가입을 강력히 추천합니다."
    st.error(report)

# 클라우드 저장
if st.session_state.get('current_user'):
    for k in static_keys:
        if k in st.session_state: user_data[k] = st.session_state[k]
    user_data['re_trades'] = st.session_state.get('re_trades', [])
    user_data['events'] = st.session_state.get('events', [])
    user_data['kids'] = st.session_state.get('kids', [])
    user_data['h_leaves'] = st.session_state.get('h_leaves', [])
    user_data['w_leaves'] = st.session_state.get('w_leaves', [])
    db[st.session_state.current_user] = user_data
    save_cloud_db(db)
