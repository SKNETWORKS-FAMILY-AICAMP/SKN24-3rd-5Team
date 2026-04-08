from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from sqltool_llm.tools_llm import build_tools_and_llm
from typing import Dict, Any
from prompts import (
    generate_query_system_prompt,
    check_query_system_prompt,
    retry_query_system_prompt,
    generate_answer_system_prompt
)
def list_tables(state: MessagesState):
    """테이블 목록 조회 및 텍스트 가이드 출력"""
    _, tools = build_tools_and_llm()
    
    # 1. 실제 도구 실행
    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_result = list_tables_tool.invoke({})
    
    # 2. 모델이 인식할 수 있도록 AIMessage로 테이블 목록 전달
    # 이 메시지가 있어야 다음 노드에서 어떤 테이블을 쓸지 판단함
    response = AIMessage(content=f"사용 가능한 테이블: {tool_result}")
    
    return {'messages': [response]}
    
def call_get_schema(state: MessagesState):
    llm, tools = build_tools_and_llm()
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    llm_with_tools = llm.bind_tools([get_schema_tool]) 

    # 핵심: 기존의 강력한 가이드를 SystemMessage로 먼저 깔아줍니다.
    # 그리고 그 뒤에 "그러니까 지금 스키마를 조회해"라는 지시를 덧붙입니다.
    combined_prompt = generate_query_system_prompt + "\n\n[명령] 위 규칙을 바탕으로 질문에 필요한 테이블의 스키마를 sql_db_schema로 조회하세요."
    
    response = llm_with_tools.invoke(
        [SystemMessage(content=combined_prompt)] + state['messages']
    )
    
    return {'messages': [response]}


def generate_query(state: MessagesState):
    llm, tools = build_tools_and_llm()
    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
    llm_with_tools = llm.bind_tools([run_query_tool])

    # 기존 프롬프트 대신 SystemMessage로 명시
    response = llm_with_tools.invoke([SystemMessage(content=generate_query_system_prompt)] + state["messages"])

    return {"messages": [response]}
    
def check_query(state: MessagesState):
    """쿼리 검증"""
    from prompts import check_query_system_prompt
    llm, tools = build_tools_and_llm()
    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")

    llm_with_tools = llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([SystemMessage(content=check_query_system_prompt)] + state['messages'])

    return {'messages': [response]}

def retry_query(state: MessagesState):
    """실패 시 재시도 로직"""
    from prompts import retry_query_system_prompt
    
    retry_count = state.get('retry_count', 0)
    if retry_count >= 3:
        return {"messages": [AIMessage(content="죄송합니다. 쿼리를 생성하는 데 실패했습니다. 다시 시도해 주세요.")]}

    llm, tools = build_tools_and_llm()
    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")

    # 마지막 에러 내용 추출
    last_msg = state['messages'][-1]
    error_context = f"에러 내용: {last_msg.content}" if isinstance(last_msg, ToolMessage) else ""

    llm_with_tools = llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([
        SystemMessage(content=retry_query_system_prompt),
        AIMessage(content=f"이전 실행 에러: {error_context}. 쿼리를 수정해서 다시 실행하세요.")
    ])

    return {'messages': [response], 'retry_count': retry_count + 1}

# def generate_answer(state: MessagesState):
#     """최종 챗봇 답변 생성 (도구 사용 X, 일반 LLM 호출)"""
#     from prompts import generate_answer_system_prompt
#     llm, _ = build_tools_and_llm()

#     # DB 결과 데이터가 state['messages']에 ToolMessage 형태로 들어있음
#     # 이를 바탕으로 친절한 답변 생성
#     response = llm.invoke([SystemMessage(content=generate_answer_system_prompt)] + state['messages'])

#     return {'messages': [response]}


def generate_answer(state: MessagesState):
    from prompts import generate_answer_system_prompt
    llm, _ = build_tools_and_llm()

    tool_results = [
        msg.content for msg in state["messages"]
        if isinstance(msg, ToolMessage)
    ]

    context = "\n".join(tool_results)

    prompt = f"""
{generate_answer_system_prompt}

다음 DB 조회 결과를 바탕으로 질문에 답하세요:

{context}
"""

    question = state["messages"][0].content

    response = llm.invoke(prompt + f"\n\n질문: {question}")

    return {
        "messages": [AIMessage(content=response.content)]
    }