
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_ollama import ChatOllama
from db.query_connection import get_db
import os

# os.chdir("/workspace/3차프로젝트")

# os.chdir(r"C:\skn24\수업자료\08_large_language_model\05_langgraph\3차프로젝트")
# from db.query_connection import get_db

def build_tools_and_llm():
    """
    DB 연결 + LLM + SQLToolkit 준비
    """
    db = get_db()

    llm = ChatOllama(
        # model="ebdm/gemma3-enhanced:12b",
        model="ebdm/gemma3-enhanced:12b",
        temperature=0
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    
    # agent = create_sql_agent(
    #     llm=llm,
    #     toolkit=toolkit,
    #     verbose=True
    # )

    return llm, tools
