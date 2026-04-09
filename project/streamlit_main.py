import streamlit as st
import os
import tempfile

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 유학·비자 통합 시스템",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 커스텀 CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #0f1b35 0%, #1a3a6b 50%, #0f2d5e 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.main-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    font-weight: 400;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.5px;
}
.main-header p {
    font-size: 0.9rem;
    opacity: 0.7;
    margin: 0;
    font-weight: 300;
}

.mode-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 100px;
    font-size: 0.78rem;
    font-weight: 500;
    margin-bottom: 1rem;
}
.mode-admissions {
    background: #e8f0fe;
    color: #1a56cc;
}
.mode-interview {
    background: #fce8e6;
    color: #c5221f;
}
.mode-idle {
    background: #f1f3f4;
    color: #5f6368;
}

.chat-bubble-user {
    background: #1a3a6b;
    color: white;
    padding: 0.8rem 1.1rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.93rem;
    line-height: 1.6;
}
.chat-bubble-ai {
    background: #f8f9fa;
    color: #1a1a2e;
    padding: 0.8rem 1.1rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 0;
    max-width: 85%;
    font-size: 0.93rem;
    line-height: 1.6;
    border: 1px solid #e8eaed;
}
.officer-tag {
    font-size: 0.75rem;
    font-weight: 700;
    color: #c5221f;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}

.progress-container {
    background: #f1f3f4;
    border-radius: 100px;
    height: 8px;
    margin: 0.5rem 0 1rem 0;
    overflow: hidden;
}
.progress-bar {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #1a3a6b, #4a90d9);
    transition: width 0.4s ease;
}

.question-counter {
    font-size: 0.8rem;
    color: #5f6368;
    margin-bottom: 0.25rem;
}

.sidebar-section {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    border: 1px solid #e8eaed;
}
.sidebar-section h4 {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 0.6rem 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.tip-box {
    background: #e8f0fe;
    border-left: 3px solid #1a56cc;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.83rem;
    color: #1a3a6b;
    line-height: 1.5;
    margin-top: 0.5rem;
}

.eval-card {
    background: white;
    border: 1px solid #e8eaed;
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 0.5rem;
}

.stButton > button {
    border-radius: 100px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 500 !important;
}

div[data-testid="stChatMessage"] {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ─────────────────────────────────────────────────────────
defaults = {
    "messages": [],
    "is_interview_mode": False,
    "pdf_path": None,
    "interview_history": [],
    "profile_context": "",
    "question_count": 0,
    "interview_done": False,
    "current_audio_features": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div style="display:flex; align-items:center; gap:14px; margin-bottom:8px;">
        <span style="font-size:2.2rem;">🎓</span>
        <div>
            <h1>AI 유학 & 비자 통합 시스템</h1>
            <p>입시 상담 · F-1 비자 인터뷰 시뮬레이션 · 실전 평가까지 한번에</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    # 서비스 선택
    st.markdown('<div class="sidebar-section"><h4>서비스 모드</h4>', unsafe_allow_html=True)
    service_mode = st.radio(
        "현재 모드",
        ["🔍 자동 감지 (AI 라우팅)", "🏫 입시 상담", "🎤 비자 인터뷰"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # PDF 업로드
    st.markdown('<div class="sidebar-section"><h4>📄 서류 업로드</h4>', unsafe_allow_html=True)
    pdf_file = st.file_uploader(
        "I-20 또는 비자 서류 PDF",
        type="pdf",
        help="비자 인터뷰 시뮬레이션에 필요합니다"
    )

    if pdf_file:
        upload_dir = "/workspace/project/uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, pdf_file.name)

        if st.session_state.pdf_path != save_path:
            with open(save_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            with st.spinner("서류 분석 중..."):
                try:
                    from service_2_run import extract_pdf_data, vector_store
                    extract_pdf_data(save_path, "user_data")

                    # 프로필 컨텍스트 로드
                    user_retriever = vector_store.as_retriever(
                        search_kwargs={"filter": {"type": "user_data"}, "k": 2}
                    )
                    user_docs = user_retriever.invoke("")
                    st.session_state.profile_context = "\n\n".join(
                        doc.page_content for doc in user_docs
                    )
                except Exception as e:
                    st.error(f"서류 분석 오류: {e}")

            st.session_state.pdf_path = save_path
            st.success(f"✅ {pdf_file.name} 분석 완료")

    if st.session_state.pdf_path:
        st.caption(f"현재 서류: `{os.path.basename(st.session_state.pdf_path)}`")
    st.markdown('</div>', unsafe_allow_html=True)

    # 인터뷰 진행 상태
    if st.session_state.is_interview_mode:
        q_count = st.session_state.question_count
        st.markdown('<div class="sidebar-section"><h4>🎙 인터뷰 진행 상태</h4>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="question-counter">질문 {min(q_count, 3)} / 3</div>',
            unsafe_allow_html=True
        )
        progress = min(q_count / 3, 1.0)
        st.markdown(
            f'<div class="progress-container"><div class="progress-bar" style="width:{progress*100}%"></div></div>',
            unsafe_allow_html=True
        )
        if st.button("인터뷰 초기화", type="secondary", use_container_width=True):
            st.session_state.interview_history = []
            st.session_state.question_count = 0
            st.session_state.is_interview_mode = False
            st.session_state.interview_done = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 사용 팁
    st.markdown("""
<div class="tip-box">
💡 <b>입시 질문 예시</b><br>
"펜실베이니아대 입학 조건 알려줘"<br><br>
💡 <b>인터뷰 시작 예시</b><br>
"비자 인터뷰 연습 시작할게"
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑 대화 초기화", use_container_width=True):
        for k in ["messages", "interview_history", "question_count",
                  "is_interview_mode", "interview_done"]:
            st.session_state[k] = [] if "history" in k or k == "messages" else False if k != "question_count" else 0
        st.rerun()

# ── 현재 모드 배지 ────────────────────────────────────────────────────────────
if st.session_state.is_interview_mode:
    st.markdown('<span class="mode-badge mode-interview">🎤 비자 인터뷰 모드 진행 중</span>', unsafe_allow_html=True)
elif st.session_state.messages:
    st.markdown('<span class="mode-badge mode-admissions">🏫 입시 상담 모드</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="mode-badge mode-idle">질문을 입력하거나 인터뷰를 시작하세요</span>', unsafe_allow_html=True)

# ── 대화 내역 렌더링 ──────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            content = msg["content"]
            if "Officer:" in content:
                parts = content.split("Officer:", 1)
                if parts[1].strip():
                    st.markdown('<div class="officer-tag">면접관</div>', unsafe_allow_html=True)
                    st.markdown(parts[1].strip())
            else:
                st.markdown(content)

            # TTS 오디오 재생 (인터뷰 모드)
            if st.session_state.is_interview_mode and os.path.exists("question.mp3"):
                if msg == st.session_state.messages[-1]:
                    st.audio("question.mp3", format="audio/mp3")

# ── 입력 영역 ─────────────────────────────────────────────────────────────────
final_input = None
audio_features = None

# 인터뷰 모드 → 음성 녹음 UI
if st.session_state.is_interview_mode and not st.session_state.interview_done:
    last_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    waiting_for_answer = (
        st.session_state.interview_history
        and not st.session_state.interview_history[-1].get("answer")
    )

    if waiting_for_answer and ("Officer:" in last_msg or "면접관" in last_msg):
        st.markdown("---")
        st.markdown("#### 🎙 답변 입력")
        input_tab, voice_tab = st.tabs(["⌨️ 텍스트로 답변", "🎤 음성으로 답변"])

        with input_tab:
            text_ans = st.text_area(
                "영어로 답변을 입력하세요",
                placeholder="Please answer in English...",
                height=120,
                key=f"text_ans_{len(st.session_state.messages)}"
            )
            if st.button("✅ 답변 제출", type="primary", key="submit_text"):
                if text_ans.strip():
                    final_input = text_ans.strip()

        with voice_tab:
            try:
                from audio_recorder_streamlit import audio_recorder
                st.markdown("아래 버튼을 눌러 녹음을 시작/종료하세요.")
                recorded = audio_recorder(
                    text="녹음 시작 / 종료",
                    icon_size="2x",
                    key=f"audio_{len(st.session_state.messages)}"
                )
                if recorded:
                    audio_path = "speech.wav"
                    with open(audio_path, "wb") as f:
                        f.write(recorded)
                    with st.spinner("음성 인식 중..."):
                        from service_2_run import speech_to_text, analyze_audio
                        converted = speech_to_text(audio_path)
                        audio_features = analyze_audio(audio_path, converted)
                    if converted:
                        st.info(f"인식된 텍스트: *{converted}*")
                        final_input = converted
                        st.session_state.current_audio_features = audio_features
            except ImportError:
                st.warning("음성 녹음 기능을 사용하려면 `audio_recorder_streamlit` 패키지를 설치해주세요.")

    elif not waiting_for_answer:
        # 다음 질문 요청 버튼
        if st.button("➡️ 다음 질문 받기", type="primary"):
            final_input = "__NEXT_QUESTION__"

# 일반 텍스트 입력
user_input = st.chat_input(
    "입시 질문 또는 메시지를 입력하세요...",
    disabled=st.session_state.is_interview_mode and not st.session_state.interview_done
)

if user_input:
    final_input = user_input

# ── 메시지 처리 ───────────────────────────────────────────────────────────────
if final_input:
    # 내부 트리거 처리
    display_input = final_input if final_input != "__NEXT_QUESTION__" else None

    if display_input:
        st.session_state.messages.append({"role": "user", "content": display_input})
        with st.chat_message("user"):
            st.markdown(display_input)

    # 인터뷰 모드: 답변을 히스토리에 기록
    if st.session_state.is_interview_mode and st.session_state.interview_history:
        last_hist = st.session_state.interview_history[-1]
        if not last_hist.get("answer") and display_input:
            last_hist["answer"] = display_input
            last_hist["audio"] = st.session_state.current_audio_features

    # ── 응답 생성 ──────────────────────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("처리 중..."):

            # 서비스 모드 분기
            is_interview_request = (
                "인터뷰" in (display_input or "") or
                "interview" in (display_input or "").lower() or
                "비자 연습" in (display_input or "") or
                service_mode == "🎤 비자 인터뷰" or
                st.session_state.is_interview_mode
            )

            if is_interview_request and not st.session_state.interview_done:
                # ── 비자 인터뷰 로직 ──────────────────────────────────────
                if not st.session_state.pdf_path:
                    response = "⚠️ 비자 인터뷰를 시작하려면 먼저 사이드바에서 PDF 서류를 업로드해주세요."
                    st.session_state.is_interview_mode = False
                else:
                    st.session_state.is_interview_mode = True
                    history = st.session_state.interview_history
                    q_count = len(history)
                    profile_ctx = st.session_state.profile_context or f"Path: {st.session_state.pdf_path}"

                    from service_2_run import get_next_question, get_final_evaluation

                    all_answered = all(h.get("answer") for h in history) if history else True

                    if q_count < 3 and all_answered:
                        # 다음 질문 생성
                        question = get_next_question(profile_ctx, history)
                        tagged = f"Officer: {question}"
                        st.session_state.interview_history.append({"question": tagged, "answer": ""})
                        st.session_state.question_count = q_count + 1
                        response = tagged

                        # TTS
                        try:
                            from service_2_run import text_to_speech
                            text_to_speech(question, "question.mp3")
                        except Exception:
                            pass

                        # 오디오 재생
                        if os.path.exists("question.mp3"):
                            st.audio("question.mp3", format="audio/mp3")

                    elif q_count >= 3 and all_answered:
                        # 최종 평가
                        with st.spinner("인터뷰 결과를 분석하는 중... 잠시만 기다려주세요"):
                            evaluation = get_final_evaluation(profile_ctx, history)
                        st.session_state.interview_done = True
                        st.session_state.is_interview_mode = False
                        response = f"🏁 **인터뷰가 종료되었습니다.**\n\n---\n\n{evaluation}"
                    else:
                        response = "답변을 기다리고 있습니다. 위에서 텍스트 또는 음성으로 답변해 주세요."

            elif service_mode == "🏫 입시 상담" or not is_interview_request:
                # ── 입시 상담 로직 ─────────────────────────────────────────
                try:
                    from multiagent import run_multi_agent_stream
                    response = run_multi_agent_stream(
                        display_input or "",
                        pdf_path=st.session_state.pdf_path,
                        history=[]
                    )
                except Exception as e:
                    try:
                        from graph import builder
                        agent = builder.compile()
                        result = ""
                        for step in agent.stream(
                            {"messages": [{"role": "user", "content": display_input or ""}]},
                            stream_mode="values"
                        ):
                            msg = step["messages"][-1]
                            if msg.type == "ai" and msg.content and not getattr(msg, "tool_calls", None):
                                result = msg.content
                        response = result or f"에이전트 오류: {e}"
                    except Exception as e2:
                        response = f"⚠️ 시스템 오류가 발생했습니다: {e2}"
            else:
                response = "처리할 수 없는 요청입니다."

        # 응답 렌더링
        if "Officer:" in response:
            parts = response.split("Officer:", 1)
            if parts[1].strip():
                st.markdown('<div class="officer-tag">면접관</div>', unsafe_allow_html=True)
                st.markdown(parts[1].strip())
        else:
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# ── 빈 상태 안내 ──────────────────────────────────────────────────────────────
if not st.session_state.messages:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:#f0f4ff; border-radius:14px; padding:1.3rem; border:1px solid #c7d7ff;">
            <div style="font-size:1.8rem; margin-bottom:8px;">🏫</div>
            <div style="font-weight:700; font-size:1rem; color:#1a3a6b; margin-bottom:6px;">입시 상담</div>
            <div style="font-size:0.86rem; color:#555; line-height:1.6;">
                학교 정보, 입학 조건, 학비, 마감일 등<br>미국 유학 입시 정보를 RDB 기반으로 검색합니다.
            </div>
            <div style="margin-top:12px; font-size:0.8rem; color:#1a56cc; background:#dde8ff; padding:6px 10px; border-radius:8px;">
                예: "펜실베이니아대 입학 조건 알려줘"
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#fff4f4; border-radius:14px; padding:1.3rem; border:1px solid #ffc7c7;">
            <div style="font-size:1.8rem; margin-bottom:8px;">🎤</div>
            <div style="font-weight:700; font-size:1rem; color:#8b0000; margin-bottom:6px;">비자 인터뷰 시뮬레이션</div>
            <div style="font-size:0.86rem; color:#555; line-height:1.6;">
                업로드한 서류 기반 개인화 질문 생성,<br>TTS 음성 출력, STT 음성 인식, 최종 평가
            </div>
            <div style="margin-top:12px; font-size:0.8rem; color:#c5221f; background:#ffe0de; padding:6px 10px; border-radius:8px;">
                예: "비자 인터뷰 연습 시작할게" (PDF 업로드 필요)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
