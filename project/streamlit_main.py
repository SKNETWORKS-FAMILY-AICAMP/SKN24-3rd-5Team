import streamlit as st
import os
from dotenv import load_dotenv

# multiagent.py에서 필요한 함수들을 가져옵니다.
try:
    # 파일 이름을 service_2_run으로 변경하여 가져옵니다.
    # speech_to_text와 analyze_audio도 녹음 처리를 위해 가져옵니다.
    from service_2_run import get_next_question, get_final_evaluation, speech_to_text, analyze_audio
except ImportError as e:
    st.error(f"파일을 불러올 수 없습니다: {e}")
    st.info("service_2_run.py 파일 이름과 함수명이 정확한지 확인하세요.")

# 1. 환경 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 사용자의 요청에 따라 .env가 아닌 'env' 경로를 유지합니다.
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "env"))

# 폴더 설정
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "interview_history" not in st.session_state:
    st.session_state.interview_history = []
if "profile_context" not in st.session_state:
    st.session_state.profile_context = None

# 2. UI 레이아웃
st.set_page_config(page_title="AI 비자 인터뷰 챗봇", page_icon="🤖")
st.title("🎓 AI 비자 통합 컨설턴트")

# 사이드바: 파일 업로드
with st.sidebar:
    st.header("⚙️ 설정 및 서류")
    pdf_file = st.file_uploader("비자 서류(PDF) 업로드", type="pdf")
    
    if pdf_file is not None:
        save_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(save_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        st.session_state.pdf_path = os.path.abspath(save_path)
        st.success(f"✅ 준비 완료: {pdf_file.name}")
        
        if st.session_state.profile_context is None:
            with st.spinner("서류 분석 중..."):
                st.session_state.profile_context = extract_pdf_data(st.session_state.pdf_path, "user_data")
    else:
        st.session_state.pdf_path = None
        st.session_state.profile_context = None
        st.info("비자 인터뷰 연습을 위해 PDF를 업로드해주세요.")

# 3. 대화 내역 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 과거 메시지 중 오디오 파일 정보가 있다면 다시 표시할 수 있으나, 
        # 여기서는 최신 질문에 대해서만 자동 재생을 처리합니다.

# 4. 채팅 입력 및 로직
if prompt := st.chat_input("답변을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            last_agent_msg = next((m["content"] for m in reversed(st.session_state.messages[:-1]) if m["role"] == "assistant"), "Initial")
            st.session_state.interview_history.append({"question": last_agent_msg, "answer": prompt})

            if len(st.session_state.interview_history) < 3:
                with st.spinner("면접관이 질문 중입니다..."):
                    new_q = get_next_question(st.session_state.profile_context, st.session_state.interview_history)
                    st.markdown(new_q)
                    st.session_state.messages.append({"role": "assistant", "content": new_q})
                    
                    # --- 오디오 재생 로직 추가 ---
                    audio_path = os.path.join(BASE_DIR, "question.mp3")
                    if os.path.exists(audio_path):
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    # ---------------------------

            else:
                with st.spinner("인터뷰 결과를 정리 중입니다..."):
                    eval_result = get_final_evaluation(st.session_state.profile_context, st.session_state.interview_history)
                    st.markdown("### 🏆 최종 인터뷰 결과 및 피드백")
                    st.markdown(eval_result)
                    st.session_state.messages.append({"role": "assistant", "content": eval_result})
                    
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            st.info("multiagent.py 내의 'input()'이나 'record()' 함수가 실행을 막고 있지 않은지 확인하세요.")