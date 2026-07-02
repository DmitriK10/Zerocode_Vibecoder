import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from tools import tools
from memory import FileChatMessageHistory

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MEMORY_FILE = os.path.abspath("memory.json")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Ты — AI-агент, который помогает пользователям выполнять задачи. Ты умеешь:
- Искать информацию в интернете (web_search)
- Получать текущую погоду для любого города (get_weather)
- Узнавать курс криптовалют (get_crypto_price)
- Узнавать курс обычных валют (get_exchange_rate)      
- Генерировать QR-коды из текста (generate_qr)          
- Читать и записывать файлы (file_read, file_write)
- Выполнять ограниченные терминальные команды (run_command)

Отвечай на русском языке, будь вежливым и полезным. Если нужно уточнить информацию, задавай вопросы."""),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def get_session_history(session_id: str):
    return FileChatMessageHistory(MEMORY_FILE, session_id)

agent_with_memory = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

def run_agent(user_input: str, session_id: str) -> str:
    try:
        result = agent_with_memory.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        return result["output"]
    except Exception as e:
        return f"Ошибка выполнения агента: {str(e)}"