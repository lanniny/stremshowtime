#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import html
import sys


ROOT = Path(__file__).resolve().parent.parent
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from showman_runtime.barrage import process_single_barrage
from showman_runtime.catalog import load_products, match_product
from showman_runtime.review import generate_review_artifacts, save_review_outputs
from showman_runtime.script_writer import build_livestream_script


DEMO_PRODUCT = "一川桑语 NFC60%桑葚复合果汁饮料"
DEMO_HOST = "主播小桑"
DEMO_NEXT_LIVE = "本周五晚上 8 点"
DEMO_INPUT = ROOT / "skills" / "barrage-responder" / "references" / "full-demo-input.jsonl"
DEMO_METRICS_TEMPLATE = (
    ROOT / "skills" / "livestream-review" / "references" / "session-metrics-template.json"
)
DEMO_VIDEO = ROOT / "讲解视频.mp4"
DEMO_POSTER = ROOT / "static_speaking.png"


def load_demo_inputs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with DEMO_INPUT.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append({str(k): str(v) for k, v in item.items()})
    return rows


def load_demo_metrics(session_date: str) -> dict[str, object]:
    with DEMO_METRICS_TEMPLATE.open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    if not isinstance(metrics, dict):
        raise ValueError("Demo metrics template must be a JSON object.")
    metrics["session_date"] = session_date
    metrics["host_name"] = DEMO_HOST
    metrics["product_name"] = DEMO_PRODUCT
    return metrics


def render_summary(
    output_dir: Path,
    script_path: Path,
    barrage_output_path: Path,
    alert_path: Path,
    report_markdown_path: Path,
    report_json_path: Path,
    barrage_entries: list[dict[str, object]],
) -> str:
    lines = [
        "# Showman 完整演示摘要",
        "",
        f"- 演示目录: `{output_dir}`",
        f"- 直播脚本: `{script_path.name}`",
        f"- 弹幕处理结果: `{barrage_output_path.name}`",
        f"- 告警记录: `{alert_path.name}`",
        f"- 复盘报告: `{report_markdown_path.name}`",
        f"- 复盘摘要 JSON: `{report_json_path.name}`",
        "",
        "## 演示流程",
        "",
        "1. 开播前：根据商品主数据生成五段式直播脚本。",
        "2. 开播中：逐条处理实时弹幕，输出分类、回复、TTS 文本和投诉告警状态。",
        "3. 下播后：读取会话指标与弹幕日志，生成结构化复盘报告。",
        "",
        "## 本次弹幕结果",
        "",
        "| 用户 | 分类 | 回复 |",
        "|------|------|------|",
    ]
    for entry in barrage_entries:
        reply = str(entry.get("reply") or "（忽略）")
        lines.append(f"| {entry['user']} | {entry['category']} | {reply} |")

    return "\n".join(lines) + "\n"


def render_visual_demo_html(
    output_dir: Path,
    script_text: str,
    barrage_entries: list[dict[str, object]],
    alert_events: list[dict[str, str]],
    review_markdown: str,
) -> str:
    video_rel = Path("../../../讲解视频.mp4").as_posix()
    poster_rel = Path("../../../static_speaking.png").as_posix()
    script_preview = "\n".join(script_text.splitlines()[:18])
    review_preview = "\n".join(review_markdown.splitlines()[:26])
    barrage_cards = "\n".join(
        f"""
        <div class="card barrage-card category-{entry['category']}">
          <div class="meta">{html.escape(str(entry['user']))} · {html.escape(str(entry['category']))}</div>
          <div class="message">{html.escape(str(entry['message']))}</div>
          <div class="reply">{html.escape(str(entry.get('reply') or '忽略'))}</div>
        </div>
        """
        for entry in barrage_entries
    )
    alert_html = "\n".join(
        f"<li>{html.escape(event['timestamp'])} · {html.escape(event['user'])} · {html.escape(event['status'])}</li>"
        for event in alert_events
    ) or "<li>本次无投诉告警</li>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Showman 数字人完整演示</title>
  <style>
    :root {{
      --bg: #f4efe7;
      --panel: rgba(255,255,255,0.84);
      --line: rgba(44, 35, 23, 0.14);
      --ink: #2d2418;
      --muted: #6b5c4a;
      --accent: #c55a2f;
      --accent-soft: #f2d4c3;
      --good: #2f7d5c;
      --warn: #9b3d25;
      --shadow: 0 18px 50px rgba(69, 48, 26, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(197,90,47,.16), transparent 30%),
        radial-gradient(circle at bottom right, rgba(47,125,92,.12), transparent 26%),
        linear-gradient(135deg, #f7f3ed, #efe6d8);
    }}
    .shell {{
      max-width: 1460px;
      margin: 0 auto;
      padding: 28px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(360px, 1.08fr) minmax(320px, 0.92fr);
      gap: 22px;
      align-items: stretch;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
    }}
    .video-panel {{
      padding: 18px;
      position: relative;
      overflow: hidden;
    }}
    .video-panel::before {{
      content: "";
      position: absolute;
      inset: auto -60px -70px auto;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, rgba(197,90,47,.25), transparent 68%);
      pointer-events: none;
    }}
    .video-wrap {{
      position: relative;
      border-radius: 20px;
      overflow: hidden;
      background: #120f0c;
      min-height: 720px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    video {{
      width: 100%;
      max-height: 78vh;
      object-fit: contain;
      background: #120f0c;
    }}
    .badge-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}
    .badge {{
      border-radius: 999px;
      padding: 8px 14px;
      background: rgba(255,255,255,.72);
      border: 1px solid var(--line);
      font-size: 13px;
      color: var(--muted);
    }}
    .side {{
      display: grid;
      gap: 18px;
      align-content: start;
    }}
    .section {{
      padding: 20px 22px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 34px;
      line-height: 1.1;
      letter-spacing: .02em;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .card {{
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.72);
      padding: 14px;
    }}
    .barrage-card {{
      margin-bottom: 10px;
    }}
    .category-A {{ border-left: 6px solid #3666c9; }}
    .category-B {{ border-left: 6px solid #2f7d5c; }}
    .category-C {{ border-left: 6px solid #b4881d; }}
    .category-D {{ border-left: 6px solid #bb4430; }}
    .category-E {{ border-left: 6px solid #6f6f6f; }}
    .meta {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .message {{
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .reply {{
      color: var(--warn);
      line-height: 1.6;
      font-size: 14px;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.68;
      color: #433627;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.7;
    }}
    .footer-note {{
      margin-top: 18px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 1120px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
      .video-wrap {{
        min-height: 480px;
      }}
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <section class="panel video-panel">
        <h1>数字人完整演示</h1>
        <p class="sub">这一页把数字人画面、直播脚本、弹幕处理和复盘结果放到一个可视化界面里。当前使用仓库内现有视频素材做本地演示，真实上线时再替换为 AIGCPanel / 硅基智能的实时数字人流。</p>
        <div class="video-wrap">
          <video controls autoplay muted loop playsinline poster="{poster_rel}">
            <source src="{video_rel}" type="video/mp4" />
            你的浏览器暂不支持视频预览，可以用同目录下的静态图查看数字人状态。
          </video>
        </div>
        <div class="badge-bar">
          <span class="badge">商品：{html.escape(DEMO_PRODUCT)}</span>
          <span class="badge">主播：{html.escape(DEMO_HOST)}</span>
          <span class="badge">模式：本地完整演示</span>
        </div>
      </section>

      <aside class="side">
        <section class="panel section">
          <h2>直播脚本摘要</h2>
          <pre>{html.escape(script_preview)}</pre>
        </section>

        <section class="panel section">
          <h2>弹幕处理结果</h2>
          <div class="grid">
            <div>{barrage_cards}</div>
            <div>
              <div class="card">
                <div class="meta">投诉告警演示</div>
                <ul>{alert_html}</ul>
              </div>
            </div>
          </div>
        </section>

        <section class="panel section">
          <h2>复盘报告摘要</h2>
          <pre>{html.escape(review_preview)}</pre>
          <p class="footer-note">真实外部接入时，这里对应的就是下播后自动生成的复盘结果。</p>
        </section>
      </aside>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    products = load_products()
    product = match_product(products, DEMO_PRODUCT)

    timestamp = datetime.now().astimezone()
    session_date = timestamp.date().isoformat()
    output_dir = ROOT / "data" / "demo-output" / f"{session_date}-full-demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: script generation
    script_text = build_livestream_script(
        product=product,
        host_name=DEMO_HOST,
        next_live_time=DEMO_NEXT_LIVE,
    )
    script_path = output_dir / "01-livestream-script.md"
    script_path.write_text(script_text + "\n", encoding="utf-8")

    # Phase 2: barrage handling with demo alert capture
    barrage_rows = load_demo_inputs()
    barrage_output_path = output_dir / "02-barrage-results.jsonl"
    barrage_log_dir = output_dir / "barrage-logs"
    alert_path = output_dir / "03-alerts.jsonl"
    alert_events: list[dict[str, str]] = []
    results: list[dict[str, object]] = []

    def demo_sender(webhook_url: str, user: str, message: str, product_name: str, alert_time: str) -> tuple[bool, str]:
        event = {
            "user": user,
            "message": message,
            "product_name": product_name,
            "timestamp": alert_time,
            "status": "demo_alert_sent",
        }
        alert_events.append(event)
        return True, "demo_alert_sent"

    for row in barrage_rows:
        decision, log_path = process_single_barrage(
            product=product,
            user=row.get("user", "匿名用户"),
            message=row.get("message", ""),
            webhook_url="demo://feishu-webhook",
            now=timestamp,
            log_dir=barrage_log_dir,
            sender=demo_sender,
        )
        payload = asdict(decision)
        payload["log_path"] = str(log_path.relative_to(ROOT))
        results.append(payload)

    barrage_output_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
        encoding="utf-8",
    )
    alert_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in alert_events) + "\n",
        encoding="utf-8",
    )

    # Phase 3: review generation
    metrics = load_demo_metrics(session_date)
    metrics["comments"] = len(results)
    metrics["likes"] = max(int(metrics.get("likes", 0)), len(results) * 150)
    outputs = generate_review_artifacts(
        metrics=metrics,
        barrage_entries=results,
        products=products,
        previous_summary=None,
    )
    report_markdown_path, report_json_path = save_review_outputs(
        outputs,
        output_path=output_dir / "04-review-report.md",
    )

    summary_path = output_dir / "00-demo-summary.md"
    summary_path.write_text(
        render_summary(
            output_dir=output_dir,
            script_path=script_path,
            barrage_output_path=barrage_output_path,
            alert_path=alert_path,
            report_markdown_path=report_markdown_path,
            report_json_path=report_json_path,
            barrage_entries=results,
        ),
        encoding="utf-8",
    )

    visual_demo_path = output_dir / "05-digital-human-demo.html"
    visual_demo_path.write_text(
        render_visual_demo_html(
            output_dir=output_dir,
            script_text=script_text,
            barrage_entries=results,
            alert_events=alert_events,
            review_markdown=outputs.markdown,
        ),
        encoding="utf-8",
    )

    print(f"完整演示已生成：{output_dir}")
    print(f"- 摘要: {summary_path}")
    print(f"- 直播脚本: {script_path}")
    print(f"- 弹幕结果: {barrage_output_path}")
    print(f"- 告警结果: {alert_path}")
    print(f"- 复盘报告: {report_markdown_path}")
    print(f"- 数字人可视化页: {visual_demo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
