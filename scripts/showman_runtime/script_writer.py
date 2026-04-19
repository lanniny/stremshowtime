from __future__ import annotations

from .catalog import Product


def _value_or_pending(value: str | None) -> str:
    return value or "[待确认]"


def _join_segments(segments: list[str]) -> str:
    return "；".join(segment for segment in segments if segment)


def build_livestream_script(
    product: Product,
    host_name: str = "主播小桑",
    next_live_time: str = "[待确认]",
) -> str:
    pain_points = product.pain_points[:3] or ["想买得放心，又怕口感和品质踩雷"]
    selling_points = product.selling_points[:4] or ["卖点信息待补充"]
    competitor_bits = [
        f"{item.get('name', '竞品')}大约{item.get('price', '[待确认]')}"
        for item in product.competitors[:2]
    ]
    specs_text = _join_segments(
        [
            product.spec_value("volume") or "",
            product.spec_value("packaging") or "",
            product.spec_value("storage") or "",
            product.spec_value("shelf_life") or "",
        ]
    )
    stock_text = f"当前库存参考还有{product.stock}件" if product.stock is not None else "库存信息待运营确认"
    price_bits = _join_segments(
        [
            f"日常价{product.regular_price}" if product.regular_price else "",
            f"直播间到手{product.live_price}" if product.live_price else "",
            f"折合{product.per_unit_price}" if product.per_unit_price else "",
        ]
    )
    link_label = product.primary_link_label
    story_text = product.story or "产品故事待补充"

    section_1 = "\n".join(
        [
            f"{host_name}：家人们晚上好，欢迎来到直播间！今天给大家带来的就是 {product.name}！",
            f"{host_name}：先把福利给大家报一下，{price_bits or '[待确认]'}，想要的家人先点点关注，别等会儿找不到直播间。",
            f"{host_name}：今天我们会把口感、配料、规格和怎么拍都讲清楚，听懂了直接点下方 {link_label} 就行。",
        ]
    )

    pain_lines = [
        f"{host_name}：你是不是也遇到过这种情况，{pain_points[0]}？",
    ]
    for extra_pain in pain_points[1:]:
        pain_lines.append(f"{host_name}：还有不少家人会担心，{extra_pain}。")
    pain_lines.append(
        f"{host_name}：所以我们今天这款 {product.name}，就是冲着把这些顾虑说透、把体验做好来的。"
    )
    section_2 = "\n".join(pain_lines)

    selling_lines = [
        f"{host_name}：先看第一个重点，{selling_points[0]}。",
    ]
    for point in selling_points[1:]:
        selling_lines.append(f"{host_name}：再看一个重点，{point}。")
    if competitor_bits:
        selling_lines.append(
            f"{host_name}：同类产品里，{_join_segments(competitor_bits)}；我们这一款更强调性价比和直播间到手体验。"
        )
    if product.ingredients:
        selling_lines.append(f"{host_name}：配料也给大家直接念，{product.ingredients}。")
    if specs_text:
        selling_lines.append(f"{host_name}：规格信息这边也记一下，{specs_text}。")
    selling_lines.append(f"{host_name}：这款产品背后的故事也很重要，{story_text}")
    section_3 = "\n".join(selling_lines)

    section_4 = "\n".join(
        [
            f"{host_name}：听到这里，想试试的家人扣个 1，我看看有多少宝宝已经心动了。",
            f"{host_name}：今天直播间的核心信息我再重复一次，{price_bits or '[待确认]'}。",
            f"{host_name}：{stock_text}，下手快一点更稳，直接点下方 {link_label} 就能拍。",
            f"{host_name}：如果你还想问配料、保质期、口感，弹幕直接发，我现场给你答。"
        ]
    )

    section_5 = "\n".join(
        [
            f"{host_name}：感谢家人们今晚的陪伴，喜欢 {product.name} 的记得先拍下，再点个关注。",
            f"{host_name}：我们下一场直播时间暂定 {next_live_time}，到时候继续给大家带来更细的产品讲解和福利信息。",
            f"{host_name}：今天的直播就先到这里，家人们晚点见！"
        ]
    )

    return "\n\n".join(
        [
            f"# {product.name} 直播口播脚本",
            f"## 环节① 开场预热\n{section_1}",
            f"## 环节② 痛点挖掘\n{section_2}",
            f"## 环节③ 产品展示与卖点讲解\n{section_3}",
            f"## 环节④ 互动答疑与逼单\n{section_4}",
            f"## 环节⑤ 下播预告\n{section_5}",
        ]
    )
