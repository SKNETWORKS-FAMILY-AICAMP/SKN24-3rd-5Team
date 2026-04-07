from langgraph.graph import MessagesState, END
from typing import Literal
from langchain_core.messages import AIMessage


DB_ERROR_KEYWORDS = ["error", "exception", "no such table", "syntax", "operationalerror", "invalid"]


def should_continue(state):
    last_message = state['messages'][-1]
    # 도구 호출(tool_calls)이 있다면 해당 도구 실행 노드(get_schema 등)로 이동
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # 호출된 도구 이름에 따라 분기
        tool_name = last_message.tool_calls[0]['name']
        if tool_name == "sql_db_schema": return "get_schema"
        if tool_name == "sql_db_query": return "check_query"

    # 도구 호출이 없고 답변이 완성되었다면
    if "SELECT" not in last_message.content:
        return "generate_answer" # 최종 답변으로
    return END


def should_continue_after_run(state: MessagesState) -> Literal["retry_query", "generate_answer"]:
    last_message = state['messages'][-1]
    content = (getattr(last_message, 'content', "") or "").lower()

    # 에러 키워드 포괄적으로 감지
    if any(keyword in content for keyword in DB_ERROR_KEYWORDS):
        return "retry_query"

    return "generate_answer"