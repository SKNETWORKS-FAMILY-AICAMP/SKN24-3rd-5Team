from dotenv import load_dotenv
import os
from graph import builder

# os.chdir("/workspace/3차프로젝트")
# 현재 경로 기준으로 .env 불러오기
load_dotenv(dotenv_path="C:/skn24/수업자료/08_large_language_model/05_langgraph/3차프로젝트/env")
# load_dotenv()
agent = builder.compile()

def run_service_1_agent(question: str) -> str:
    result = ""
    for step in agent.stream(
        {'messages': [{'role': 'user', 'content': question}]},
        stream_mode='values'
    ):
        message = step['messages'][-1]
        if message.type == 'ai' and message.content and not message.tool_calls:
            result = message.content
    return result.pretty_print() 

# run_service_1_agent('펜실베니아 대학에서 가장 많이 묻는 질문이 뭔지 알려줘')