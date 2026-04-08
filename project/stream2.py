import streamlit as st
import os
import time
from dotenv import load_dotenv

# ── Import (파일명 및 함수명 확인 필수) ───────────────────────────────────────────
try:
    from multiagent import run_multi_agent_stream
    from service_2_run import (
        extract_pdf_data, get_next_question, get_final_evaluation, 
        speech_to_text, analyze_audio
    )
except ImportError as e:
    st.error(f"파일을 불러오는데 실패했습니다: {e}")

from streamlit_mic_recorder import mic_recorder

# 1. 환경 설정 및 세션 초기화
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "env"))

if "messages" not in st.session_state: st.session_state.messages = []
if "interview_history" not in st.session_state: st.session_state.interview_history = []
if "profile_context" not in st.session_state: st.session_state.profile_context = None
if "mode" not in st.session_state: st.session_state.mode = "admission" # 기본은 입시상담

st.set_page_config(page_title="AI 유학 통합 컨설턴트", page_icon="🎓")
st.title("🎓 AI 유학 & 비자 통합 컨설팅")

# 2. 사이드바: PDF 업로드
with st.sidebar:
    st.header("📄 서류 업로드")
    pdf_file = st.file_uploader("입시/비자 서류 업로드", type="pdf")
    if pdf_file:
        save_path = os.path.join(BASE_DIR, "uploaded_files", pdf_file.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f: f.write(pdf_file.getbuffer())
        st.session_state.pdf_path = save_path
        if st.session_state.profile_context is None:
            with st.spinner("서류 분석 중..."):
                st.session_state.profile_context = extract_pdf_data(save_path, "user_data")
            st.success("서류 분석 완료! 상담을 시작하세요.")

# 3. 대화 내역 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 입력 및 로직 처리
if st.session_state.profile_context:
    
    # --- [비자 인터뷰 자동 재생 로직] ---
    # 인터뷰 모드이고 마지막 메시지가 면접관 질문일 때 음성 재생
    if st.session_state.mode == "interview" and st.session_state.messages:
        last_m = st.session_state.messages[-1]
        if last_m["role"] == "assistant" and "🏆" not in last_m["content"]:
            st.audio("question.mp3", format="audio/mp3", autoplay=True, key=f"tts_{len(st.session_state.messages)}")

    # --- [입력 UI] ---
    st.write("---")
    c1, c2 = st.columns([1, 4])
    with c1:
        # 인터뷰 모드일 때만 녹음 버튼 활성화
        recorded_audio = mic_recorder(start_prompt="🎤 녹음", stop_prompt="🛑 정지", key='visa_mic') if st.session_state.mode == "interview" else None
    
    user_input = st.chat_input("메시지를 입력하세요 (예: '비자 인터뷰 시작해줘')")

    # 음성 녹음 완료 처리
    if recorded_audio:
        with open("speech.wav", "wb") as f: f.write(recorded_audio['bytes'])
        user_input = speech_to_text("speech.wav")
        st.session_state.last_audio_data = analyze_audio("speech.wav", user_input)

    # 5. 메인 로직 수행
    if user_input:
        # 사용자 답변 표시
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        # [상태 전환 로직] 비자 인터뷰 시작 키워드 감지
        if any(keyword in user_input for keyword in ["비자