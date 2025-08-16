import streamlit as st
import pandas as pd

# CSV 파일 로드 (인코딩: 'cp949')
df = pd.read_csv("final_brion_data.csv", encoding='cp949')



# 치료 단계 순서 정의 및 정렬
treatment_order = ["Neoadjuvant", "Adjuvant", "1st line", "2nd+ line", "Recurrent"]
df["TreatmentLine"] = pd.Categorical(df["TreatmentLine"], categories=treatment_order, ordered=True)

st.set_page_config(page_title="유방암 병기 기반 약제 추천", layout="wide")
st.title("🧬 유방암 병기 기반 약제 추천 AI")
st.markdown("---")

st.header("1️⃣ 병기 및 병리 정보 입력")

# T/N 사용자 정의 값 반영
t_mapping = {
    "TX": "T1", "T0": "T1", "Tis (DCIS)": "T1", "Tis (Paget)": "T1",
    "T1mi": "T1", "T1a": "T1", "T1b": "T1", "T1c": "T1",
    "T2": "T2", "T3": "T3",
    "T4a": "T4", "T4b": "T4", "T4c": "T4", "T4d": "T4"
}
n_mapping = {
    "cNX": "N0", "cN0": "N0", "cN1mi": "N1",
    "cN2a": "N2", "cN2b": "N2",
    "cN3a": "N3", "cN3b": "N3", "cN3c": "N3"
}

col1, col2, col3 = st.columns(3)
with col1:
    t_raw = st.selectbox("Primary Tumor (T)", list(t_mapping.keys()))
    her2 = st.radio("HER2 Status", ["Neg (-)", "Pos (+)"], horizontal=True)
with col2:
    n_raw = st.selectbox("Regional Lymph Nodes (N)", list(n_mapping.keys()))
    er = st.radio("ER Status", ["Neg (-)", "Pos (+)"], horizontal=True)
with col3:
    m = st.selectbox("Distant Metastasis (M)", ["M0", "cM0(i+)", "M1"])
    pr = st.radio("PR Status", ["Neg (-)", "Pos (+)"], horizontal=True)

t = t_mapping[t_raw]
n = n_mapping[n_raw]

# OncotypeDx, gBRCA, PDL1에 대한 selectbox 생성 (NaN 값 제외)
oncotype = st.selectbox("OncotypeDx 조건", sorted(df['OncotypeDx'].dropna().unique()))
gbrca = st.selectbox("gBRCA 여부", sorted(df['gBRCA'].dropna().unique()))
pdl1 = st.selectbox("PDL1 상태", sorted(df['PDL1'].dropna().unique()))


# 병기 계산
stage = "병기 계산 불가"
if "M1" in m:
    stage = "Stage IV"
elif t == "T1" and n == "N0" and "M0" in m:
    stage = "Stage I"
elif t == "T2" and n == "N0" and "M0" in m:
    stage = "Stage II"
elif t == "T3" or n == "N2" or n == "N3":
    stage = "Stage III"
elif t == "T0" and n == "N0" and "M0" in m:
    stage = "Stage 0"


# 아형 분류
subtype = "-"
if er == "Pos (+)" or pr == "Pos (+)":
    if her2 == "Neg (-)":
        subtype = "HR+/HER2-"
    elif her2 == "Pos (+)":
        subtype = "HR+/HER2+"
elif er == "Neg (-)" and pr == "Neg (-)" and her2 == "Pos (+)":
    subtype = "HR-/HER2+"
elif er == "Neg (-)" and pr == "Neg (-)" and her2 == "Neg (-)":
    subtype = "TNBC"

st.markdown(f"#### **계산된 병기:** {stage} | **계산된 아형:** {subtype}")


# 필터링
filtered_df = df[
    (df['Stage'] == stage) &
    (df['Subtype'] == subtype) &
    (df['OncotypeDx'] == oncotype) &
    (df['gBRCA'] == gbrca) &
    (df['PDL1'] == pdl1)
].sort_values("TreatmentLine")

st.divider()
st.header("2️⃣ 치료전략 및 약제 추천 결과")

if filtered_df.empty:
    st.warning("선택된 조건에 맞는 추천 약제가 없습니다. 다른 조건을 선택해보세요.")
else:
    for i, row in filtered_df.iterrows():
        # 각 결과에 대한 정보창 제목 설정
        expander_title = f"🩺 치료 단계: {row['TreatmentLine']} | 💊 약제명: {row['RecommendedRegimen']}"
        with st.expander(expander_title, expanded=True):
            st.markdown("---")
            
            # '1회_용량' 컬럼의 복합적인 '-' 값을 처리하는 새 로직
            dose_per_session_raw = row['1회_용량(160cm/60kg)_mg']
            
            # 값이 문자열일 경우에만 처리
            if isinstance(dose_per_session_raw, str):
                # 1. 쉼표로 분리하고 각 항목의 공백 제거
                items = [item.strip() for item in dose_per_session_raw.split(',')]
                # 2. 각 항목을 확인하여 '-'를 '정보 없음'으로 변경
                processed_items = ['정보 없음' if item == '-' else item for item in items]
                # 3. 다시 쉼표와 공백으로 합치기
                dose_per_session = ', '.join(processed_items)
            else:
                # 문자열이 아닌 경우(숫자, 빈 값 등)는 그대로 사용
                dose_per_session = dose_per_session_raw

            # 이모티콘과 한글 레이블을 포함하도록 HTML 블록 수정
            html_block = f"""
            <div style='line-height: 2.0; font-size: 16px'>
                <p><strong>🩺 치료 단계:</strong> {row['TreatmentLine']}</p>
                <p><strong>💊 약제명:</strong> {row['RecommendedRegimen']}</p>
                <p><strong>📌 NCCN 권고 등급:</strong> {row['NCCN_Category']}</p>
                <p><strong>🧪 임상시험:</strong> {row['Trial']}</p>
            """

            # 급여여부 스타일 적용
            coverage_text = str(row.get("급여여부", "")).strip()
            if coverage_text in ["급여", "선별급여(복합요법)"]:
                html_block += f"<p><strong>✅ 급여여부:</strong> {coverage_text}</p>"
            elif coverage_text == "비급여":
                html_block += "<p><strong>❌ 급여여부:</strong> 비급여</p>"
            else:
                html_block += f"<p><strong>ℹ️ 급여여부:</strong> {coverage_text or '정보 없음'}</p>"

            # 용량 및 단가 정보 스타일 적용
            html_block += f"<p><strong>💉 권장 용량:</strong> {row['권장용량_표시']}</p>"
            html_block += f"<p><strong>💊 1회 용량(160cm/60kg)mg:</strong> {dose_per_session}</p>"
            html_block += f"<p><strong>💰 최종 비용:</strong> {row['단가_표시']}</p>"

            html_block += "</div>"
            st.markdown(html_block, unsafe_allow_html=True)
            
        st.markdown("---")
