import httpx
from .config import Config

MCP_URL = Config.MCP_SERVER_URL

async def get_tools():
    """Асинхронно получить список доступных MCP-инструментов."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MCP_URL}/tools")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": f"Не удалось получить список инструментов: {str(e)}"}

async def call_tool(tool_name: str, arguments: dict = None):
    """Асинхронно вызвать инструмент на MCP-сервере."""
    if arguments is None:
        arguments = {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{MCP_URL}/call",
                json={"tool": tool_name, "arguments": arguments}
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", "Инструмент выполнен, но результат пуст.")
    except Exception as e:
        return f"Ошибка при вызове инструмента: {str(e)}"