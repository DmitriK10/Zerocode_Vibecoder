from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import uvicorn

from .db import init_db
from .tools import MCP_TOOLS, TOOL_FUNCTIONS

init_db()

app = FastAPI(title="MCP Server", description="MCP-сервер для кинотеки")

@app.get("/tools")
async def get_tools():
    return MCP_TOOLS

class CallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}

@app.post("/call")
async def call_tool(request: CallRequest):
    tool_name = request.tool
    args = request.arguments

    if tool_name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"Инструмент '{tool_name}' не найден")

    # Находим описание инструмента в MCP_TOOLS
    tool_schema = next((t for t in MCP_TOOLS if t['name'] == tool_name), None)
    if tool_schema:
        required = tool_schema.get('inputSchema', {}).get('required', [])
        # Проверяем наличие всех обязательных аргументов
        missing = [r for r in required if r not in args]
        if missing:
            raise HTTPException(status_code=400, detail=f"Отсутствуют обязательные аргументы: {', '.join(missing)}")

    func = TOOL_FUNCTIONS[tool_name]
    try:
        if args:
            result = func(**args)
        else:
            result = func()
        if not isinstance(result, str):
            import json
            result = json.dumps(result, ensure_ascii=False, indent=2)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("mcp_server.server:app", host="127.0.0.1", port=8000, reload=True)