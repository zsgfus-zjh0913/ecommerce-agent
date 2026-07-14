"""
Agent 核心 — 调用 DeepSeek API（OpenAI 兼容），处理 Tool Use 循环
"""

import json
import os
from pathlib import Path
from typing import AsyncGenerator

from openai import AsyncOpenAI
from dotenv import load_dotenv

from .memory import ConversationMemory
from .tools import execute_tool
from .tools_schema import TOOLS_SCHEMA

# 显式指定 .env 路径，确保从项目根目录加载
load_dotenv(Path(__file__).parent.parent / ".env")

SYSTEM_PROMPT = """你是一个专业的电商客服助手，名为"小智"。你服务的店铺主营服装、鞋帽、配饰等时尚品类。

## 你的职责
1. 热情友好地接待每一位顾客，语气自然亲切
2. 回答关于退换货、发货、支付、尺码等常见问题
3. 帮助用户查询订单状态和物流信息
4. 处理退换货申请
5. 根据用户需求推荐合适的商品

## 工具使用规则
- 用户询问店铺政策（退货、发货、运费、支付等）→ 必须调用 search_faq
- 用户想查订单、查物流 → 必须调用 lookup_order
- 用户明确要退货/退款/换货 → 必须调用 process_return
- 用户想买/求推荐/浏览商品 → 必须调用 recommend_products
- 一个工具结果不够时，可以多次调用工具

## 重要原则
- 永远使用工具来获取信息，不要编造任何数据
- 如果工具返回未找到，诚实告知用户，并建议联系人工客服
- 回复要结构化、清晰，适当使用换行和列表
- 不确定的事情不要猜测，积极引导用户提供更多信息
"""


class EcommerceAgent:
    """电商客服 Agent — DeepSeek 版"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key or "请替换" in self.api_key:
            raise ValueError("请先在 .env 文件中设置有效的 DEEPSEEK_API_KEY")

        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.memory = ConversationMemory(max_turns=20)
        self.tools = TOOLS_SCHEMA

    def reset(self):
        """重置对话历史"""
        self.memory.clear()

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        处理用户消息，流式返回结果。
        内部处理 Tool Use 循环（最多 5 轮），最终文本流式输出。
        """
        self.memory.add_user_message(user_message)

        for _ in range(5):  # 最多 5 轮 tool use
            # 调用 DeepSeek（流式）
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                + self.memory.get_messages(),
                tools=self.tools,
                stream=True,
            )

            # 收集流式响应
            content_chunks: list[str] = []
            tool_calls_map: dict[int, dict] = {}  # index → {id, name, args}

            async for chunk in stream:
                delta = chunk.choices[0].delta

                # 文本内容
                if delta.content:
                    content_chunks.append(delta.content)
                    yield delta.content

                # 工具调用
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "args": "",
                            }
                        if tc.id:
                            tool_calls_map[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_map[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_map[idx]["args"] += tc.function.arguments

            # 如果没有 tool_calls，对话结束
            if not tool_calls_map:
                full_text = "".join(content_chunks)
                self.memory.add_assistant_message(full_text if full_text else None)
                return

            # 保存 assistant 消息（含 tool_calls）
            tool_calls_for_memory = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                tool_calls_for_memory.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["args"],
                    },
                })
            self.memory.add_assistant_message(
                "".join(content_chunks) if content_chunks else None,
                tool_calls=tool_calls_for_memory,
            )

            # 执行所有工具并添加结果
            for tc in tool_calls_for_memory:
                try:
                    parsed_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    parsed_args = {}
                result = execute_tool(tc["function"]["name"], parsed_args)
                self.memory.add_tool_result(tc["id"], tc["function"]["name"], result)

        # 超过最大轮次
        yield "\n\n（系统提示：操作轮次已用完，如需进一步帮助请联系人工客服。）"
