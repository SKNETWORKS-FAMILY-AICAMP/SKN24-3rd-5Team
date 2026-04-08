# ── 환경변수 ──────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── imports ───────────────────────────────────────────────────────────────────
import os
import re
import random
import shutil

import numpy as np
import librosa
import sounddevice as sd
from scipy.io.wavfile import write

import pandas as pd
from datasets import load_dataset

from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pdf2image import convert_from_path
import pytesseract


# ── 전역 클라이언트 / 모델 초기화 ────────────────────────────────────────────
client = OpenAI()

llm = ChatOllama(
    model="ebdm/gemma3-enhanced:12b",
    temperature=0.5
)

embed_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": "cpu"}   # GPU 있으면 "cuda"
)

vector_store = Chroma(
    collection_name="s2_interview_data",
    embedding_function=embed_model,
    persist_directory="./chroma_db"
)


# ── 유틸 함수들 ───────────────────────────────────────────────────────────────

def extract_text_flattened_pdf(pdf_path):
    poppler_bin = shutil.which("pdftocairo")
    poppler_path = os.path.dirname(poppler_bin) if poppler_bin else "/opt/homebrew/bin/"

    tesseract_bin = shutil.which("tesseract")
    pytesseract.pytesseract.tesseract_cmd = tesseract_bin if tesseract_bin else "/opt/homebrew/bin/tesseract"

    try:
        pages = convert_from_path(pdf_path, 300, poppler_path=poppler_path)
        full_text = []
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page)
            full_text.append(text)
            print(f"  Page {i+1} processed.")
        return "".join(full_text)
    except Exception as e:
        return f"Still failing: {e}"


def extract_pdf_data(pdf_path, doc_type):
    print(f"[PDF] Processing {doc_type}: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    final_docs = []

    if doc_type == "essay":
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        for chunk in splitter.split_documents(docs):
            chunk.metadata = {"source": pdf_path, "type": "essay"}
            final_docs.append(chunk)
    else:
        result = extract_text_flattened_pdf(pdf_path)
        final_docs.append(Document(
            page_content=result,
            metadata={"source": pdf_path, "type": "user_data"}
        ))

    vector_store.add_documents(final_docs)
    print(f"[PDF] Done — {len(final_docs)} doc(s) added to vector store.")


# ── 고유명사 전처리 ───────────────────────────────────────────────────────────

UNIVERSITIES = [
    "Northeastern University", "Tennessee state university", "Imo state university",
    "southeastern louisiana university", "University of Alabama", "Oregon State University",
    "Miami University", "Rice University", "Obafemi Awolowo University", "Vermont Law School",
    "Lousiana State University", "Georgia State University", "University of South Carolina Gould",
    "GSU", "TSU", "OSU", "USC", "SLU", "UTA", "Lamar",
]
MAJORS = [
    "Industrial engineering and Operations research",
    "Advanced Studies in English Language and Digital Humanities",
    "funeral services and mortuary science", "Project Management", "Criminal Justice",
    "Computer Engineering", "Biotechnology", "Microbiology", "Chemistry", "Public Health", "Geoscience",
]
COUNTRIES = [
    "United States of America", "Trinidad and Tobago", "United States", "Ivory Coast",
    "XYZ country", "Nigeria", "Africa", "Ghana", "China", "Turkey", "the US",
]
LOCATIONS = [
    "Anambra State", "Osun state", "Abidjan", "Portland", "Abeokuta",
    "Alabama", "Osogbo", "Vermont", "Lagos", "Abuja", "Maine", "Ife",
]
ORGANIZATIONS = [
    "Institute For Agricultural Research", "Food and Agricultural Organization of the United Nations",
    "Nigerian center for disease control and prevention", "Federal Ministry of Environment",
    "Nigerian Bar Association", "National Youth Service Corps", "Ministry of Environment",
    "MPOWER Financing", "Dakali Ventures", "open dreams",
]
AMOUNT_PAT = re.compile(
    r'\$[\d,]+(?:\.\d+)?'
    r'|[\d,]+(?:\.\d+)?\s*USD'
    r'|[\d,]+(?:\.\d+)?\s*naira'
    r'|[\d,.]+\s*million\s*naira'
    r'|[\d,]+k',
    re.IGNORECASE
)
TOKEN_MAP = {
    "UNIVERSITY": UNIVERSITIES, "MAJOR": MAJORS,
    "COUNTRY": COUNTRIES, "LOCATION": LOCATIONS, "ORGANIZATION": ORGANIZATIONS,
}

def build_pattern(terms):
    escaped = [re.escape(t) for t in sorted(terms, key=len, reverse=True)]
    return re.compile(r'(?<!\w)(' + '|'.join(escaped) + r')(?!\w)', re.IGNORECASE)

def replace_proper_nouns(text):
    if not isinstance(text, str):
        return text
    for token, terms in TOKEN_MAP.items():
        text = build_pattern(terms).sub(token, text)
    return AMOUNT_PAT.sub('[AMOUNT]', text)


# ── TTS / STT / 녹음 / 음성 분석 ─────────────────────────────────────────────

def text_to_speech(text, filename="question.mp3"):
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )
    with open(filename, "wb") as f:
        f.write(response.content)


def speech_to_text(audio_file):
    with open(audio_file, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcription.text


def record(duration=10, output_path="speech.wav"):
    print(f"  [녹음 중... {duration}초]")
    audio = sd.rec(int(duration * 44100), samplerate=44100, channels=1)
    sd.wait()
    write(output_path, 44100, audio)
    print("  [녹음 완료]")


def analyze_audio(audio_path, text):
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    word_count = len(text.split())
    speed = word_count / duration if duration > 0 else 0
    fillers = ["um", "uh", "like", "you know"]
    filler_count = sum(text.lower().count(f) for f in fillers)
    energy = np.mean(librosa.feature.rms(y=y))
    intervals = librosa.effects.split(y, top_db=20)
    speech_duration = sum((end - start) for start, end in intervals) / sr
    pause_duration = duration - speech_duration
    pause_ratio = pause_duration / duration if duration > 0 else 0
    return {
        "duration": round(duration, 2),
        "word_count": word_count,
        "speed": round(speed, 2),
        "filler_count": filler_count,
        "energy": round(float(energy), 4),
        "pause_duration": round(pause_duration, 2),
        "pause_ratio": round(pause_ratio, 2),
    }


# ── 메인 run 함수 ─────────────────────────────────────────────────────────────

def run_service_2_visa(
    user_pdf_path: str = "data_user_data/f-1_yuji.pdf",
    essay_pdf_path: str = None,
    n_questions: int = 3,
    record_duration: int = 10,
):
    """
    F1 비자 인터뷰 시뮬레이션 전체 파이프라인

    Args:
        user_pdf_path   : 사용자 개인정보 PDF 경로
        essay_pdf_path  : 에세이 PDF 경로 (없으면 None)
        n_questions     : 인터뷰 질문 수 (기본 3)
        record_duration : 녹음 시간(초) (기본 10)
    """

    # 1. PDF 데이터 → VectorDB ------------------------------------------------
    extract_pdf_data(user_pdf_path, "user_data")
    if essay_pdf_path:
        extract_pdf_data(essay_pdf_path, "essay")

    # 2. HuggingFace QA 데이터 로딩 & 전처리 → VectorDB ----------------------
    print("[DATA] Loading HuggingFace QA dataset...")
    df = load_dataset("Blessing988/f1_visa_transcripts")
    df = pd.DataFrame(df["train"])
    visa_df = df[['input', 'output']].copy()
    visa_df['input']  = visa_df['input'].apply(replace_proper_nouns)
    visa_df['output'] = visa_df['output'].apply(replace_proper_nouns)

    qa_docs = [
        Document(
            page_content=row["input"],
            metadata={"answer": row["output"], "source": "f1_visa_interview_qna", "type": "qa"}
        )
        for _, row in visa_df.iterrows()
    ]
    vector_store.add_documents(qa_docs)
    print(f"[DATA] {len(qa_docs)} QA docs added.")

    # 3. Retriever 세팅 --------------------------------------------------------
    qa_retriever   = vector_store.as_retriever(search_kwargs={"filter": {"type": "qa"}})
    user_retriever = vector_store.as_retriever(search_kwargs={"filter": {"type": "user_data"}, "k": 2})

    # 4. 사용자 프로필 로드 ----------------------------------------------------
    user_docs = user_retriever.invoke("")
    profile_context = "\n\n".join(doc.page_content for doc in user_docs)

    # 5. 인터뷰 루프 -----------------------------------------------------------
    history = []

    for i in range(n_questions):
        print(f"\n{'='*50}")
        print(f"Question {i+1} / {n_questions}")
        print('='*50)

        q_ref = random.choice(qa_retriever.invoke("F1 visa interview")).page_content

        history_text = "".join(
            f"Q: {h['question']}\nA: {h['answer']}\n" for h in history
        )

        question_prompt = f"""
        당신은 미국 F1 비자 인터뷰 면접관입니다.

        지원자 정보:
        {profile_context}

        이전 인터뷰:
        {history_text}

        참고 질문:
        {q_ref}

        [핵심 규칙]
        - 질문은 영어로 1~2문장으로 간결하게 작성하세요.
        - 참고 질문을 그대로 사용하는 것은 금지합니다.
        - 참고 질문은 오직 "문장 구조"만 참고하세요.
        - 반드시 지원자 정보의 실제 내용을 사용해서 질문을 생성하세요. (전공, 학교, 계획 등)
        - 이전 인터뷰의 질문과 같은 질문은 하지 않습니다.
        - 이전 인터뷰의 답변에 이어지는 꼬리질문은 금지합니다.
        - 없는 정보는 생성하지 않습니다.

        반드시 영어로 질문 1개만 출력하세요.
        """
        question = llm.invoke(question_prompt).content.strip()
        print(f"\nOfficer: {question}")

        text_to_speech(question, "question.mp3")
        # RunPod는 IPython Audio 불가 → mp3 파일로 저장만 함
        # (로컬에서 들으려면 scp로 받거나 play 커맨드 사용)

        input("\n엔터 누르고 말하세요 ▶ ")
        record(duration=record_duration)
        user_answer = speech_to_text("speech.wav")
        audio_features = analyze_audio("speech.wav", user_answer)

        print(f"User: {user_answer}")

        history.append({
            "question": question,
            "answer": user_answer,
            "audio": audio_features,
        })

    # 6. 최종 평가 -------------------------------------------------------------
    print(f"\n{'='*50}")
    print("Evaluating...")
    print('='*50)

    history_text  = ""
    audio_summary = ""

    a_ref = random.choice(qa_retriever.invoke("Suggested answers")).metadata["answer"]

    for i, h in enumerate(history, 1):
        history_text  += f"Q{i}: {h['question']}\nA{i}: {h['answer']}\n"
        a = h["audio"]
        audio_summary += (
            f"Q{i} Audio - duration: {a['duration']}, speed: {a['speed']}, "
            f"pause_ratio: {a['pause_ratio']}, filler_count: {a['filler_count']}\n"
        )

    final_prompt = f"""
    You are a US F1 visa officer.

    지원자 정보:
    {profile_context}

    참고 답변:
    {a_ref}

    이전 인터뷰:
    {history_text}

    음성 분석:
    {audio_summary}

    [핵심 규칙]
    - 평가 시 한국어로 출력합니다.

    [평가 기준]
    1. 사용자의 답변이 지원자 정보와 일치하는 내용인가를 평가하세요.
    2. 사용자의 답변이 논리성이 있는지 평가하세요.
    3. 사용자의 답변이 문법적으로 오류가 없는지 평가하세요.
    4. 사용자의 답변이 영어로 표현되었는지 평가하세요.
    5. 참고 답변과 비교하여 지원자의 답변이 인터뷰 질문에 적절히 답변했는지 평가하세요.
    6. 음성 분석에 기반하여 지원자의 자신감과 유창성을 평가하세요.
        - 말 속도가 너무 느리거나 빠르지 않은지 평가하세요.
        - pause 비율이 낮을수록 유창성이 높다고 평가하세요.
        - filler 사용이 적을수록 자신감이 높다고 평가하세요.

    Output:
    최종 결과: 비자 승인 또는 비자 거절
        - 실제 f1 비자 인터뷰의 결과에 맞게 "비자 승인" 또는 "비자 거절"로 출력하세요.
    전반적인 피드백:
        - 한국어 한 문단으로 지원자의 잘한 점과 개선할 점을 평가하세요.
    개선사항:
        - 구체적으로 무엇이 부족했는지 설명하세요.
        - 사용자의 대답마다 1~2문장으로 평가하세요.
    """

    final_evaluation = llm.invoke(final_prompt).content.strip()

    print("\n" + "=" * 50)
    print("Final Interview Result")
    print("=" * 50)
    print(final_evaluation)


# ── 엔트리포인트 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_service_2_visa(
        user_pdf_path="data_user_data/f-1_yuji.pdf",
        essay_pdf_path=None,   # 에세이 있으면 경로 입력
        n_questions=3,
        record_duration=10,
    )
