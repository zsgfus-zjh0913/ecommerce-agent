"""
对话历史管理 — 滑动窗口，保留最近 N 轮对话
使用 OpenAI 兼容消息格式
"""


class ConversationMemory:
    """管理多轮对话上下文，支持 OpenAI 兼容的 Messages API 格式"""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[dict] = []

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str | None, tool_calls: list[dict] | None = None):
        """
        保存 assistant 消息。
        - 纯文本时 content 为字符串
        - 有 tool_calls 时，content 可为 None，tool_calls 为列表
        """
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        self._trim()

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str):
        """添加工具执行结果"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result,
        })

    def _trim(self):
        """保持总轮次不超过 max_turns"""
        user_count = sum(1 for m in self.messages if m["role"] == "user")
        while user_count > self.max_turns:
            idx_user = next(i for i, m in enumerate(self.messages) if m["role"] == "user")
            self.messages.pop(idx_user)
            if idx_user < len(self.messages) and self.messages[idx_user]["role"] == "assistant":
                self.messages.pop(idx_user)
            user_count -= 1

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def clear(self):
        self.messages = []
