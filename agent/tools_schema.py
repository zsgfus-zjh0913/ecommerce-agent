"""
OpenAI 兼容格式的 Tool Definitions
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "搜索电商FAQ知识库，查询退货政策、发货时效、运费标准、尺码选择等常见问题。当用户询问店铺政策、流程类问题时应使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户的问题关键词，如'退货'、'运费'、'尺码'等",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "根据订单号或手机号查询订单的当前状态、物流信息、商品详情。当用户想查看订单、物流时应使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，如 ORD-2024001",
                    },
                    "phone": {
                        "type": "string",
                        "description": "用户手机号（部分隐藏），如 138****6789",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_return",
            "description": "为用户创建退货或换货申请。当用户明确要退货、退款、换货时应使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "要退换的订单号",
                    },
                    "reason": {
                        "type": "string",
                        "description": "退换货原因，如'尺码不合适'、'质量问题'、'不想要了'",
                    },
                    "action": {
                        "type": "string",
                        "enum": ["return", "exchange"],
                        "description": "退货退款还是换货",
                    },
                },
                "required": ["order_id", "reason", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_products",
            "description": "根据用户偏好和需求，从商品目录中推荐合适商品。当用户想购物、求推荐、浏览商品时应使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户的需求描述，如'夏季连衣裙'、'男士商务衬衫'",
                    },
                    "category": {
                        "type": "string",
                        "description": "商品品类：上衣、裤装、裙装、外套、鞋靴、配饰",
                    },
                },
            },
        },
    },
]
