import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import urllib.request

# =====================================================================
# ☁️ 회원님의 전용 클라우드 DB 주소
# =====================================================================
FIREBASE_URL = "https://familiy-financial-plan-default-rtdb.asia-southeast1.firebasedatabase.app/finance_db.json"

# 1. 페이지 설정 및 프리미엄 디자인 UI/UX
st.set_page_config(page_title="우리 가족 자산 마스터 (Cloud Ver.)", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; font-size: 20px !important; }
    section[data-testid="stSidebar"] { background-color: #e0f2fe !important; border-right: 1px solid #bae6fd; }
    section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stHeader, section[data-testid="stSidebar"] .stSelectbox label { color: #000000 !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 6px solid #0ea5e9; }
    .stTabs [data-baseweb="tab"] { font-size: 22px !important; font-weight: 700; padding: 12px 30px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: 700; background-color: #0ea5e9; color: white; height: 3.5rem; }
    [data-testid="stDataFrame"] { font-family: 'Noto Sans KR', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 클라우드 데이터 통신 함수 ---
def load_cloud_db():
    try:
        req = urllib.request.Request(FIREBASE_URL)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data if data else {}
    except Exception:
        return {}

def save_cloud_db(db_data):
    try:
        req = urllib.request.Request(FIREBASE_URL, data=json.dumps(db_data).encode('utf-8'), method='PUT')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req)
    except Exception as e:
        st.sidebar.error("클라우드 저장 실패! 인터넷 연결을 확인해주세요.")

# --- 정밀 소득세 & 4대보험 계산 엔진 ---
def get_annual_tax_and_insurance(gross_income_manwon):
    if gross_income_manwon <= 0: return 0
    insurance = gross_income_manwon * 0.09
    tax_base = gross_income_manwon * 0.75
    if tax_base <= 1400: tax = tax_base * 0.06
    elif tax_base <= 5000: tax = 84 + (tax_base - 1400) * 0.15
    elif tax_base <= 8800: tax = 624 + (tax_base - 5000) * 0.24
    elif tax_base <= 15000: tax = 1536 + (tax_base - 8800) * 0.35
    elif tax_base <= 30000: tax = 3706 + (tax_base - 15000) * 0.38
    elif tax_base <= 50000: tax = 9406 + (tax_base - 30000) * 0.40
    elif tax_base <= 100000: tax = 17406 + (tax_base - 50000) * 0.42
    else: tax = 38406 + (tax_base - 100000) * 0.45
    return insurance + (tax * 1.1)

# --- 3. 클라우드 계정 로그인 UI ---
db = load_cloud_db()

st.sidebar.title("☁️ 클라우드 계정 연동")
user_id = st.sidebar.text_input("아이디를 입력하세요 (예: ethan123)", key="login_id")

if not user_id:
    st.markdown(f"<h1 style='text-align: center; margin-top: 100px;'>👨‍👩‍👧‍👦 우리 가족 자산 마스터 (Cloud Ver.)</h1>", unsafe_allow_html=True)
    st.info("👈 **왼쪽 사이드바에 '아이디'를 입력해주세요.**\n\n(아무 아이디나 입력하시면 즉시 나만의 전용 클라우드 데이터베이스가 생성됩니다. 다른 기기에서도 해당 아이디만 입력하면 데이터를 그대로 불러옵니다!)", icon="🚀")
    st.stop()

# 🌟 업데이트: 로그인 세션 바인딩 및 에러 원천 차단 안전장치
user_data = db.get(user_id, {})

if 'current_user' not in st.session_state or st.session_state.current_user != user_id:
    st.session_state.current_user = user_id
    
    static_keys = [
        'sys_start_yr', 'sys_end_yr', 'h_birth_yr', 'w_birth_yr', 
        'h_s_in', 'h_br_in', 'h_i_in', 'h_promo_yr', 'h_promo_r', 'h_ret_in', 'h_sev_in', 'h_p_in', 'h_side_in', 'h_side_end',
        'w_s_in', 'w_br_in', 'w_inc_in', 'w_promo_yr', 'w_promo_r', 'w_r_in', 'w_sev_in', 'w_p_in', 'w_side_in', 'w_side_end',
        'liv_m_in', 'liv_g_in', 'inv_ini_in', 'inv_gr_in', 'inv_rat_in', 
        'debt_ini_in', 'debt_r_in', 'debt_t_in', 'debt_tp_in', 're_ini_in', 're_gr_in', 
        'ret_down_r', 'ret_debt_r', 'ret_schd', 'ret_jepq', 'h_unemp', 'w_unemp'
    ]
    for k in static_keys:
        if k in user_data:
            st.session_state[k] = user_data[k]

# 이미 로그인된 상태라도 리스트형 데이터가 없으면 무조건 생성해주는 안전장치
if 're_trades' not in st.session_state: st.session_state.re_trades = user_data.get('re_trades', [])
if 'events' not in st.session_state: st.session_state.events = user_data.get('events', [])
if 'kids' not in st.session_state: st.session_state.kids = user_data.get('kids', [{"name": "첫째", "birth": 2027, "costs": [100, 150, 200, 250, 300]}])
if 'h_leaves' not in st.session_state: st.session_state.h_leaves = user_data.get('h_leaves', [])
if 'w_leaves' not in st.session_state: st.session_state.w_leaves = user_data.get('w_leaves', [])


st.sidebar.success(f"🟢 **{user_id}** 계정 접속됨 (클라우드 실시간 저장 중)")
st.sidebar.markdown("---")

st.title("👨‍👩‍👧‍👦 우리 가족 통합 자산 프로젝션 v18.0 (정책 고증)")
st.markdown("---")

# --- 4. 사이드바: 설정 레버 ---
st.sidebar.title("🛠️ 재무 전략 설정")

with st.sidebar.expander("📅 시나리오 및 기본 설정", expanded=True):
    c1, c2 = st.columns(2)
    start_yr = c1.number_input("시작 연도", value=st.session_state.get('sys_start_yr', 2026), min_value=2024, key="sys_start_yr")
    end_yr = c2.number_input("종료 연도", value=st.session_state.get('sys_end_yr', 2095), min_value=start_yr+10, max_value=2150, key="sys_end_yr")
    c3, c4 = st.columns(2)
    h_birth_yr = c3.number_input("남편 출생년도", value=st.session_state.get('h_birth_yr', 1995), min_value=1950, max_value=2010, key="h_birth_yr")
    w_birth_yr = c4.number_input("아내 출생년도", value=st.session_state.get('w_birth_yr', 1994), min_value=1950, max_value=2010, key="w_birth_yr")

with st.sidebar.expander("👤 부부 소득(세전) 및 휴직/은퇴", expanded=True):
    h_tab, w_tab = st.tabs([f"남편({str(h_birth_yr)[-2:]})", f"아내({str(w_birth_yr)[-2:]})"])
    
    with h_tab:
        h_sal = st.number_input("남편 월급(세전, 만)", value=st.session_state.get('h_s_in', 830), key="h_s_in")
        h_bonus_r = st.number_input("남편 상여비율(%)", value=st.session_state.get('h_br_in', 20.0), key="h_br_in") / 100
        h_inc = st.number_input("매년 급여 인상률(%)", value=st.session_state.get('h_i_in', 3.0), key="h_i_in") / 100
        
        st.markdown("**🚀 승진 시점 연봉 점프**")
        c1, c2 = st.columns(2)
        h_promo_yr = c1.number_input("승진 예상 연도", value=st.session_state.get('h_promo_yr', start_yr+4), min_value=start_yr, key="h_promo_yr")
        h_promo_r = c2.number_input("승진 인상률(%)", value=st.session_state.get('h_promo_r', 15.0), key="h_promo_r") / 100
        
        st.markdown("**👶 육아휴직 계획**")
        if st.button("➕ 남편 육아휴직 추가", key="add_h_leave"):
            st.session_state.h_leaves.append({"year": start_yr+1, "mos": 6, "pay": 150})
        for i, lv in enumerate(st.session_state.h_leaves):
            c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
            lv['year'] = c1.number_input(f"휴직 연도{i}", start_yr, end_yr, lv.get('year', start_yr+1), key=f"hl_y_{i}")
            lv['mos'] = c2.number_input(f"기간(월){i}", 1, 12, lv.get('mos', 6), key=f"hl_m_{i}")
            lv['pay'] = c3.number_input(f"월급여(만){i}", value=lv.get('pay', 150), key=f"hl_p_{i}")
            if c4.button("삭제", key=f"hl_del_{i}"):
                st.session_state.h_leaves.pop(i)
                st.rerun()
        
        st.markdown("---")
        h_ages = list(range(40, 81))
        h_opts = [f"{h_birth_yr + a}년 ({a}세)" for a in h_ages]
        h_ret_def_idx = h_ages.index(55) if 55 in h_ages else 0
        if 'h_ret_in' in st.session_state and st.session_state.h_ret_in in h_opts:
            h_ret_def_idx = h_opts.index(st.session_state.h_ret_in)
        h_ret_sel = st.selectbox("남편 은퇴 시점", h_opts, index=h_ret_def_idx, key="h_ret_in")
        h_ret_age = h_ages[h_opts.index(h_ret_sel)]
        h_sev_pay = st.number_input("예상 퇴직금(만)", value=st.session_state.get('h_sev_in', 10000), step=1000, key="h_sev_in")
        
        h_unemp = st.checkbox("은퇴 첫해 실업급여 수령 (9개월, 약 1,780만 원)", value=st.session_state.get('h_unemp', True), key="h_unemp")
        
        st.markdown("**🌱 은퇴 후 현금흐름**")
        h_p_amt = st.number_input("월 예상 공적연금(65세~)", value=st.session_state.get('h_p_in', 150), key="h_p_in")
        c1, c2 = st.columns(2)
        h_side_in = c1.number_input("소일거리 월급(만)", value=st.session_state.get('h_side_in', 50), step=10, key="h_side_in")
        h_side_end = c2.number_input("종료 나이(세)", value=st.session_state.get('h_side_end', 70), min_value=h_ret_age, max_value=100, key="h_side_end")
        
    with w_tab:
        w_sal = st.number_input("아내 월급(세전, 만)", value=st.session_state.get('w_s_in', 500), key="w_s_in")
        w_bonus_r = st.number_input("아내 상여비율(%)", value=st.session_state.get('w_br_in', 20.0), key="w_br_in") / 100
        w_inc = st.number_input("매년 급여 인상률(%)", value=st.session_state.get('w_inc_in', 3.0), key="w_inc_in") / 100
        
        st.markdown("**🚀 승진 시점 연봉 점프**")
        c1, c2 = st.columns(2)
        w_promo_yr = c1.number_input("승진 예상 연도 ", value=st.session_state.get('w_promo_yr', start_yr+3), min_value=start_yr, key="w_promo_yr")
        w_promo_r = c2.number_input("승진 인상률(%) ", value=st.session_state.get('w_promo_r', 15.0), key="w_promo_r") / 100
        
        st.markdown("**👶 육아휴직 계획**")
        if st.button("➕ 아내 육아휴직 추가", key="add_w_leave"):
            st.session_state.w_leaves.append({"year": start_yr+1, "mos": 12, "pay": 150})
        for i, lv in enumerate(st.session_state.w_leaves):
            c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
            lv['year'] = c1.number_input(f"휴직 연도 {i}", start_yr, end_yr, lv.get('year', start_yr+1), key=f"wl_y_{i}")
            lv['mos'] = c2.number_input(f"기간(월) {i}", 1, 12, lv.get('mos', 12), key=f"wl_m_{i}")
            lv['pay'] = c3.number_input(f"월급여(만) {i}", value=lv.get('pay', 150), key=f"wl_p_{i}")
            if c4.button("삭제", key=f"wl_del_{i}"):
                st.session_state.w_leaves.pop(i)
                st.rerun()
        
        st.markdown("---")
        w_ages = list(range(40, 81))
        w_opts = [f"{w_birth_yr + a}년 ({a}세)" for a in w_ages]
        w_ret_def_idx = w_ages.index(55) if 55 in w_ages else 0
        if 'w_r_in' in st.session_state and st.session_state.w_r_in in w_opts:
            w_ret_def_idx = w_opts.index(st.session_state.w_r_in)
        w_ret_sel = st.selectbox("아내 은퇴 시점", w_opts, index=w_ret_def_idx, key="w_r_in")
        w_ret_age = w_ages[w_opts.index(w_ret_sel)]
        w_sev_pay = st.number_input("예상 퇴직금(만) ", value=st.session_state.get('w_sev_in', 8000), step=1000, key="w_sev_in")
        
        w_unemp = st.checkbox("은퇴 첫해 실업급여 수령 (9개월, 약 1,780만 원) ", value=st.session_state.get('w_unemp', True), key="w_unemp")
        
        st.markdown("**🌱 은퇴 후 현금흐름**")
        w_p_amt = st.number_input("아내 월 예상연금(65세~)", value=st.session_state.get('w_p_in', 130), key="w_p_in")
        c1, c2 = st.columns(2)
        w_side_in = c1.number_input("소일거리 월급(만) ", value=st.session_state.get('w_side_in', 50), step=10, key="w_side_in")
        w_side_end = c2.number_input("종료 나이(세) ", value=st.session_state.get('w_side_end', 70), min_value=w_ret_age, max_value=100, key="w_side_end")

with st.sidebar.expander("💸 생활비 레버", expanded=False):
    living_monthly = st.number_input("월 고정 생활비(만)", value=st.session_state.get('liv_m_in', 450), key="liv_m_in")
    living_gr = st.number_input("생활비 인상률(%)", value=st.session_state.get('liv_g_in', 2.5), key="liv_g_in") / 100

with st.sidebar.expander("📈 금융 투자 자산 설정", expanded=False):
    inv_init = st.number_input("현재 투자 원금(만)", value=st.session_state.get('inv_ini_in', 15000), key="inv_ini_in")
    inv_gr = st.number_input("기대 수익률(%)", value=st.session_state.get('inv_gr_in', 7.0), key="inv_gr_in") / 100
    inv_ratio = st.slider("💰 흑자 시 투자 비중(%)", 0, 100, st.session_state.get('inv_rat_in', 90), key="inv_rat_in")

with st.sidebar.expander("💳 대출 및 상환 방식", expanded=False):
    st.markdown("**기존 대출 설정**")
    debt_init = st.number_input("현재 대출 잔액(만)", value=st.session_state.get('debt_ini_in', 60000), key="debt_ini_in")
    debt_r = st.number_input("기본 대출 금리(%)", value=st.session_state.get('debt_r_in', 4.0), key="debt_r_in") / 100
    debt_term = st.number_input("상환 기간(년)", value=st.session_state.get('debt_t_in', 30), key="debt_t_in")
    
    dt_idx = 0 if st.session_state.get('debt_tp_in', "원리금균등") == "원리금균등" else 1
    debt_type = st.selectbox("상환 방식 선택", ["원리금균등", "원금균등"], index=dt_idx, key="debt_tp_in")
    
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
    re_init_val = st.number_input("현재 집 가액(만)", value=st.session_state.get('re_ini_in', 150000), key="re_ini_in")
    re_gr_rate = st.number_input("부동산 상승률(%)", value=st.session_state.get('re_gr_in', 4.0), key="re_gr_in") / 100
    if st.button("➕ 갈아타기 추가"):
        st.session_state.re_trades.append({"year": start_yr+10, "new_price": 250000, "use_inv": 60000, "new_debt_amt": 80000, "use_cash": 0})
    
    temp_price = re_init_val
    temp_yr = start_yr
    for i, tr in enumerate(st.session_state.re_trades):
        st.markdown(f"**📍 계획 #{i+1}**")
        tr['year'] = st.number_input(f"매수 연도 {i}", start_yr, end_yr, tr.get('year', start_yr+10), key=f"tr_y_{i}")
        tr['new_price'] = st.number_input(f"신규 주택 매수가(만) {i}", value=tr.get('new_price', 250000), step=10000, key=f"tr_np_{i}")
        
        est_price = temp_price * ((1 + re_gr_rate)**(max(0, tr['year'] - temp_yr)))
        est_gain = max(0, est_price - re_init_val) * 0.20
        est_sale = est_price - est_gain
        acq_tax = tr['new_price'] * 0.033
        
        years_passed = max(0, tr['year'] - start_yr)
        est_rem_debt = max(0, debt_init - (debt_init / debt_term * years_passed)) if debt_term > 0 else 0
        gap = tr['new_price'] + acq_tax - est_sale + est_rem_debt
        
        st.info(f"💡 **[예상 필요 조달액: 약 {gap/10000:.2f}억]**\n"
                f"신규주택({tr['new_price']/10000:.1f}억) + 취득세 + 기존대출상환 - 기존주택매각")
        st.caption("🔻 위 금액에 맞춰 신규대출/금융매도/예금사용을 세팅하세요.")
        
        c1, c2, c3 = st.columns(3)
        tr['new_debt_amt'] = c1.number_input(f"신규 대출 총액{i}", value=tr.get('new_debt_amt', 80000), step=5000, key=f"tr_debt_{i}")
        tr['use_inv'] = c2.number_input(f"금융 매도(만){i}", value=tr.get('use_inv', 60000), step=1000, key=f"tr_inv_{i}")
        tr['use_cash'] = c3.number_input(f"보유 예금(만){i}", value=tr.get('use_cash', 0), step=1000, key=f"tr_cash_{i}")
        
        temp_price = tr['new_price']
        temp_yr = tr['year']
        if st.button(f"🗑️ 계획 #{i+1} 삭제", key=f"re_del_{i}"): 
            st.session_state.re_trades.pop(i)
            st.rerun()

with st.sidebar.expander("🍼 자녀 & 특별 이벤트", expanded=False):
    if st.button("➕ 자녀 추가"): 
        st.session_state.kids.append({"name": f"자녀{len(st.session_state.kids)+1}", "birth": start_yr+1, "costs": [100, 150, 200, 250, 300]})
    for i, kid in enumerate(st.session_state.kids):
        col1, col2 = st.columns([3, 1])
        col1.write(f"👶 **{kid['name']}**")
        if col2.button("삭제", key=f"k_del_{i}"):
            st.session_state.kids.pop(i)
            st.rerun()
        kid['birth'] = st.number_input(f"출생년 {i}", 1990, end_yr, kid.get('birth', 2027), key=f"kb_{i}")
        c1, c2 = st.columns(2)
        kid['costs'][0] = c1.number_input(f"영유아 {i}", value=kid['costs'][0], key=f"kc0_{i}")
        kid['costs'][1] = c2.number_input(f"초등 {i}", value=kid['costs'][1], key=f"kc1_{i}")
        kid['costs'][2] = c1.number_input(f"중등 {i}", value=kid['costs'][2], key=f"kc2_{i}")
        kid['costs'][3] = c2.number_input(f"고등 {i}", value=kid['costs'][3], key=f"kc3_{i}")
        kid['costs'][4] = c1.number_input(f"대학 {i}", value=kid['costs'][4], key=f"kc4_{i}")
    
    st.markdown("---")
    if st.button("➕ 이벤트 추가"): 
        st.session_state.events.append({"name": "이벤트", "year": start_yr+3, "cost": 6000})
    for i, ev in enumerate(st.session_state.events):
        col1, col2 = st.columns([3, 1])
        ev['name'] = col1.text_input(f"명칭 {i}", ev.get('name', '이벤트'), key=f"ev_n_{i}")
        if col2.button("삭제", key=f"ev_del_{i}"):
            st.session_state.events.pop(i)
            st.rerun()
        ev['year'] = st.number_input(f"년도 {i}", start_yr, end_yr, ev.get('year', start_yr+3), key=f"ev_y_{i}")
        ev['cost'] = st.number_input(f"비용 {i}", 0, 1000000, ev.get('cost', 6000), key=f"ev_c_{i}")

with st.sidebar.expander("👵 은퇴 시점 리밸런싱 & 배당", expanded=False):
    st.markdown("**1️⃣ 주택 연금화 (다운사이징)**")
    ret_re_down_ratio = st.slider("최종 은퇴 시 부동산 매각 비율(%)", 0, 100, st.session_state.get('ret_down_r', 30), step=10, key="ret_down_r")
    st.caption("매각 대금은 양도세 정산 후 전액 금융자산으로 즉시 편입됩니다.")
    st.markdown("---")
    st.markdown("**2️⃣ 은퇴 시점 부채 상환**")
    ret_debt_payoff_ratio = st.slider("은퇴 시 부채 상환 비율(%)", 0, 100, st.session_state.get('ret_debt_r', 100), step=10, key="ret_debt_r")
    st.caption("상환 자금은 총 금융자산 내에서 우선 차감됩니다.")
    st.markdown("---")
    st.markdown("**3️⃣ 은퇴 후 금융자산 배분**")
    s_schd = st.slider("SCHD (배당성장) %", 0, 100, st.session_state.get('ret_schd', 25), key="ret_schd")
    s_jepq = st.slider("JEPQ (고배당) %", 0, 100, st.session_state.get('ret_jepq', 25), key="ret_jepq")
    st.info(f"기존 금융자산 유지(재투자): {100 - s_schd - s_jepq}%")

# --- 5. 시뮬레이션 엔진 ---
def run_simulation():
    res = []
    c_re = re_init_val
    c_re_base = re_init_val
    c_inv = inv_init
    c_cash = 1000  
    c_debt = debt_init
    c_h_sal, c_w_sal = h_sal, w_sal
    
    curr_debt_r = debt_r
    curr_debt_type = debt_type
    rem_debt_term = debt_term
    
    h_ret_year = h_birth_yr + h_ret_age
    w_ret_year = w_birth_yr + w_ret_age
    final_ret_year = max(h_ret_year, w_ret_year)

    for year in range(start_yr, end_yr + 1):
        h_age, w_age = year - h_birth_yr, year - w_birth_yr
        ev_list, pension = [], 0
        t_acq_total, t_gain_total = 0, 0
        unemp_income_y = 0
        
        if year == h_promo_yr and h_age <= h_ret_age:
            c_h_sal *= (1 + h_promo_r)
            ev_list.append(f"🎉남편 승진({h_promo_r*100:.0f}% 인상)")
        if year == w_promo_yr and w_age <= w_ret_age:
            c_w_sal *= (1 + w_promo_r)
            ev_list.append(f"🎉아내 승진({w_promo_r*100:.0f}% 인상)")
        
        h_work_mos, h_leave_inc = 12, 0
        h_leave_mos_total = 0
        for lv in st.session_state.h_leaves:
            if year == lv['year']:
                h_leave_mos_total += lv['mos']
                h_leave_inc += lv['pay'] * lv['mos']
                ev_list.append(f"👨‍🍼남편 육아휴직({lv['mos']}개월)")
        h_work_mos = max(0, 12 - h_leave_mos_total)
            
        w_work_mos, w_leave_inc = 12, 0
        w_leave_mos_total = 0
        for lv in st.session_state.w_leaves:
            if year == lv['year']:
                w_leave_mos_total += lv['mos']
                w_leave_inc += lv['pay'] * lv['mos']
                ev_list.append(f"👩‍🍼아내 육아휴직({lv['mos']}개월)")
        w_work_mos = max(0, 12 - w_leave_mos_total)
        
        if h_age <= h_ret_age: inc_h = (c_h_sal * h_work_mos * (1+h_bonus_r)) + h_leave_inc
        elif h_age <= h_side_end: inc_h = (h_side_in * 12)
        else: inc_h = 0
            
        if w_age <= w_ret_age: inc_w = (c_w_sal * w_work_mos * (1+w_bonus_r)) + w_leave_inc
        elif w_age <= w_side_end: inc_w = (w_side_in * 12)
        else: inc_w = 0
            
        if h_age >= 65: pension += (h_p_amt * 12)
        if w_age >= 65: pension += (w_p_amt * 12)
        
        if year >= final_ret_year:
            schd_yoc = 0.035 * (1.05 ** (year - final_ret_year))
            jepq_yield = 0.095 
            gen_yield = 0.01   
            blended_yield = (s_schd/100)*schd_yoc + (s_jepq/100)*jepq_yield + (1 - s_schd/100 - s_jepq/100)*gen_yield
        else:
            blended_yield = 0.01
            
        div_income_y = c_inv * blended_yield
        
        gov_support_y = 0
        tax_credit_kids = 0
        k_total = 0
        for kid in st.session_state.kids:
            ka = year - kid['birth']
            if ka == 0: gov_support_y += 110 * 12
            elif ka == 1: gov_support_y += 60 * 12
            elif 2 <= ka <= 7: gov_support_y += 10 * 12
            
            if 8 <= ka <= 20: tax_credit_kids += 1
            
            sch_stage = ""
            if ka == 7: sch_stage = f"👶{kid['name']} 초교 입학"
            elif ka == 13: sch_stage = f"🧒{kid['name']} 중교 입학"
            elif ka == 16: sch_stage = f"🧑{kid['name']} 고교 입학"
            elif ka == 19: sch_stage = f"👨‍🎓{kid['name']} 대학 입학"
            elif ka == 23: sch_stage = f"💼{kid['name']} 독립"
            
            if 0<=ka<=7: k_total += kid['costs'][0]*12
            elif 8<=ka<=13: k_total += kid['costs'][1]*12
            elif 14<=ka<=16: k_total += kid['costs'][2]*12
            elif 17<=ka<=19: k_total += kid['costs'][3]*12
            elif 20<=ka<=23: k_total += kid['costs'][4]*12
            
            if sch_stage: ev_list.append(sch_stage)
            if year == kid['birth']: ev_list.append(f"🍼{kid['name']} 탄생")
            
        if year == h_ret_year:
            c_inv += h_sev_pay
            if st.session_state.get('h_unemp', True): 
                unemp_income_y += 198 * 9
                ev_list.append("💼남편 실업급여 수령")
            ev_list.append(f"👨‍🦳남편 은퇴(퇴직금 {h_sev_pay//10000}억)")
        if year == w_ret_year:
            c_inv += w_sev_pay
            if st.session_state.get('w_unemp', True): 
                unemp_income_y += 198 * 9
                ev_list.append("💼아내 실업급여 수령")
            ev_list.append(f"👩‍🦳아내 은퇴(퇴직금 {w_sev_pay//10000}억)")
            
        total_income_y = inc_h + inc_w + pension + div_income_y + gov_support_y + unemp_income_y
        
        for tr in st.session_state.re_trades:
            if year == tr['year']:
                gain = max(0, c_re - c_re_base) * 0.20
                acq = tr['new_price'] * 0.033
                t_gain_total += gain
                t_acq_total += acq
                
                net_sale = c_re - gain
                need_amt = tr['new_price'] + acq + c_debt
                
                req_new_debt = tr.get('new_debt_amt', 80000)
                use_inv = tr.get('use_inv', 60000)
                use_cash = tr.get('use_cash', 0)
                
                actual_use_inv = min(c_inv, use_inv)
                actual_use_cash = min(c_cash, use_cash)
                
                c_inv -= actual_use_inv
                c_cash -= actual_use_cash
                
                total_funding = net_sale + req_new_debt + actual_use_inv + actual_use_cash
                surplus = total_funding - need_amt
                
                if surplus >= 0:
                    c_cash += surplus
                    c_debt = req_new_debt
                else:
                    deficit = abs(surplus)
                    if c_cash >= deficit: c_cash -= deficit
                    else:
                        deficit -= c_cash
                        c_cash = 0
                        if c_inv >= deficit: c_inv -= deficit
                        else:
                            deficit -= c_inv
                            c_inv = 0
                            req_new_debt += deficit 
                    c_debt = req_new_debt
                
                c_re = tr['new_price']
                c_re_base = tr['new_price']
                curr_debt_r = tr.get('new_debt_r', curr_debt_r)
                curr_debt_type = tr.get('new_debt_type', curr_debt_type)
                rem_debt_term = tr.get('new_debt_term', debt_term)
                ev_list.append("🏠부동산 갈아타기")

        if year == final_ret_year:
            if ret_re_down_ratio > 0:
                down_ratio = ret_re_down_ratio / 100
                downsize_amt = c_re * down_ratio
                base_cost = c_re_base * down_ratio
                ds_gain = max(0, downsize_amt - base_cost) * 0.20
                t_gain_total += ds_gain
                net_proceeds = downsize_amt - ds_gain
                c_inv += net_proceeds  
                c_re -= downsize_amt
                c_re_base -= base_cost
                ev_list.append(f"📉주택축소({ret_re_down_ratio}%)")
                
            if ret_debt_payoff_ratio > 0 and c_debt > 0:
                payoff_target = c_debt * (ret_debt_payoff_ratio / 100)
                actual_payoff = min(payoff_target, c_inv)
                if actual_payoff > 0:
                    c_inv -= actual_payoff
                    c_debt -= actual_payoff
                    ev_list.append(f"💳부채상환({ret_debt_payoff_ratio}%)")

        tax_h = get_annual_tax_and_insurance(inc_h)
        tax_w = get_annual_tax_and_insurance(inc_w)
        
        child_tax_credit = 0
        if tax_credit_kids == 1: child_tax_credit = 15
        elif tax_credit_kids == 2: child_tax_credit = 30
        elif tax_credit_kids >= 3: child_tax_credit = 30 + (tax_credit_kids - 2) * 30
        
        tax_earned = max(0, tax_h + tax_w - child_tax_credit)
        
        tax_pension = pension * 0.05 if pension > 0 else 0
        t_fin_tax = div_income_y * 0.154 if div_income_y > 0 else 0
        tax_dividend_pension = t_fin_tax + tax_pension
        
        t_hold = (c_re * 0.6) * 0.002
        t_comp = max(0, (c_re - 120000) * 0.005)
        
        total_tax_y = tax_earned + tax_dividend_pension + t_hold + t_comp

        interest_a = c_debt * curr_debt_r
        principal_a, repay_a = 0, 0
        if c_debt > 0 and rem_debt_term > 0:
            if curr_debt_type == "원리금균등":
                if curr_debt_r > 0:
                    denom = ((1 + curr_debt_r) ** rem_debt_term) - 1
                    if denom > 0: pmt = (c_debt * curr_debt_r * ((1 + curr_debt_r) ** rem_debt_term)) / denom
                    else: pmt = c_debt / rem_debt_term
                else: pmt = c_debt / rem_debt_term
                principal_a = pmt - interest_a
                repay_a = pmt
            else:
                principal_a = c_debt / rem_debt_term
                repay_a = principal_a + interest_a
            rem_debt_term -= 1
        elif c_debt > 0:
            repay_a = interest_a
        
        ev_cost = sum(ev['cost'] for ev in st.session_state.events if ev['year'] == year)
        if ev_cost > 0:
            spec_ev_names = [ev['name'] for ev in st.session_state.events if ev['year'] == year]
            ev_list.append(f"🎁이벤트: {','.join(spec_ev_names)}")
        
        curr_living_y = (living_monthly * 12) * ((1 + living_gr)**(year - start_yr))
        total_exp_y = curr_living_y + k_total + total_tax_y + repay_a + ev_cost
        net_flow_y = total_income_y - total_exp_y
        
        if net_flow_y >= 0:
            c_inv += net_flow_y * (inv_ratio / 100)
            c_cash += net_flow_y * (1 - inv_ratio/100)
        else:
            c_inv += net_flow_y 
            if c_inv < 0:
                c_cash += c_inv  
                c_inv = 0
                if c_cash < 0:
                    c_debt -= c_cash 
                    c_cash = 0
            
        c_re *= (1 + re_gr_rate)
        effective_growth = inv_gr - blended_yield
        c_inv *= (1 + effective_growth) 
        c_debt = max(0, c_debt - principal_a)
        
        event_str_tooltip = "<br>".join(ev_list) if ev_list else "이슈 없음"
        
        res.append({
            "연도": year, "순자산_억": round((c_re + c_inv + c_cash - c_debt)/10000, 2),
            "총자산_억": round((c_re + c_inv + c_cash)/10000, 2),
            "부동산_억": round(c_re/10000, 2), "금융자산_억": round(c_inv/10000, 2), 
            "예금_억": round(c_cash/10000, 2), "대출_억": round(c_debt/10000, 2),
            
            "연_남편소득_만": round(inc_h, 0), "연_아내소득_만": round(inc_w, 0),
            "연_배당_만": round(div_income_y, 0), "연_연금_만": round(pension, 0),
            "연_정부지원_만": round(gov_support_y + unemp_income_y, 0), 
            "연_생활비_만": round(curr_living_y, 0), "연_양육비_만": round(k_total, 0),
            "연_원리금_만": round(repay_a, 0), "연_보유세_만": round(t_hold + t_comp, 0),
            "연_근로소득세_만": round(tax_earned, 0), "연_배당연금세_만": round(tax_dividend_pension, 0), "연_이벤트_만": round(ev_cost, 0),
            "연_총수입_만": round(total_income_y, 0), "연_총지출_만": round(total_exp_y, 0), "연_FCF_만": round(net_flow_y, 0),
            
            "월_남편소득_만": round(inc_h / 12, 0), "월_아내소득_만": round(inc_w / 12, 0),
            "월_배당_만": round(div_income_y / 12, 0), "월_연금_만": round(pension / 12, 0),
            "월_정부지원_만": round((gov_support_y + unemp_income_y) / 12, 0), 
            "월_생활비_만": round(curr_living_y / 12, 0), "월_양육비_만": round(k_total / 12, 0),
            "월_원리금_만": round(repay_a / 12, 0), "월_보유세_만": round((t_hold + t_comp) / 12, 0),
            "월_근로소득세_만": round(tax_earned / 12, 0), "월_배당연금세_만": round(tax_dividend_pension / 12, 0), "월_이벤트_만": round(ev_cost / 12, 0),
            "월_총수입_만": round(total_income_y / 12, 0), "월_총지출_만": round(total_exp_y / 12, 0), "월_FCF_만": round(net_flow_y / 12, 0),
            
            "총수입_만": round(total_income_y, 0), "월_순현금_만": round(net_flow_y / 12, 0), "월_지출_만": round(total_exp_y / 12, 0),
            "보유세_만": round(t_hold + t_comp, 0), "금융소득세_만": round(t_fin_tax, 0),
            "양도세_만": round(t_gain_total, 0), "취득세_만": round(t_acq_total, 0),
            "이벤트": event_str_tooltip
        })
        c_h_sal *= (1 + h_inc)
        c_w_sal *= (1 + w_inc)
        
    return pd.DataFrame(res)

df_res = run_simulation()

# --- 6. 대시보드 출력 UI ---

final_ret_yr = max(h_birth_yr + h_ret_age, w_birth_yr + w_ret_age)
if final_ret_yr <= end_yr:
    ret_row = df_res[df_res["연도"] == final_ret_yr].iloc[0]
    
    st.markdown(f"## 🏠 우리 가족 자산 계획 요약")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚩 남편 은퇴 연도", f"{h_birth_yr + h_ret_age}년", f"({h_ret_age}세)")
    col2.metric("🚩 아내 은퇴 연도", f"{w_birth_yr + w_ret_age}년", f"({w_ret_age}세)")
    col3.metric(f"은퇴({final_ret_yr}년) 시 총자산", f"{ret_row['총자산_억']:.2f}억")
    col4.metric(f"은퇴({final_ret_yr}년) 시 순자산", f"{ret_row['순자산_억']:.2f}억")
    st.markdown("---")

def draw_premium_table(df):
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns), fill_color='#0ea5e9', font=dict(color='white', size=16, family="Noto Sans KR"), align='center', height=45),
        cells=dict(values=[df[col] for col in df.columns], fill_color='#f8fafc', font=dict(color='#0f172a', size=15, family="Noto Sans KR"), align='center', height=35))
    ])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=650)
    return fig

def draw_stacked_bar(data, items, title, total_col=None):
    fig = go.Figure()
    
    for col_name, label_name, color in items:
        fig.add_trace(go.Bar(
            x=data["연도"], y=data[col_name], name=label_name, marker_color=color,
            hovertemplate="%{y:,.0f}만<extra></extra>"
        ))
        
    if total_col:
        fig.add_trace(go.Scatter(
            x=data["연도"], y=data[total_col], name="<b>[해당 연도 총합계]</b>",
            mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False,
            hovertemplate="<b>%{y:,.0f}만</b><extra></extra>"
        ))
        
    fig.update_layout(
        barmode='stack', title=dict(text=title, font=dict(size=20)),
        height=450, margin=dict(l=10, r=10, t=50, b=20), template="plotly_white",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=16, font_family="Noto Sans KR", align="left"),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=13))
    )
    return fig

def draw_fcf_bar(data, col_name, title):
    fig = go.Figure()
    colors = ['#10b981' if val >= 0 else '#ef4444' for val in data[col_name]]
    fig.add_trace(go.Bar(
        x=data["연도"], y=data[col_name], name="FCF", marker_color=colors,
        hovertemplate="<b>%{y:,.0f}만</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=data["연도"], y=[0]*len(data["연도"]), name="<b>[주요 이슈]</b>",
        mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False,
        customdata=data["이벤트"], hovertemplate="%{customdata}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        height=450, margin=dict(l=10, r=10, t=50, b=20), template="plotly_white",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=16, font_family="Noto Sans KR", align="left")
    )
    return fig

m_tab, t_tab, s_tab, d_tab = st.tabs(["📊 자산 성장 로드맵", "⚖️ 상세 세무 분석", "👵 은퇴 & 배당 시뮬레이션", "📋 데이터 상세"])

with m_tab:
    period = st.radio("🔍 조회 기간", ["5년", "10년", "20년", "30년", "전체"], horizontal=True, index=4, key="p_sel")
    len_data = len(df_res)
    display_len = {"5년": min(5, len_data), "10년": min(10, len_data), "20년": min(20, len_data), "30년": min(30, len_data), "전체": len_data}[period]
    sub = df_res.head(display_len)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub["연도"], y=sub["총자산_억"], name="<b>[총자산]</b>", mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False, hovertemplate="<b>%{y:.2f}억</b><extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["순자산_억"], name="순자산", marker_color='#10b981', hovertemplate="%{y:.2f}억<extra></extra>"))
    fig.add_trace(go.Bar(x=sub["연도"], y=sub["대출_억"], name="부채", marker_color='#ef4444', hovertemplate="%{y:.2f}억<extra></extra>"))
    fig.add_trace(go.Scatter(x=sub["연도"], y=[0]*len(sub["연도"]), name="<b>[이슈]</b>", mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False, customdata=sub["이벤트"], hovertemplate="%{customdata}<extra></extra>"))
    
    fig.update_layout(title="🏠 우리 가족 자산 계획 (단위: 억)", barmode='stack', hovermode="x unified", height=500, template="plotly_white", font=dict(size=18),
                      hoverlabel=dict(bgcolor="white", font_size=18, font_family="Noto Sans KR", align="left"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏢 주요 자산 지표 (단위: 억)")
    def draw_mini_asset(data, col, title, color):
        f = go.Figure(go.Bar(x=data["연도"], y=data[col], name=title.split("(")[0], marker_color=color, hovertemplate="<b>%{y:.2f}억</b><extra></extra>"))
        f.add_trace(go.Scatter(x=data["연도"], y=[0]*len(data["연도"]), name="<b>[이슈]</b>", mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False, customdata=data["이벤트"], hovertemplate="%{customdata}<extra></extra>"))
        f.update_layout(title=dict(text=title, font=dict(size=20)), height=320, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white", hovermode="x unified",
                        hoverlabel=dict(bgcolor="white", font_size=16, font_family="Noto Sans KR", align="left"))
        return f
    
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(draw_mini_asset(sub, "부동산_억", "🏠 부동산(억)", "#f97316"), use_container_width=True)
    c2.plotly_chart(draw_mini_asset(sub, "금융자산_억", "📈 금융투자(억)", "#8b5cf6"), use_container_width=True)
    c3.plotly_chart(draw_mini_asset(sub, "예금_억", "💰 예금(억)", "#0ea5e9"), use_container_width=True)
    st.markdown("---")
    
    in_items_m = [("월_남편소득_만", "남편소득", "#3b82f6"), ("월_아내소득_만", "아내소득", "#ec4899"), ("월_정부지원_만", "국가지원/실업급여", "#06b6d4"), ("월_배당_만", "배당(수입)", "#f59e0b"), ("월_연금_만", "공적연금", "#10b981")]
    out_items_m = [("월_생활비_만", "생활비", "#0ea5e9"), ("월_양육비_만", "양육비", "#10b981"), ("월_원리금_만", "대출상환", "#f59e0b"),
                   ("월_보유세_만", "보유세", "#ef4444"), ("월_근로소득세_만", "근로소득/4대보험", "#8b5cf6"), ("월_배당연금세_만", "배당/연금세", "#d946ef"), ("월_이벤트_만", "이벤트", "#ec4899")]
    
    in_items_y = [("연_남편소득_만", "남편소득", "#3b82f6"), ("연_아내소득_만", "아내소득", "#ec4899"), ("연_정부지원_만", "국가지원/실업급여", "#06b6d4"), ("연_배당_만", "배당(수입)", "#f59e0b"), ("연_연금_만", "공적연금", "#10b981")]
    out_items_y = [("연_생활비_만", "생활비", "#0ea5e9"), ("연_양육비_만", "양육비", "#10b981"), ("연_원리금_만", "대출상환", "#f59e0b"),
                   ("연_보유세_만", "보유세", "#ef4444"), ("연_근로소득세_만", "근로소득/4대보험", "#8b5cf6"), ("연_배당연금세_만", "배당/연금세", "#d946ef"), ("연_이벤트_만", "이벤트", "#ec4899")]

    st.markdown("#### 🌊 월간 현금흐름 분석 (수입 vs 지출 vs FCF)")
    st.info("💡 **FCF(잉여현금흐름)란?** 총 수입에서 모든 지출을 빼고 남은 '순수 여윳돈'입니다. 적자(-)가 발생할 경우 **보유 중인 금융자산(주식 등)을 1순위로 매각하여 자동으로 부족한 생활비를 충당**하도록 설계되었습니다.", icon="💵")
    
    cm1, cm2, cm3 = st.columns(3)
    cm1.plotly_chart(draw_stacked_bar(sub, in_items_m, "📥 월 유입 현금(만)", "월_총수입_만"), use_container_width=True)
    cm2.plotly_chart(draw_stacked_bar(sub, out_items_m, "📤 월 지출 상세(만)", "월_총지출_만"), use_container_width=True)
    cm3.plotly_chart(draw_fcf_bar(sub, "월_FCF_만", "💵 월 잉여현금(FCF)"), use_container_width=True)
    st.markdown("---")
    
    st.markdown("#### 🌊 연간 현금흐름 분석 (수입 vs 지출 vs FCF)")
    cy1, cy2, cy3 = st.columns(3)
    cy1.plotly_chart(draw_stacked_bar(sub, in_items_y, "📥 연 유입 현금(만)", "연_총수입_만"), use_container_width=True)
    cy2.plotly_chart(draw_stacked_bar(sub, out_items_y, "📤 연 지출 상세(만)", "연_총지출_만"), use_container_width=True)
    cy3.plotly_chart(draw_fcf_bar(sub, "연_FCF_만", "💵 연 잉여현금(FCF)"), use_container_width=True)

with t_tab:
    st.info("💡 **세무 시뮬레이션 가정 사항**\n* **근로소득세 및 4대보험:** 매년 대한민국의 **8단계 누진세율(6%~45%)**과 4대보험(약 9%) 요율을 적용하여 산출합니다.\n* **자녀 세액공제:** 8세~20세 자녀 1명당 15만, 2명 30만, 3명 60만원의 세금을 자동 공제합니다.\n* **취득/양도세:** 주택 갈아타기 시 각각 3.3%, 20%를 적용합니다.\n* **금융소득세:** 배당금 발생액의 15.4%를 자동 차감합니다.", icon="ℹ️")
    st.header("⚖️ 상세 세무 분석 테이블 (단위: 만원)")
    t_disp = df_res[["연도", "보유세_만", "금융소득세_만", "양도세_만", "취득세_만", "이벤트"]].copy()
    for col in ["보유세_만", "금융소득세_만", "양도세_만", "취득세_만"]: t_disp[col] = t_disp[col].apply(lambda x: f"{x:,.0f}")
    t_disp.columns = ["연도", "🏠 보유세(재산+종부)", "📈 금융소득세(배당등)", "💸 양도세", "📝 취득세", "🚩 관련 이벤트"]
    st.dataframe(t_disp, use_container_width=True, hide_index=True, height=600)

with s_tab:
    if final_ret_yr > end_yr:
        st.warning(f"⚠️ 설정된 은퇴 연도({final_ret_yr}년)가 시뮬레이션 종료 시점({end_yr}년)을 초과합니다. 종료 연도를 늘려주세요.")
    else:
        st.header(f"🚩 최종 은퇴 연도: {final_ret_yr}년 (주택 다운사이징 및 부채상환 완료 후)")
        st.info(f"💡 **배당 시뮬레이션 및 현재가치 가정 사항**\n* **현재가치(PV):** 매년 3%의 물가상승(할인율)을 가정하여, {final_ret_yr}년의 자산을 현재({start_yr}년) 기준의 구매력으로 환산합니다.\n* **은퇴 전 배당:** 금융자산에서 연 평균 1%의 배당수익이 발생한다고 가정합니다.\n* **은퇴 후 배당:** JEPQ는 연 9.5% 고정, SCHD는 초기 3.5% (이후 연 5%씩 배당금 성장, Yield on Cost 적용)로 배당금을 지급합니다.", icon="ℹ️")
        
        ret_row = df_res[df_res["연도"] == final_ret_yr].iloc[0]
        total_asset_fv = ret_row["총자산_억"]
        c_inv_fv = ret_row["금융자산_억"]
        
        discount_rate = 0.03
        num_years = final_ret_yr - start_yr
        discount_factor = (1 + discount_rate) ** max(0, num_years)
        
        total_asset_pv = total_asset_fv / discount_factor
        c_inv_pv = c_inv_fv / discount_factor
        
        st.markdown("#### ⏳ 은퇴 시점 자산 가치 평가 (미래가치 vs 현재가치)")
        col_fv1, col_pv1, col_blank, col_fv2, col_pv2 = st.columns([2, 2, 0.5, 2, 2])
        col_fv1.metric(f"총자산 (미래가치)", f"{total_asset_fv:.2f}억")
        col_pv1.metric(f"총자산 (할인 현재가치)", f"{total_asset_pv:.2f}억")
        col_fv2.metric(f"금융자산 (미래가치)", f"{c_inv_fv:.2f}억")
        col_pv2.metric(f"금융자산 (할인 현재가치)", f"{c_inv_pv:.2f}억")
        
        st.markdown("---")
        st.markdown("#### 💰 은퇴 후 배당 포트폴리오 (미래가치 기준)")
        
        schd_amt = c_inv_fv * (s_schd / 100)
        jepq_amt = c_inv_fv * (s_jepq / 100)
        keep_amt = c_inv_fv * ((100 - s_schd - s_jepq) / 100)
        init_m_div = ((schd_amt * 0.035) + (jepq_amt * 0.095) + (keep_amt * 0.01)) * 10000 / 12
        
        c1, c2, c3 = st.columns(3)
        c1.metric("첫 달 예상 배당금", f"{init_m_div:,.0f}만")
        c2.metric(f"SCHD ({s_schd}%) 배분액", f"{schd_amt:.2f}억")
        c3.metric(f"JEPQ ({s_jepq}%) 배분액", f"{jepq_amt:.2f}억")
        st.caption(f"💡 기존 투자 유지 자산 (배당 1%): {keep_amt:.2f}억")
        st.markdown("---")
        
        div_data = []
        sim_inv_val = c_inv_fv
        for y in range(final_ret_yr, end_yr + 1):
            s_p = sim_inv_val * (s_schd/100)
            j_p = sim_inv_val * (s_jepq/100)
            k_p = sim_inv_val * ((100 - s_schd - s_jepq)/100)
            schd_yoc = 0.035 * (1.05**(y-final_ret_yr))
            m_div = ((s_p * schd_yoc) + (j_p * 0.095) + (k_p * 0.01)) * 10000 / 12
            div_data.append({"연도": y, "월_배당금": m_div})
            sim_inv_val *= (1 + inv_gr)
            
        df_div = pd.DataFrame(div_data)
        fig_div = go.Figure()
        fig_div.add_trace(go.Scatter(x=df_div["연도"], y=df_div["월_배당금"], fill='tozeroy', name="월 배당(만)", marker_color="#8b5cf6", hovertemplate="<b>%{y:,.0f}만</b><extra></extra>"))
        fig_div.update_layout(title="은퇴 후 월 배당 성장 추이 (미래가치)", height=450, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig_div, use_container_width=True)

with d_tab:
    st.subheader("📋 전체 상세 데이터")
    cols_to_show = ["연도", "순자산_억", "총자산_억", "부동산_억", "금융자산_억", "예금_억", "대출_억", 
                    "연_총수입_만", "연_총지출_만", "연_FCF_만", "월_총수입_만", "월_총지출_만", "월_FCF_만", 
                    "월_생활비_만", "월_양육비_만", "월_원리금_만", "월_보유세_만", "월_근로소득세_만", "월_배당연금세_만", "월_이벤트_만",
                    "보유세_만", "금융소득세_만", "양도세_만", "취득세_만", "이벤트"]
    d_disp = df_res[cols_to_show].copy()
    for col in d_disp.columns:
        if col not in ["연도", "이벤트"]:
            if "_억" in col: d_disp[col] = d_disp[col].apply(lambda x: f"{x:,.2f}")
            else: d_disp[col] = d_disp[col].apply(lambda x: f"{x:,.0f}")
    d_disp["이벤트"] = d_disp["이벤트"].apply(lambda x: str(x).replace("<br>", " / "))
    st.dataframe(d_disp, use_container_width=True, hide_index=True, height=650)

# --- 7. 사용자 데이터 자동 저장 로직 ---
static_keys = [
    'sys_start_yr', 'sys_end_yr', 'h_birth_yr', 'w_birth_yr', 
    'h_s_in', 'h_br_in', 'h_i_in', 'h_promo_yr', 'h_promo_r', 'h_ret_in', 'h_sev_in', 'h_p_in', 'h_side_in', 'h_side_end',
    'w_s_in', 'w_br_in', 'w_inc_in', 'w_promo_yr', 'w_promo_r', 'w_r_in', 'w_sev_in', 'w_p_in', 'w_side_in', 'w_side_end',
    'liv_m_in', 'liv_g_in', 'inv_ini_in', 'inv_gr_in', 'inv_rat_in', 
    'debt_ini_in', 'debt_r_in', 'debt_t_in', 'debt_tp_in', 're_ini_in', 're_gr_in', 
    'ret_down_r', 'ret_debt_r', 'ret_schd', 'ret_jepq', 'h_unemp', 'w_unemp'
]

if st.session_state.get('current_user'):
    user_data = db.get(st.session_state.current_user, {})
    for k in static_keys:
        if k in st.session_state:
            user_data[k] = st.session_state[k]
            
    user_data['re_trades'] = st.session_state.get('re_trades', [])
    user_data['events'] = st.session_state.get('events', [])
    user_data['kids'] = st.session_state.get('kids', [])
    user_data['h_leaves'] = st.session_state.get('h_leaves', [])
    user_data['w_leaves'] = st.session_state.get('w_leaves', [])

    db[st.session_state.current_user] = user_data
    save_cloud_db(db)
