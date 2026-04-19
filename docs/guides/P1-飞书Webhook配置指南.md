# P1 — 飞书 Webhook 投诉预警配置

> 预计耗时: 10分钟

## Step 1: 创建飞书群机器人

1. 打开飞书，进入或创建一个「直播场控群」
2. 点击群设置（右上角三个点）→ 群机器人 → 添加机器人
3. 选择「自定义机器人」
4. 机器人名称填: `直播投诉预警`
5. 点击完成，**复制 Webhook 地址**

Webhook 地址格式类似:
```
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Step 2: 配置到服务器

拿到 Webhook 地址后，告诉我（浮浮酱），我会帮你配置到 OpenClaw 中。

或者自行执行:
```bash
ssh root@154.219.123.90 -p 52714
echo 'export FEISHU_WEBHOOK_URL=你的webhook地址' >> ~/.bashrc
source ~/.bashrc
```

## Step 3: 测试通知

配置完成后，可以用 curl 测试:
```bash
curl -X POST "你的webhook地址" \
  -H "Content-Type: application/json" \
  -d '{
    "msg_type": "interactive",
    "card": {
      "header": {
        "title": { "tag": "plain_text", "content": "⚠️ 直播间投诉预警" },
        "template": "red"
      },
      "elements": [
        {
          "tag": "div",
          "fields": [
            { "is_short": true, "text": { "tag": "lark_md", "content": "**用户:** 测试用户" } },
            { "is_short": true, "text": { "tag": "lark_md", "content": "**时间:** 2026-04-15 20:30" } }
          ]
        },
        {
          "tag": "div",
          "text": { "tag": "lark_md", "content": "**投诉内容:** 这是一条测试投诉消息" }
        },
        {
          "tag": "div",
          "text": { "tag": "lark_md", "content": "**建议处理:** 尽快联系该用户，避免二次投诉升级" }
        }
      ]
    }
  }'
```

如果飞书群收到了红色卡片消息，说明配置成功！
