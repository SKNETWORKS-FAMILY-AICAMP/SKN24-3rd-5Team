from langgraph.graph import MessagesState, END
from typing import Literal

DB_ERROR_KEYWORDS = ["error", "exception", "no such table", "syntax", "operationalerror", "invalid"]

# 1. SQL 서비스 내부용: 툴을 더 쓸지 답변을 만들지 결정
def should_continue(state: MessagesState):
    """Service 1(SQL) 내부 노드 흐름 제어"""
    last_message = state['messages'][-1]
    
    # 모델이 도구를 호출했다면 해당 도구 노드로 이동
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_name = last_message.tool_calls[0]['name']
        if tool_name == "sql_db_schema": 
            return "get_schema"
        if tool_name == "sql_db_query": 
            return "check_query"

    # 도구 호출이 없고, 텍스트에 SELECT(쿼리)가 없다면 답변 생성
    content = (getattr(last_message, 'content', "") or "")
    if "SELECT" not in content:
        return "generate_answer"
        
    return "__end__"

# 2. SQL 서비스 내부용: 쿼리 실행 후 에러가 났을 때 재시도 여부 결정
def should_continue_after_run(state: MessagesState) -> Literal["retry_query", "generate_answer"]:
    """쿼리 실행 결과 에러 여부 판단"""
    last_message = state['messages'][-1]
    content = (getattr(last_message, 'content', "") or "").lower()

    if any(keyword in content for keyword in DB_ERROR_KEYWORDS):
        return "retry_query"

    return "generate_answer"

# 3. 메인 라우터용: 질문의 카테고리에 따라 어떤 서비스로 보낼지 결정
def route_decision(state: MultiAgentState):
    # router_node에서 저장한 route 값을 읽습니다.
    # 만약 값이 없으면 기본적으로 service1로 보냅니다.
    target = state.get("route", "service1")
    print(f"--- [EDGE DEBUG] 다음 노드로 이동: {target} ---")
    return target