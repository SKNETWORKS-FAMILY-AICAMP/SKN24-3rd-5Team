import asyncio
import json
import os
from typing import List, Optional
from dotenv import load_dotenv

# Playwright
from playwright.async_api import async_playwright

# OpenAI & Pydantic imports
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Load environment variables (.env file)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)



class SchoolInfo(BaseModel):
    school_code: str = Field(description="Unique short code of the school, e.g. 'NYU'")
    name: str = Field(description="Full official name of the university")
    country: str = Field(description="Country of the school, e.g., 'USA' or 'United States'")
    address: str = Field(description="Address or City/State location, e.g., 'New York, NY'")

class AdmissionInfo(BaseModel):
    admission_id: str = Field(description="Unique admission ID, e.g. 'NYU_ADM'")
    school_code: str = Field(description="Unique school code, e.g. 'NYU'")
    tuition: Optional[int] = Field(description="Annual tuition fee as an integer (e.g., 60000). Use null if not found.")
    regular_deadline: str = Field(description="Regular admission deadline, e.g., 'Jan 1'")
    early_deadline: str = Field(description="Early Action/Decision deadline, e.g., 'Nov 1'")

class RequirementInfo(BaseModel):
    requirement_id: str = Field(description="Unique requirement ID, e.g. 'NYU_REQ_1'")
    school_code: str = Field(description="Unique school code, e.g. 'NYU'")
    document_type: str = Field(description="e.g. 'SAT/ACT', 'TOEFL', 'IELTS', 'Duolingo', 'PTE', 'Cambridge English', 'iTEP', 'Essay', 'Recommendation Letter', 'Portfolio', 'Audition', 'Transcript'")
    requirement_policy: str = Field(description="e.g. 'Required', 'Conditionally Required', 'Optional', 'Test-Free', 'Recommended'. Note: English Language Tests (TOEFL, IELTS, Duolingo, etc.) should be 'Conditionally Required' since you MUST take at least one if you are a non-native speaker.")
    metric_name: str = Field(description="e.g. 'Competitive Score', 'Minimum Score', 'Quantity required', 'Minimum GPA'")
    metric_value: str = Field(description="e.g. '100', '135', '7.5', '191', '70'. MUST extract the exact numeric score if a competitive/recommended score is mentioned. ONLY use 'N/A' if numbers are completely missing.")
    notes: str = Field(description="Specific nuances. If the extracted score is 'competitive' or 'recommended' rather than a strict minimum, you MUST explicitly state that caveat here (e.g., 'No strict minimum, but this is the competitive score'). Keep under 2 sentences.")

class FAQ(BaseModel):
    school_code: str = Field(description="School code")
    category: str = Field(description="Category")
    question: str = Field(description="Question")
    answer: str = Field(description="Answer")


class RAGDocument(BaseModel):
    school: str = Field(description="University name (e.g., NYU, USC)") # 학교 이름
    school_code: str                                                    # 학교 코드
    
    category: str = Field(
        description="essay, philosophy, international, major, culture, faq, scholarship, housing"
    ) # 카테고리 (에세이, 철학, 국제, 전공, 문화, faq, 장학금, 주거)
    
    title: str = Field(
        description="Short title of the chunk (used for better retrieval relevance)"
    ) # 청크 제목 (문서 내에서)
    
    content: str = Field(
        description="A coherent, natural language SUMMARY of the topic written in 1-3 paragraphs. DO NOT copy-paste raw UI text, button labels, or broken table headers (like 'TOTAL HOUSEHOLD INCOME'). Synthesize the information into complete, readable sentences."
    ) # 청크 내용 (문서 내에서)
    
    source_url: str = Field(
        description="Original page URL"
    ) # 원본 페이지 url

class UniversityExtraction(BaseModel):
    school_info: SchoolInfo
    admission_info: AdmissionInfo
    requirements: List[RequirementInfo]
    faq_info: List[FAQ]
    rag_docs: List[RAGDocument]

URLS = {
    "NYU": [
        "https://www.nyu.edu/admissions/undergraduate-admissions.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/all-freshmen-applicants.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/international-applicants.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/nyu-facts.html",
        "https://www.nyu.edu/admissions/financial-aid-and-scholarships.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/all-freshmen-applicants/additional-program-requirements.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/standardized-tests.html",
        "https://www.nyu.edu/admissions/financial-aid-and-scholarships/cost-of-attendance.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/standardized-tests/english-language-testing.html",
        "https://www.nyu.edu/about/news-publications/nyu-at-a-glance.html",
        "https://www.nyu.edu/admissions/undergraduate-admissions/admitted-students/spring-admission.html"
    ],
    # "USC": [
    #     "https://admission.usc.edu/apply/first-year-students/",
    #     "https://admission.usc.edu/apply/dates-deadlines/",
    #     "https://admission.usc.edu/apply/international-students/",
    #     "https://admission.usc.edu/cost-and-financial-aid/financial-aid-and-scholarships/",
    #     "https://admission.usc.edu/test-optional-faq/",
    #     "https://admission.usc.edu/admitted-students/faq/",
    #     "https://admission.usc.edu/prospective-students/how-to-apply/deadline-faqs/"
    # ],
    # "UIUC": [
    #     "https://www.admissions.illinois.edu/apply/freshman/requirements", 
    #     "https://www.admissions.illinois.edu/apply/freshman/dates",        
    #     "https://www.admissions.illinois.edu/apply/freshman/profile",      
    #     "https://www.admissions.illinois.edu/invest/tuition",
    #     "https://www.admissions.illinois.edu/faq/admitted-international",
    #     "https://www.admissions.illinois.edu/faq/applicant-freshman",
    #     "https://www.admissions.illinois.edu/faq",
    #     "https://www.admissions.illinois.edu/apply/freshman/essays",
    #     "https://www.commonapp.org/apply/essay-prompts"
    # ],
    # "Columbia": [
    #     "https://undergrad.admissions.columbia.edu/apply/first-year/instructions",
    #     "https://undergrad.admissions.columbia.edu/apply/first-year/deadlines",
    #     "https://undergrad.admissions.columbia.edu/apply/international/english-proficiency",
    #     "https://undergrad.admissions.columbia.edu/content/class-profile",
    #     "https://undergrad.admissions.columbia.edu/apply/international/aid",
    #     "https://cc-seas.financialaid.columbia.edu/eligibility/facts",
    #     "https://undergrad.admissions.columbia.edu/apply/firstyear",
    #     "https://undergrad.admissions.columbia.edu/apply/international",
    #     "https://undergrad.admissions.columbia.edu/faq",
    # ],
    # "UCLA": [
    #     "https://admission.ucla.edu/apply/international-applicants",
    #     "https://financialaid.ucla.edu/undergraduate/cost-of-attendance",
    #     "https://admission.ucla.edu/apply/first-year",
    #     "https://admission.ucla.edu/apply/first-year/first-year-requirements",
    #     "https://admission.ucla.edu/apply/first-year/first-year-profile/2025",
    #     "https://admission.ucla.edu/apply/majors",
    #     "https://admission.ucla.edu/apply/supplemental-applications",
    #     "https://admission.ucla.edu/sites/default/files/documents/UCLA-Counselor-Admission-FAQ-March-2025_0.pdf",
    #     "https://admission.ucla.edu/apply/first-year/personal-insight-questions"
    # ],
    # "BU": [
    #     "https://www.bu.edu/admissions/apply/first-year/",
    #     "https://www.bu.edu/admissions/apply/deadlines/",
    #     "https://www.bu.edu/admissions/apply/international/",
    #     "https://www.bu.edu/admissions/why-bu/class-profile/",
    #     "https://www.bu.edu/finaid/aid-basics/cost-of-education/",
    #     "https://www.bu.edu/careers/students/outcomes/",
    #     "https://www.bu.edu/admissions/apply/faqs-helpful-forms/faqs/"
    # ],
    # "UCBerkeley": [
    #     "https://admissions.berkeley.edu/apply-to-berkeley/first-year-applicants-uc-berkeley/",
    #     "https://admissions.berkeley.edu/apply-to-berkeley/application-resources/selection-process/",
    #     "https://admissions.berkeley.edu/apply-to-berkeley/first-year-applicants-uc-berkeley/first-year-policy-changes/",
    #     "https://admissions.berkeley.edu/apply-to-berkeley/international-students/",
    #     "https://admissions.berkeley.edu/apply-to-berkeley/student-profile/",
    #     "https://financialaid.berkeley.edu/how-aid-works/cost-of-attendance/",
    #     "https://career.berkeley.edu/start-exploring/where-do-cal-grads-go/",
    #     "https://admissions.berkeley.edu/application-faqs/",
    #     "https://admission.universityofcalifornia.edu/apply-now.html",
    #     "https://admission.universityofcalifornia.edu/apply-now/freshman-applicants/"
    # ],
    # "UCSD": [
    #     "https://admissions.ucsd.edu/first-year/application-requirements.html",
    #     "https://admissions.ucsd.edu/international/index.html",
    #     "https://admissions.ucsd.edu/first-year/freshman-profile.html",
    #     "https://fas.ucsd.edu/cost-of-attendance/undergraduates/index.html",
    #     "https://admissions.ucsd.edu/first-year/application-timeline.html",
    #     "https://admissions.ucsd.edu/first-year/application-review.html",
    #     "https://admissions.ucsd.edu/faq/index.html"
    # ],
    # "Purdue": [
    #     "https://admissions.purdue.edu/become-student/class-profile/",
    #     "https://admissions.purdue.edu/become-student/guide/",
    #     "https://admissions.purdue.edu/become-student/international/",
    #     "https://admissions.purdue.edu/become-student/english-proficiency/",
    #     "https://admissions.purdue.edu/become-student/course-requirements/",
    #     "https://admissions.purdue.edu/become-student/first-year-criteria/",
    #     "https://admissions.purdue.edu/become-student/guide/#essay-guide",
    #     "https://admissions.purdue.edu/become-student/deadlines/",
    #     "https://admissions.purdue.edu/academics/majors/",
    #     "https://www.purdue.edu/treasurer/finance/bursar-office/tuition/fee-rates-2025-2026/undergraduate-tuition-and-fees-2025-2026/"
    # ],
    # "PennState": [
    #     "https://admissions.psu.edu/apply/requirements/",
    #     "https://www.psu.edu/admission/undergraduate",
    #     "https://www.psu.edu/resources/international-students/deadlines",
    #     "https://admissions.psu.edu/apply/international/requirements/",
    #     "https://admissions.psu.edu/apply/statistics/",
    #     "https://www.psu.edu/academics/undergraduate/majors",
    #     "https://tuition.psu.edu/",
    #     "https://www.psu.edu/resources/international-students/steps-to-apply",
    #     "https://www.psu.edu/resources/first-year-students/requirements",
    #     "https://www.psu.edu/resources/first-year-students/eligibility",
    #     "https://www.psu.edu/resources/international-students/application-review",
    #     "https://www.psu.edu/resources/international-students/credentials/south-korea",
    #     "https://www.psu.edu/admission/undergraduate/how-to-apply",
    #     "https://www.psu.edu/resources/first-year-students/steps-to-apply",
    #     "https://www.psu.edu/resources/faq/general",
    #     "https://www.psu.edu/resources/faq/international-students",
    #     "https://www.psu.edu/resources/faq/application-process",
    #     "https://www.psu.edu/resources/faq/financial-aid"
    # ]
}

async def fetch_and_extract(name: str, url_list: List[str], browser) -> Optional[UniversityExtraction]:
    combined_body_text = ""
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        for url in url_list:
            print(f"\n[{name}] Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)
            text = await page.evaluate("() => document.body.innerText")
            combined_body_text += f"\n\n--- CONTENT FROM {url} ---\n\n" + text
            print(combined_body_text)
            
        await context.close()
        
        print(f"[{name}] Fetched {len(combined_body_text)} total characters. Starting OpenAI analysis...")
        
        trimmed_text = combined_body_text[:80000] # 토큰 제한으로 인해 80000자만 사용
        
        completion = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a specialized US University Admissions AI assistant. Extract FAQ data (Questions and Answers) and unstructured narrative text (RAG VectorDBs) directly from the raw website text. For RAG VectorDBs, synthesize the information into coherent, natural language sentences. DO NOT just copy-paste raw website UI text or broken tables. The text contains blocks starting with '--- CONTENT FROM <URL> ---'. Use this to assign 'source_url'. Use the provided 'school_code'."
                },
                {"role": "user", "content": f"Target University School Code: {name}\nRAW WEBSITE TEXT:\n{trimmed_text}"}
            ],
            response_format=UniversityExtraction,
        )
        
        extracted_data = completion.choices[0].message.parsed
        print(f"[{name}] Extraction Successful!")
        return extracted_data

    except Exception as e:
        print(f"[{name}] Crawl/Extract Error: {e}")
        return None

# 메인 실행
async def main():
    if not OPENAI_API_KEY:
        print("CRITICAL: OPENAI_API_KEY is not set in the environment or .env file.")
        return

    all_schools = []
    all_admissions = []
    all_requirements = []
    all_rag_docs = []
    all_faqs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 크롤링 및 LLM 추출
        for name, url_list in URLS.items():
            result = await fetch_and_extract(name, url_list, browser)
            if result:
                school_code = name

                
                
                # 데이터 변환 및 리스트 추가
                all_schools.append(result.school_info.model_dump())
                
                adm_dict = result.admission_info.model_dump()
                adm_dict["admission_id"] = f"{school_code}_ADM"
                adm_dict["school_code"] = school_code
                all_admissions.append(adm_dict)
                
                req_idx = 1
                for req in result.requirements:
                    req_dict = req.model_dump()
                    req_dict["requirement_id"] = f"{school_code}_REQ_{req_idx}"
                    req_dict["school_code"] = school_code
                    all_requirements.append(req_dict)
                    req_idx += 1

                faq_idx = 1
                for faq in result.faq_info:
                    faq_dict = faq.model_dump()
                    faq_dict["faq_id"] = f"{school_code}_FAQ_{faq_idx}"
                    faq_dict["school_code"] = school_code
                    all_faqs.append(faq_dict)
                    faq_idx += 1

                for doc in result.rag_docs:
                    all_rag_docs.append(doc.model_dump())
                    
        await browser.close()
        
    # json 파일로 저장
    print("\n[Save] Writing data to JSON files for inspection...")
    os.makedirs("data/raw_json", exist_ok=True)
    
    with open("data/raw_json/rdb_schools1.json", "w", encoding="utf-8") as f:
        json.dump(all_schools, f, indent=4, ensure_ascii=False)
        
    with open("data/raw_json/rdb_admissions1.json", "w", encoding="utf-8") as f:
        json.dump(all_admissions, f, indent=4, ensure_ascii=False)
        
    with open("data/raw_json/rdb_requirements1.json", "w", encoding="utf-8") as f:
        json.dump(all_requirements, f, indent=4, ensure_ascii=False)

    with open("data/raw_json/rdb_faqs1.json", "w", encoding="utf-8") as f:
        json.dump(all_faqs, f, indent=4, ensure_ascii=False)
        
    with open("data/raw_json/chromadb_docs1.json", "w", encoding="utf-8") as f:
        json.dump(all_rag_docs, f, indent=4, ensure_ascii=False)
        
    print("[Save] Created rdb_schools.json, rdb_admissions.json, rdb_requirements.json, rdb_faqs.json, and chromadb_docs.json")

if __name__ == "__main__":
    asyncio.run(main())
