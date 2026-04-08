from langgraph.prebuilt import ToolNode
from sqltool_llm.tools_llm import build_tools_and_llm


def build_tool_nodes():
    _, tools = build_tools_and_llm()

    get_schema_tool = next(tool for tool in tools if tool.name == 'sql_db_schema')
    run_query_tool = next(tool for tool in tools if tool.name == 'sql_db_query')

    get_schema_node = ToolNode([get_schema_tool], name='get_schema')
    run_query_node = ToolNode([run_query_tool], name='run_query')
    return get_schema_node, run_query_node

get_schema_node, run_query_node = build_tool_nodes()

