from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import json
import re
import urllib.error
import urllib.request

from .catalog import Product, normalize_text
from .paths import BARRAGE_LOG_DIR


A_KEYWORDS = (
    "多少钱",
    "价格",
    "多少米",
    "配料",
    "配料表",
    "成分",
    "保质期",
    "能放多久",
    "好喝",
    "口感",
    "添加剂",
    "怎么买",
    "下单",
    "链接",
    "小黄车",
    "几度",
    "度数",
)
B_KEYWORDS = (
    "已拍",
    "拍了",
    "拍下",
    "库存",
    "还有吗",
    "还有没有",
    "发货",
    "优惠",
    "便宜点",
    "加急",
    "催单",
)
D_KEYWORDS = (
    "投诉",
    "质量太差",
    "质量差",
    "物流太慢",
    "客服不理",
    "退货",
    "退款",
    "破损",
    "假货",
    "和描述不符",
    "骗人",
    "失望",
    "售后",
)
C_KEYWORDS = (
    "讲得真好",
    "支持",
    "来了",
    "好看",
    "不错",
    "关注了",
    "从",
    "厉害",
    "助农",
)

FAQ_ALIAS_GROUPS: dict[str, tuple[str, ...]] = {
    "price": ("多少钱", "价格", "多少米", "售价", "多少钱一瓶"),
    "shelf_life": ("保质期", "能放多久", "多久过期", "保存多久"),
    "ingredients": ("配料", "配料表", "成分", "原料"),
    "taste": ("好喝", "口感", "酸不酸", "甜不甜", "味道"),
    "additives": ("添加剂", "防腐剂"),
    "buy": ("怎么买", "下单", "链接", "小黄车", "哪里拍"),
    "stock": ("库存", "还有吗", "还有没有", "剩多少"),
    "difference": ("区别", "和其他品牌", "和别家"),
    "alcohol": ("几度", "度数", "酒精度"),
}


@dataclass(slots=True)
class BarrageDecision:
    user: str
    message: str
    product_id: str
    product_name: str
    category: str
    reply: str | None
    tts_text: str | None
    alert_required: bool
    alert_status: str
    timestamp: str


def truncate_for_live(text: str, limit: int = 50) -> str:
    clean = re.sub(r"\s+", "", text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1] + "…"


def looks_like_spam(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if re.search(r"https?://|www\.", stripped):
        return True
    if re.fullmatch(r"[\W_]+", stripped):
        return True
    if len(stripped) >= 6 and len(set(stripped)) <= 2:
        return True
    return False


def classify_barrage_message(text: str) -> str:
    normalized = normalize_text(text)
    if looks_like_spam(text):
        return "E"
    if any(keyword in normalized for keyword in map(normalize_text, D_KEYWORDS)):
        return "D"
    if any(keyword in normalized for keyword in map(normalize_text, B_KEYWORDS)):
        return "B"
    if any(keyword in normalized for keyword in map(normalize_text, A_KEYWORDS)) or "?" in text or "？" in text:
        return "A"
    if any(keyword in normalized for keyword in map(normalize_text, C_KEYWORDS)):
        return "C"
    return "E"


def _purchase_cta(product: Product) -> str:
    return f"点下方{product.primary_link_label}就能拍啦～"


def _detect_alias_group(message: str) -> str | None:
    normalized = normalize_text(message)
    for alias_name, keywords in FAQ_ALIAS_GROUPS.items():
        if any(normalize_text(keyword) in normalized for keyword in keywords):
            return alias_name
    return None


def _answer_product_question(product: Product, message: str) -> str:
    alias_group = _detect_alias_group(message)
    shelf_life = product.spec_value("shelf_life") or "[待确认]"
    cta = _purchase_cta(product)

    if alias_group == "price":
        live_price = product.live_price or "[待确认]"
        unit_price = product.per_unit_price or "[待确认]"
        return truncate_for_live(f"直播间{live_price}，折合{unit_price}，{cta}")

    if alias_group == "shelf_life":
        return truncate_for_live(f"保质期{shelf_life}，常温存放就行，{cta}")

    if alias_group == "ingredients":
        ingredients = product.ingredients or "[待确认]"
        return truncate_for_live(f"配料是{ingredients}，喜欢的直接拍～")

    if alias_group == "taste":
        if product.faq.get("好喝吗"):
            return truncate_for_live(f"{product.faq['好喝吗']} {cta}")
        return truncate_for_live(f"口感会偏柔和顺口，冰一下更好喝，{cta}")

    if alias_group == "additives":
        if product.faq.get("有添加剂吗"):
            return truncate_for_live(f"{product.faq['有添加剂吗']} {cta}")
        return truncate_for_live(f"配料以商品详情页为准，{cta}")

    if alias_group == "buy":
        return truncate_for_live(cta)

    if alias_group == "stock":
        return truncate_for_live("库存还在动态变化，喜欢的现在拍更稳妥～")

    if alias_group == "difference":
        if product.competitors and product.per_unit_price:
            return truncate_for_live(
                f"同类里我们到手{product.per_unit_price}，口感也更柔和～"
            )
        return truncate_for_live(f"核心区别可以看详情页，{cta}")

    if alias_group == "alcohol":
        if product.faq.get("度数多少"):
            return truncate_for_live(f"{product.faq['度数多少']} {cta}")
        return truncate_for_live("具体度数以商品详情页为准，喜欢可直接拍～")

    return truncate_for_live("具体可以咨询客服小姐姐哦～")


def _build_b_category_reply(message: str) -> str:
    normalized = normalize_text(message)
    if "发货" in normalized or "加急" in normalized:
        return truncate_for_live("感谢家人支持！发货时效以店铺通知为准哦～")
    if "库存" in normalized:
        return truncate_for_live("库存还在动态变化，喜欢的家人抓紧拍哦～")
    if "优惠" in normalized:
        return truncate_for_live("直播间已经是当前福利价了，直接拍更划算～")
    return truncate_for_live("感谢家人支持！喜欢的现在拍，别错过直播间福利～")


def _build_c_category_reply(message: str) -> str:
    normalized = normalize_text(message)
    if "助农" in normalized:
        return truncate_for_live("感谢家人支持助农！点点关注，一起把好产品带出去～")
    if "从" in normalized and "过来" in normalized:
        return truncate_for_live("欢迎新来的家人！先点关注，想问什么直接发弹幕～")
    return truncate_for_live("谢谢家人支持！觉得不错的点点关注不迷路哦～")


def _build_d_category_reply() -> str:
    return truncate_for_live("非常抱歉带来不好的体验，这边马上转人工场控跟进～")


def append_barrage_log(entry: BarrageDecision, log_dir: Path | None = None) -> Path:
    target_dir = log_dir or BARRAGE_LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    date_part = entry.timestamp.split("T", 1)[0]
    log_path = target_dir / f"{date_part}-barrage.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return log_path


def send_feishu_alert(
    webhook_url: str,
    user: str,
    message: str,
    product_name: str,
    timestamp: str,
) -> tuple[bool, str]:
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "⚠️ 直播间投诉预警"},
                "template": "red",
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {"tag": "lark_md", "content": f"**用户:** {user}"},
                        },
                        {
                            "is_short": True,
                            "text": {"tag": "lark_md", "content": f"**时间:** {timestamp}"},
                        },
                    ],
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**商品:** {product_name}"},
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**投诉内容:** {message}"},
                },
            ],
        },
    }
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status = getattr(response, "status", 200)
            if 200 <= status < 300:
                return True, f"sent:{status}"
            return False, f"http_{status}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, f"failed:{exc.__class__.__name__}"


def process_single_barrage(
    product: Product,
    user: str,
    message: str,
    webhook_url: str | None = None,
    now: datetime | None = None,
    log_dir: Path | None = None,
    sender: Callable[[str, str, str, str, str], tuple[bool, str]] = send_feishu_alert,
) -> tuple[BarrageDecision, Path]:
    timestamp = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    category = classify_barrage_message(message)

    reply: str | None = None
    tts_text: str | None = None
    alert_required = False
    alert_status = "not_required"

    if category == "A":
        reply = _answer_product_question(product, message)
    elif category == "B":
        reply = _build_b_category_reply(message)
    elif category == "C":
        reply = _build_c_category_reply(message)
    elif category == "D":
        reply = _build_d_category_reply()
        alert_required = True
        if webhook_url:
            sent, status = sender(webhook_url, user, message, product.name, timestamp)
            alert_status = status
            if not sent:
                alert_status = status
        else:
            alert_status = "missing_webhook"

    if reply:
        tts_text = reply

    decision = BarrageDecision(
        user=user,
        message=message,
        product_id=product.id,
        product_name=product.name,
        category=category,
        reply=reply,
        tts_text=tts_text,
        alert_required=alert_required,
        alert_status=alert_status,
        timestamp=timestamp,
    )
    log_path = append_barrage_log(decision, log_dir=log_dir)
    return decision, log_path
