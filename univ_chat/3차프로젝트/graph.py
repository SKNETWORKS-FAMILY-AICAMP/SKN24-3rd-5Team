from sqltool_llm.tools_llm import build_tools_and_llm
from nodes.tool_nodes import build_tool_nodes
from nodes.state_handlers import list_tables, call_get_schema, generate_query, check_query, retry_query, generate_answer
from nodes.conditions import should_continue, should_continue_after_run

from langgraph.graph import END, START, MessagesState, StateGraph

def build_state_graph():
    # 1. LLM + tools 
    llm, tools = build_tools_and_llm()

    # 2. ToolNode 
    get_schema_node, run_query_node = build_tool_nodes()

    # 3. Builder(StateGraph) 
    builder = StateGraph(MessagesState)
    
    # [수정] 노드 이름을 문자열로 명확히 지정해야 엣지 연결 시 혼선이 없습니다.
    builder.add_node("list_tables", list_tables)
    builder.add_node("call_get_schema", call_get_schema)
    builder.add_node("get_schema", get_schema_node)
    builder.add_node("generate_query", generate_query)
    builder.add_node("check_query", check_query)
    builder.add_node("run_query", run_query_node)
    builder.add_node("retry_query", retry_query)
    builder.add_node("generate_answer", generate_answer)

    # 4. Edge 연결
    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")

    # [중요] 조건부 엣지: 목적지(Mapping)를 명확히 작성해야 노드가 연결됩니다.
    builder.add_conditional_edges(
        "generate_query",
        should_continue,
        {
            "check_query": "check_query",
            "generate_answer": "generate_answer",
            "__end__": END
        }
    )

    builder.add_edge("check_query", "run_query")

    # [중요] 실행 후 답변으로 갈지 재시도할지 결정
    builder.add_conditional_edges(
        "run_query",
        should_continue_after_run,
        {
            "retry_query": "retry_query",
            "generate_answer": "generate_answer",
        }
    )

    # 에러 시 다시 실행 노드로, 답변 완료 시 종료로
    builder.add_edge("retry_query", "run_query")
    builder.add_edge("generate_answer", END)

    return builder

# 5. Agent 생성
builder = build_state_graph()