"""
电商客服 AI Agent — FastAPI 入口
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from agent.core import EcommerceAgent

app = FastAPI(title="电商客服 AI Agent", version="1.0.0")

# 挂载静态文件
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 全局 Agent 实例（每个请求共用，对话历史存于内存中）
agent = EcommerceAgent()


@app.get("/", response_class=HTMLResponse)
async def index():
    """聊天界面"""
    html_file = static_dir / "index.html"
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "电商客服 AI Agent"}


@app.post("/api/chat")
async def chat(request: Request):
    """SSE 流式聊天接口"""
    body = await request.json()
    user_message = body.get("message", "").strip()

    if not user_message:
        return StreamingResponse(
            _single_event("请输入消息内容"),
            media_type="text/event-stream",
        )

    async def stream():
        try:
            async for chunk in agent.chat(user_message):
                yield _sse(chunk)
            yield _sse("[DONE]")
        except Exception as e:
            yield _sse(f"抱歉，系统出了点问题：{str(e)}")
            yield _sse("[DONE]")

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/reset")
async def reset():
    """重置对话"""
    agent.reset()
    return {"status": "ok", "message": "对话已重置"}


def _sse(text: str) -> str:
    """格式化 SSE 消息"""
    return f"data: {json.dumps(text, ensure_ascii=False)}\n\n"


async def _single_event(text: str):
    yield _sse(text)
    yield _sse("[DONE]")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8002, reload=True)
