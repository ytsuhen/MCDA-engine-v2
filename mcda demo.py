import streamlit as st

# Налаштування сторінки на широкий формат
st.set_page_config(page_title="CDS Rule Engine", layout="wide")

def calculate_mcda_score(patient_data):
    THRESHOLD = 10
    
    # Крок 1: Внутрішньодоменне поглинання
    domain_max_scores = {}
    for domain, scores in patient_data.items():
        valid_scores = [s for s in scores if s > 0]
        domain_max_scores[domain] = max(valid_scores) if valid_scores else 0
            
    active_maxes = [v for v in domain_max_scores.values() if v > 0]
    
    if not active_maxes:
        return 0.0, "Придатний", domain_max_scores, 0, 0, 0.0
        
    # Крок 2: Знаходимо M та S_rest
    M = max(active_maxes)
    S_rest = sum(active_maxes) - M
    
    # Крок 3: Асимптотична формула
    alpha = (THRESHOLD - M) / THRESHOLD
    final_score = round(M + (S_rest * alpha), 2)
    
    # Крок 4: Маршрутизація статусів
    if final_score < 3.0:
        status = "Придатний"
    elif final_score < 10.0:
        status = "Обмежено придатний"
    else:
        status = "Непридатний"
        
    return final_score, status, domain_max_scores, M, S_rest, alpha

# ==========================================
# ІНТЕРФЕЙС (UI)
# ==========================================

st.title("🩺 MCDA (multiple-criteria decision analysis)")
st.markdown("""
Цей прототип демонструє роботу **гібридної MCDA-моделі**. 
Система автоматично застосовує *внутрішньодоменне поглинання* (захист від дублювання діагнозів) та *асимптотичне додавання* (захист від фродової ескалації статусу).
""")

severity_map = {
    "Норма <5% (0)": 0, 
    "Легке .1 (1)": 1, 
    "Помірне .2 (3)": 3, 
    "Важке .3 (10)": 10
}

st.header("1. Клінічні дані (Введення кодів МКФ)")

# 4 колонки для доменів
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("👁️ Зір (b2)")
    v1 = st.selectbox("Міопія (b210)", list(severity_map.keys()), index=0, key="v1")
    v2 = st.selectbox("Катаракта (b215)", list(severity_map.keys()), index=0, key="v2")
    v3 = st.selectbox("Астигматизм (b220)", list(severity_map.keys()), index=0, key="v3")

with col2:
    st.subheader("🫀 Серце (b4)")
    h1 = st.selectbox("Гіпертонія (b420)", list(severity_map.keys()), index=0, key="h1")
    h2 = st.selectbox("ІХС (b410)", list(severity_map.keys()), index=0, key="h2")
    h3 = st.selectbox("Аритмія (b460)", list(severity_map.keys()), index=0, key="h3")

with col3:
    st.subheader("🦴 Спина (b7)")
    m1 = st.selectbox("Остеохондроз (b710)", list(severity_map.keys()), index=0, key="m1")
    m2 = st.selectbox("Грижа (b715)", list(severity_map.keys()), index=0, key="m2")
    m3 = st.selectbox("М'язовий спазм (b730)", list(severity_map.keys()), index=0, key="m3")

with col4:
    st.subheader("🍏 Шлунок (b5)")
    g1 = st.selectbox("Гастрит (b515)", list(severity_map.keys()), index=0, key="g1")
    g2 = st.selectbox("Виразка (b525)", list(severity_map.keys()), index=0, key="g2")
    g3 = st.selectbox("Рефлюкс (b510)", list(severity_map.keys()), index=0, key="g3")

st.write("---")

if st.button("🚀 Згенерувати висновок ВЛК", type="primary", use_container_width=True):
    
    patient_data = {
        'Зір (b2)': [severity_map[v1], severity_map[v2], severity_map[v3]],
        'Серце (b4)': [severity_map[h1], severity_map[h2], severity_map[h3]],
        'Спина (b7)': [severity_map[m1], severity_map[m2], severity_map[m3]],
        'Шлунок (b5)': [severity_map[g1], severity_map[g2], severity_map[g3]]
    }
    
    score, status, domain_maxes, M, S_rest, alpha = calculate_mcda_score(patient_data)
    
    # Вивід головного результату
    st.header("2. Фінальний результат")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="Кумулятивний бал (Burden Index)", value=f"{score} / 10.0")
    with res_col2:
        if status == "Придатний":
            st.success(f"⚖️ СТАТУС: {status}")
        elif status == "Обмежено придатний":
            st.warning(f"⚖️ СТАТУС: {status}")
        else:
            st.error(f"⚖️ СТАТУС: {status}")

    # Блок "Прозорість обчислень" (Explainable AI)
    st.header("3. Прозорість обчислень (Rule Engine Decode)")
    with st.expander("Розгорнути математичний аудит (Audit Trail)", expanded=True):
        
        st.markdown("### Етап А: Внутрішньодоменне поглинання (Intra-domain MAX)")
        st.write("*Алгоритм фільтрує коморбідний шум. З кожного органу береться лише найтяжче порушення. Дублікати ігноруються.*")
        
        cols = st.columns(4)
        for i, (dom, val) in enumerate(domain_maxes.items()):
            cols[i].metric(label=f"Вектор: {dom}", value=val)
            
        st.markdown("---")
        st.markdown("### Етап Б: Асимптотична агрегація (AMA Combined Values)")
        st.write(f"**Домінуючий тягар (M):** {M} *(найважча хвороба серед усіх систем)*")
        st.write(f"**Сума супутніх хвороб (S_rest):** {S_rest} *(сума решти векторів)*")
        st.write(f"**Коефіцієнт вільного простору (α):** {alpha} *( (10 - {M}) / 10 )*")
        
        st.info(f"**Формула:** Score = {M} + ({S_rest} × {alpha}) = **{score}**")
