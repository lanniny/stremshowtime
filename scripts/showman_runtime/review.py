from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import json
import re

from .catalog import Product
from .paths import BARRAGE_LOG_DIR, REVIEW_REPORT_DIR


METRIC_FIELDS = (
    "duration_minutes",
    "total_views",
    "peak_online",
    "new_followers",
    "comments",
    "likes",
    "product_clicks",
    "orders",
    "sales_amount",
)

KEYWORD_BANK = {
    "多少钱",
    "价格",
    "保质期",
    "配料",
    "配料表",
    "添加剂",
    "口感",
    "好喝",
    "库存",
    "发货",
    "优惠",
    "下单",
    "小黄车",
    "物流",
    "客服",
    "退货",
    "助农",
    "桑葚",
    "果汁",
    "果酒",
}


@dataclass(slots=True)
class ReviewOutputs:
    markdown: str
    summary: dict[str, object]


def _normalize_message(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _safe_number(value: object) -> int | float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return None


def _format_value(value: int | float | None, decimals: int = 0) -> str:
    if value is None:
        return "数据缺失"
    if isinstance(value, float) and decimals:
        return f"{value:.{decimals}f}"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _rate(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def _format_percent(value: float | None) -> str:
    if value is None:
        return "数据缺失"
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Metrics file must contain a JSON object: {path}")
    return data


def load_barrage_entries(log_path: Path | None = None, log_dir: Path | None = None) -> list[dict[str, object]]:
    if log_path is None:
        directory = log_dir or BARRAGE_LOG_DIR
        candidates = sorted(directory.glob("*-barrage.jsonl"))
        if not candidates:
            return []
        log_path = candidates[-1]

    entries: list[dict[str, object]] = []
    with log_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                entries.append(item)
    return entries


def _build_keyword_bank(products: list[Product]) -> set[str]:
    bank = set(KEYWORD_BANK)
    for product in products:
        bank.add(product.category or "")
        bank.update(key for key in product.faq if key)
        bank.update(
            token
            for token in re.findall(r"[\u4e00-\u9fff]{2,4}", product.name)
            if token
        )
    return {keyword for keyword in bank if keyword}


def _top_keywords(entries: list[dict[str, object]], products: list[Product]) -> list[str]:
    counter: Counter[str] = Counter()
    bank = _build_keyword_bank(products)
    for entry in entries:
        message = _normalize_message(str(entry.get("message", "")))
        if not message:
            continue
        for keyword in bank:
            if keyword in message:
                counter[keyword] += 1

    if not counter:
        for entry in entries:
            message = _normalize_message(str(entry.get("message", "")))
            if 1 < len(message) <= 8:
                counter[message] += 1

    return [item for item, _ in counter.most_common(10)]


def _top_questions(entries: list[dict[str, object]]) -> list[str]:
    counter = Counter(
        _normalize_message(str(entry.get("message", "")))
        for entry in entries
        if entry.get("category") == "A"
    )
    counter.pop("", None)
    return [item for item, _ in counter.most_common(3)]


def _category_counts(entries: list[dict[str, object]]) -> dict[str, int]:
    counts = {category: 0 for category in ("A", "B", "C", "D", "E")}
    for entry in entries:
        category = str(entry.get("category", "")).strip().upper()
        if category in counts:
            counts[category] += 1
    return counts


def _complaints(entries: list[dict[str, object]]) -> list[dict[str, str]]:
    complaints: list[dict[str, str]] = []
    for entry in entries:
        if entry.get("category") != "D":
            continue
        complaints.append(
            {
                "user": str(entry.get("user", "未知用户")),
                "message": str(entry.get("message", "")),
                "status": str(entry.get("alert_status", "未记录")),
            }
        )
    return complaints[:5]


def _suggestions(
    metrics: dict[str, object],
    counts: dict[str, int],
) -> list[dict[str, str]]:
    total_views = _safe_number(metrics.get("total_views"))
    comments = _safe_number(metrics.get("comments"))
    clicks = _safe_number(metrics.get("product_clicks"))
    orders = _safe_number(metrics.get("orders"))
    suggestions: list[dict[str, str]] = []

    comment_rate = _rate(comments, total_views)
    click_rate = _rate(clicks, total_views)
    conversion_rate = _rate(orders, clicks)

    if comment_rate is None or comment_rate < 0.03:
        suggestions.append(
            {
                "title": "增加互动钩子",
                "reason": f"当前互动率为 {_format_percent(comment_rate)}，低于目标参考值 3%。",
                "action": "把“扣1”“想听配料表直接发弹幕”这类互动问题固定插入开场和逼单环节。",
            }
        )

    if click_rate is None or click_rate < 0.05:
        suggestions.append(
            {
                "title": "强化小黄车引导",
                "reason": f"当前点击率为 {_format_percent(click_rate)}，说明口播到商品点击的转化偏弱。",
                "action": "每讲完一个核心卖点后都重复一次明确 CTA，例如“点下方 1 号链接直接拍”。",
            }
        )

    if conversion_rate is None or conversion_rate < 0.03:
        suggestions.append(
            {
                "title": "优化逼单节奏",
                "reason": f"当前点击到下单转化率为 {_format_percent(conversion_rate)}，还没有把心动用户稳稳接住。",
                "action": "在答疑后补一轮价格、库存、下单路径的复述，减少用户从点击到下单的犹豫。",
            }
        )

    if counts["D"] > 0:
        suggestions.append(
            {
                "title": "跟进投诉闭环",
                "reason": f"本场出现 {counts['D']} 条投诉/负面弹幕，说明售后或预期管理存在风险。",
                "action": "复盘投诉原文并补充 FAQ，必要时提前在直播中说明发货、口感或售后边界。",
            }
        )

    if counts["A"] > max(counts["B"], counts["C"], 0):
        suggestions.append(
            {
                "title": "提前覆盖高频问答",
                "reason": "A 类咨询占比最高，说明用户在核心信息上仍有大量未被提前解答的疑问。",
                "action": "把价格、配料、保质期、口感这些问题前置进脚本，减少直播中重复答疑成本。",
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "title": "延续当前节奏",
                "reason": "本场关键指标没有明显短板，可继续稳定执行当前脚本框架。",
                "action": "记录表现最好的开场和促单话术，下一场优先复用并做小幅迭代。",
            }
        )

    return suggestions[:3]


def _find_previous_summary(
    report_dir: Path,
    session_date: str,
    product_name: str,
) -> dict[str, object] | None:
    candidates = sorted(report_dir.glob("*-review.json"))
    same_product: list[Path] = []
    fallback: list[Path] = []
    for path in candidates:
        if path.name.startswith(session_date):
            continue
        fallback.append(path)
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if payload.get("product_name") == product_name:
            same_product.append(path)

    selected = same_product[-1] if same_product else (fallback[-1] if fallback else None)
    if selected is None:
        return None
    return _load_json(selected)


def generate_review_artifacts(
    metrics: dict[str, object],
    barrage_entries: list[dict[str, object]],
    products: list[Product],
    previous_summary: dict[str, object] | None = None,
) -> ReviewOutputs:
    session_date = str(metrics.get("session_date") or date.today().isoformat())
    product_name = str(metrics.get("product_name") or "数据缺失")
    host_name = str(metrics.get("host_name") or "主播")

    counts = _category_counts(barrage_entries)
    top_keywords = _top_keywords(barrage_entries, products)
    top_questions = _top_questions(barrage_entries)
    complaints = _complaints(barrage_entries)
    suggestions = _suggestions(metrics, counts)

    total_views = _safe_number(metrics.get("total_views"))
    new_followers = _safe_number(metrics.get("new_followers"))
    comments = _safe_number(metrics.get("comments"))
    likes = _safe_number(metrics.get("likes"))
    clicks = _safe_number(metrics.get("product_clicks"))
    orders = _safe_number(metrics.get("orders"))
    sales_amount = _safe_number(metrics.get("sales_amount"))

    rates = {
        "follow_rate": _rate(new_followers, total_views),
        "comment_rate": _rate(comments, total_views),
        "click_rate": _rate(clicks, total_views),
        "conversion_rate": _rate(orders, clicks),
        "average_order_value": _rate(sales_amount, orders),
    }

    current_summary = {
        "session_date": session_date,
        "product_name": product_name,
        "host_name": host_name,
        "metrics": {field: metrics.get(field) for field in METRIC_FIELDS},
        "rates": rates,
        "barrage_counts": counts,
        "top_keywords": top_keywords,
        "top_questions": top_questions,
        "complaints": complaints,
        "suggestions": suggestions,
    }

    previous_metrics = (
        previous_summary.get("metrics", {}) if isinstance(previous_summary, dict) else {}
    )

    lines = [
        "# 直播复盘报告",
        "",
        f"> 日期: {session_date}",
        f"> 商品: {product_name}",
        f"> 主播: {host_name}",
        "",
        "---",
        "",
        "## 📊 数据总览",
        "",
        "| 指标 | 数值 | 行业参考 | 评价 |",
        "|------|------|---------|------|",
        f"| 直播时长 | {_format_value(_safe_number(metrics.get('duration_minutes')))}分钟 | — | — |",
        f"| 总观看人次 | {_format_value(total_views)} | — | — |",
        f"| 最高在线人数 | {_format_value(_safe_number(metrics.get('peak_online')))} | — | — |",
        f"| 新增粉丝 | {_format_value(new_followers)} | 转粉率={_format_percent(rates['follow_rate'])} | 高于1%为优 |",
        f"| 评论总数 | {_format_value(comments)} | 互动率={_format_percent(rates['comment_rate'])} | 高于3%为优 |",
        f"| 点赞总数 | {_format_value(likes)} | — | — |",
        f"| 商品点击次数 | {_format_value(clicks)} | 点击率={_format_percent(rates['click_rate'])} | 高于5%为优 |",
        f"| 成交订单数 | {_format_value(orders)} | 转化率={_format_percent(rates['conversion_rate'])} | 高于3%为优 |",
        f"| 预估销售额 | {_format_value(sales_amount, decimals=2)} | 客单价={_format_value(rates['average_order_value'], decimals=2)} | — |",
        "",
        "## 🔍 弹幕分析",
        "",
        "### 高频关键词 TOP10",
    ]

    if top_keywords:
        for index, keyword in enumerate(top_keywords[:10], start=1):
            lines.append(f"{index}. {keyword}")
    else:
        lines.append("1. 数据缺失")

    lines.extend(["", "### 用户最关心的问题 TOP3"])
    if top_questions:
        for index, question in enumerate(top_questions[:3], start=1):
            lines.append(f"{index}. {question}")
    else:
        lines.append("1. 数据缺失")

    total_barrage = sum(counts.values()) or 0
    lines.extend(
        [
            "",
            "### 弹幕类型分布",
            f"- A类（产品咨询）: {_format_percent(_rate(counts['A'], total_barrage))}",
            f"- B类（购买意向）: {_format_percent(_rate(counts['B'], total_barrage))}",
            f"- C类（闲聊互动）: {_format_percent(_rate(counts['C'], total_barrage))}",
            f"- D类（投诉负面）: {_format_percent(_rate(counts['D'], total_barrage))}",
            f"- E类（无关刷屏）: {_format_percent(_rate(counts['E'], total_barrage))}",
            "",
            "### 投诉汇总",
            "| 用户 | 内容 | 处理状态 |",
            "|------|------|---------|",
        ]
    )
    if complaints:
        for complaint in complaints:
            lines.append(
                f"| {complaint['user']} | {complaint['message']} | {complaint['status']} |"
            )
    else:
        lines.append("| — | 本场未记录到投诉弹幕 | — |")

    lines.extend(["", "## 💡 优化建议", ""])
    for index, suggestion in enumerate(suggestions, start=1):
        lines.extend(
            [
                f"{index}. **{suggestion['title']}**",
                f"   - 原因: {suggestion['reason']}",
                f"   - 具体措施: {suggestion['action']}",
            ]
        )

    lines.extend(
        [
            "",
            "## 📈 与上场对比",
            "",
            "| 指标 | 上场 | 本场 | 变化 |",
            "|------|------|------|------|",
        ]
    )

    for label, field in (
        ("总观看", "total_views"),
        ("新增粉丝", "new_followers"),
        ("成交订单", "orders"),
        ("销售额", "sales_amount"),
    ):
        previous_value = _safe_number(previous_metrics.get(field)) if isinstance(previous_metrics, dict) else None
        current_value = _safe_number(metrics.get(field))
        if previous_value is None or current_value is None:
            delta = "数据缺失"
        else:
            diff = current_value - previous_value
            if diff > 0:
                delta = f"+{diff}"
            elif diff < 0:
                delta = str(diff)
            else:
                delta = "持平"
        lines.append(
            f"| {label} | {_format_value(previous_value, decimals=2)} | {_format_value(current_value, decimals=2)} | {delta} |"
        )

    return ReviewOutputs(markdown="\n".join(lines) + "\n", summary=current_summary)


def save_review_outputs(
    outputs: ReviewOutputs,
    report_dir: Path | None = None,
    output_path: Path | None = None,
) -> tuple[Path, Path]:
    directory = report_dir or REVIEW_REPORT_DIR
    directory.mkdir(parents=True, exist_ok=True)

    session_date = str(outputs.summary.get("session_date") or date.today().isoformat())
    markdown_path = output_path or directory / f"{session_date}-review.md"
    json_path = markdown_path.with_suffix(".json")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_path.write_text(outputs.markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(outputs.summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return markdown_path, json_path
