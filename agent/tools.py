"""
工具定义 — 供 Claude Tool Use 调用

四个工具：
1. search_faq       — 搜索 FAQ 知识库
2. lookup_order     — 查询订单
3. process_return   — 处理退换货
4. recommend_products — 商品推荐
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from .tools_schema import TOOLS_SCHEMA

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: list[dict]):
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据 tool_name 分发到对应函数，返回 JSON 字符串结果"""

    if tool_name == "search_faq":
        return _search_faq(arguments.get("query", ""))
    elif tool_name == "lookup_order":
        return _lookup_order(arguments.get("order_id", ""), arguments.get("phone", ""))
    elif tool_name == "process_return":
        return _process_return(
            arguments.get("order_id", ""),
            arguments.get("reason", ""),
            arguments.get("action", "return"),
        )
    elif tool_name == "recommend_products":
        return _recommend_products(arguments.get("query", ""), arguments.get("category", ""))
    else:
        return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def _search_faq(query: str) -> str:
    """关键词 + 简单匹配搜索 FAQ"""
    if not query:
        return json.dumps({"error": "请提供要查询的问题"}, ensure_ascii=False)

    from utils.search import search_faq

    results = search_faq(query, top_k=3)
    if not results:
        return json.dumps({
            "found": False,
            "message": "未找到匹配的FAQ，建议转人工客服。",
            "results": [],
        }, ensure_ascii=False)

    return json.dumps({
        "found": True,
        "message": f"找到 {len(results)} 条相关问题",
        "results": [
            {"question": r["question"], "answer": r["answer"]} for r in results
        ],
    }, ensure_ascii=False)


def _lookup_order(order_id: str, phone: str) -> str:
    """按订单号或手机号查询订单"""
    if not order_id and not phone:
        return json.dumps({"error": "请提供订单号或手机号"}, ensure_ascii=False)

    orders = load_json("orders.json")

    if order_id:
        matched = [o for o in orders if o["order_id"].upper() == order_id.upper()]
    else:
        matched = [o for o in orders if o["phone"] == phone]

    if not matched:
        return json.dumps({
            "found": False,
            "message": "未找到该订单，请核实订单号或手机号是否正确。",
            "orders": [],
        }, ensure_ascii=False)

    # 返回简化的订单信息
    result_orders = []
    for o in matched:
        info = {
            "order_id": o["order_id"],
            "status": o["status"],
            "total": o["total"],
            "items": o["items"],
            "order_time": o["order_time"],
            "logistics": o.get("logistics"),
        }
        if o.get("return_info"):
            info["return_info"] = o["return_info"]
        result_orders.append(info)

    return json.dumps({
        "found": True,
        "message": f"找到 {len(matched)} 个订单",
        "orders": result_orders,
    }, ensure_ascii=False)


def _process_return(order_id: str, reason: str, action: str) -> str:
    """处理退换货申请"""
    if not order_id:
        return json.dumps({"error": "请提供订单号"}, ensure_ascii=False)
    if not reason:
        return json.dumps({"error": "请说明退换货原因"}, ensure_ascii=False)

    orders = load_json("orders.json")
    matched = [o for o in orders if o["order_id"].upper() == order_id.upper()]

    if not matched:
        return json.dumps({
            "success": False,
            "message": "未找到该订单，请核实订单号。",
        }, ensure_ascii=False)

    order = matched[0]

    # 检查是否可以退换
    if not order.get("can_return", False):
        return json.dumps({
            "success": False,
            "message": f"订单 {order_id} 当前状态为「{order['status']}」，暂不支持退换货。"
                       f"{'退货截止日期已过' if order.get('return_deadline') else ''}",
        }, ensure_ascii=False)

    # 生成退货单
    return_id = f"RTN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    action_text = "退货退款" if action == "return" else "换货"

    return json.dumps({
        "success": True,
        "message": f"已为您创建{action_text}申请",
        "return_id": return_id,
        "order_id": order_id,
        "action": action_text,
        "reason": reason,
        "refund_amount": order["total"],
        "instructions": [
            "1. 请将商品包装完好，附上退货单号",
            "2. 寄回地址：XX省XX市XX区XX路XX号 电商仓储部收",
            "3. 请在包裹内附纸条写明退货单号 RTN-" + return_id,
            "4. 仓库验收后，退款将在3-5个工作日内原路返回",
        ],
    }, ensure_ascii=False)


def _recommend_products(query: str, category: str) -> str:
    """搜索并推荐商品"""
    if not query and not category:
        return json.dumps({"error": "请描述您的需求或需要的品类"}, ensure_ascii=False)

    from utils.search import search_products

    search_query = query or category
    results = search_products(search_query, top_k=5)

    if not results:
        return json.dumps({
            "found": False,
            "message": "未找到匹配的商品，您可以尝试其他关键词。",
            "products": [],
        }, ensure_ascii=False)

    return json.dumps({
        "found": True,
        "message": f"为您找到 {len(results)} 款相关商品",
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "category": p["category"],
                "colors": p["colors"],
                "sizes": p["sizes"],
                "rating": p["rating"],
                "description": p["description"],
                "tags": p["tags"],
                "in_stock": p["stock"] > 0,
            }
            for p in results
        ],
    }, ensure_ascii=False)
