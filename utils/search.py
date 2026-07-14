"""
简易搜索工具 — 关键词匹配 + Jaccard 相似度
用于在 FAQ 和商品列表中进行模糊搜索
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    """加载 data/ 目录下的 JSON 文件"""
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> set[str]:
    """中文简易分词：2-grams + 单字"""
    text = text.lower().strip()
    bigrams = {text[i : i + 2] for i in range(len(text) - 1)}
    singles = set(text)
    return bigrams | singles


def jaccard_similarity(query_tokens: set, target_tokens: set) -> float:
    """Jaccard 相似度"""
    if not query_tokens or not target_tokens:
        return 0
    intersection = query_tokens & target_tokens
    union = query_tokens | target_tokens
    return len(intersection) / len(union) if union else 0


def keyword_match(query: str, keywords: list[str]) -> float:
    """关键词匹配得分：query 中包含的关键词越多，分越高"""
    query_lower = query.lower()
    matched = sum(1 for kw in keywords if kw in query_lower)
    return matched / len(keywords) if keywords else 0


def search_faq(query: str, top_k: int = 3) -> list[dict]:
    """
    综合搜索 FAQ：
    - 关键词匹配权重 0.6
    - Jaccard 相似度权重 0.4
    """
    faqs = load_json("faq.json")
    query_tokens = tokenize(query)
    scored = []

    for item in faqs:
        kw_score = keyword_match(query, item.get("keywords", []))
        # 对 question 字段做 Jaccard
        question_tokens = tokenize(item["question"])
        jac_score = jaccard_similarity(query_tokens, question_tokens)
        total_score = kw_score * 0.6 + jac_score * 0.4
        scored.append((total_score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k] if score > 0.05]


def search_products(query: str, top_k: int = 5) -> list[dict]:
    """
    搜索商品：
    - 品类名、标签、商品名匹配
    """
    products = load_json("products.json")
    query_lower = query.lower()
    query_tokens = tokenize(query)
    scored = []

    for item in products:
        # 标签匹配
        tag_hits = sum(1 for t in item.get("tags", []) if t in query_lower)
        # 品类匹配
        cat_hit = 1 if item.get("category", "") in query_lower else 0
        # 商品名匹配
        name_tokens = tokenize(item["name"])
        name_sim = jaccard_similarity(query_tokens, name_tokens)
        # 综合分
        total = tag_hits * 0.2 + cat_hit * 0.3 + name_sim * 0.5
        scored.append((total, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k] if score > 0.05]
