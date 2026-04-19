# stremshowtime

一个面向“本地数字人直播间联调”的仓库。

你可以用它完成三类事情：

1. 在本机快速跑起一个“像直播间”的控制台页面
2. 演示脚本生成、弹幕处理、人工回复、手动播报、复盘报告
3. 逐步接入真实边界：AIGCPanel、飞书 Webhook、BarrageGrab / 外部弹幕源

如果你想要的是：

- 先看一个能跑的直播间演示
- 再一步步接到真实数字人
- 最后能处理弹幕、播报指定内容、触发投诉告警

那这份 README 就是按这个顺序写的。

## 你最终会得到什么

跑起来之后，浏览器里会有一个本地页面，默认地址是：

```text
http://127.0.0.1:8765
```

页面里可以看到：

1. 数字人舞台区
2. 当前商品直播脚本
3. 实时弹幕流
4. 当前播报内容
5. 人工回复弹幕入口
6. AIGCPanel / 飞书 / 弹幕源状态
7. 直播复盘生成入口

## 先看操作总流程

如果你想一眼看明白全流程，顺序就是这 8 步：

1. 准备 Python 运行环境
2. 复制本地配置文件
3. 启动本地 bridge
4. 先跑“纯本地演示模式”
5. 确认手动播报、人工回复弹幕都正常
6. 配置飞书 Webhook
7. 配置并验证 AIGCPanel 真人音色链路
8. 接入真实弹幕源

你可以先只做前 4 步，5 分钟内看到页面。

## 一、环境准备

### 1. 操作系统

优先按 Windows + PowerShell 使用。

这个仓库里很多示例命令默认就是 Windows 写法。

### 2. Python

建议 Python `3.10+`。

检查是否可用：

```powershell
python --version
```

如果系统里没有 `python` 命令，请先安装 Python，再重新打开 PowerShell。

### 3. 可选依赖

如果你要接 BarrageGrab / WebSocket 弹幕源，需要安装：

```powershell
pip install websocket-client
```

如果你只看本地演示，不接真实弹幕源，这一步可以先跳过。

### 4. AIGCPanel

如果你要真人音色、真实数字人链路，需要先安装 AIGCPanel。

安装与制作流程可以看：

- 官方网站: [https://aigcpanel.com/](https://aigcpanel.com/)
- 官方下载页: [https://aigcpanel.com/zh/download](https://aigcpanel.com/zh/download)
- 官方 Windows 安装教程: [https://aigcpanel.com/zh/document/69](https://aigcpanel.com/zh/document/69)
- 官方声音克隆步骤: [https://aigcpanel.com/zh/document/8](https://aigcpanel.com/zh/document/8)
- 官方声音合成步骤: [https://aigcpanel.com/zh/document/9](https://aigcpanel.com/zh/document/9)
- 官方视频合成步骤: [https://aigcpanel.com/zh/document/10](https://aigcpanel.com/zh/document/10)
- 官方数字人直播说明: [https://aigcpanel.com/zh/document/32](https://aigcpanel.com/zh/document/32)
- 官方数字人直播推流配置: [https://aigcpanel.com/zh/document/40](https://aigcpanel.com/zh/document/40)
- 官方开源仓库: [https://github.com/modstart-lib/aigcpanel](https://github.com/modstart-lib/aigcpanel)
- [P0-AIGCPanel安装与数字人制作.md](docs/guides/P0-AIGCPanel安装与数字人制作.md)

注意：

如果你是刚重装 AIGCPanel，或者换了电脑，原来的音色克隆和数字人模板不一定还在。

想得到“原来的真人声音效果”，你至少要在 AIGCPanel 里确认这 3 样东西已经存在：

1. 可用的 TTS / 声音克隆模型
2. 已完成的声音克隆记录
3. 可用的数字人视频模板

缺任意一项，页面虽然还能跑，但不会真的回放你原来的真人音色。

## 二、先用 5 分钟跑起来

这是最短路径，不需要先接飞书，也不需要先接 AIGCPanel。

### 第 1 步：进入项目目录

```powershell
cd stremshowtime
```

### 第 2 步：复制本地配置文件

```powershell
Copy-Item config\live-bridge.example.json config\live-bridge.json
```

说明：

- `config/live-bridge.example.json` 是模板
- `config/live-bridge.json` 是你本机实际使用的配置
- `config/live-bridge.json` 已被 `.gitignore` 忽略，不会提交到仓库

### 第 3 步：直接启动完整演示

```powershell
python scripts/live_bridge.py --load-demo
```

你会看到类似输出：

```text
Live studio bridge is running at http://127.0.0.1:8765
Open the URL above in a browser to view the livestream console.
```

### 第 4 步：打开浏览器

访问：

```text
http://127.0.0.1:8765
```

这时你应该已经能看到：

1. 控制台页面能打开
2. 商品脚本已经生成
3. 页面右侧能看到演示弹幕
4. 当前播报内容会变化

如果你只做到这里，说明项目已经“跑起来了”。

## 三、认识页面里每个区域是干什么的

打开页面后，建议你按这个顺序看：

### 1. 顶部状态区

这里会显示：

- 当前直播间标题
- 当前商品
- 当前主播
- 当前会话状态

### 2. 中间舞台区

这里是“数字人舞台”。

默认情况下：

- 没接 AIGCPanel 时，它会显示本地素材和播报状态
- 接上 AIGCPanel 且有真实返回媒体时，会优先播放真实音频或视频

### 3. 右侧弹幕流

这里会显示：

- 进入 bridge 的弹幕
- 每条弹幕的分类
- 生成的回复
- “引用回复”按钮

### 4. 控制表单区

这里有 4 个最重要的表单：

1. 重建本场直播
2. 手动注入弹幕
3. 指定播报内容
4. 人工回复弹幕

### 5. 接入联调区

这里有 2 组核心动作：

1. AIGCPanel：`Ping`、`提交当前播报`、`查询任务`、`取消任务`
2. 飞书 / 复盘：`发送飞书测试`、`生成本场复盘`

## 四、先把“手动播报”和“人工回复”玩明白

这一步非常重要，因为它是后面接真实链路前最容易自测的部分。

### 1. 指定播报内容

在“指定播报内容”表单里输入：

- 播报人：例如 `主播小桑`
- 播报内容：例如 `欢迎来到直播间，今天我们主推桑葚汁`

点击：

```text
立即播报这段话
```

你应该能看到：

1. “当前播报”区域文字更新
2. 回复队列里新增一条手动播报
3. 页面舞台进入“正在播报”的视觉状态

### 2. 手动注入弹幕

在“手动注入弹幕”里输入：

- 用户昵称：例如 `新观众`
- 弹幕内容：例如 `多少钱？`

点击：

```text
发送到桥
```

你应该能看到：

1. 右侧弹幕流新增一条弹幕
2. 系统根据分类规则生成回复
3. 当前播报内容切到这条回复

### 3. 人工回复弹幕

你可以有两种方式回复：

1. 直接在“人工回复弹幕”表单里自己填
2. 点击右侧弹幕卡片里的“引用回复”，自动带入用户和原始弹幕

然后填写：

- 回复分类：默认 `MANUAL`
- 回复内容：例如 `库存还在，现在拍 1 号链接就可以`

点击：

```text
回复这条弹幕
```

你应该能看到：

1. 当前播报切到你的人工回复
2. 弹幕流里出现一条人工回复记录
3. 回复队列新增一条记录

如果这三步都正常，说明本地核心链路已经通了。

## 五、如何正常启动和停止本地服务

### 正常启动

最常用是这两个命令：

```powershell
python scripts/live_bridge.py
```

或者：

```powershell
python scripts/live_bridge.py --load-demo
```

### 正常停止

如果窗口就在前台，直接按：

```text
Ctrl + C
```

### 如果端口被占用

查看谁占了 `8765`：

```powershell
netstat -ano -p TCP | findstr :8765
```

记下最后一列的 PID，然后结束进程：

```powershell
Stop-Process -Id <PID> -Force
```

## 六、配置文件应该怎么改

你的本机实际配置文件是：

```text
config/live-bridge.json
```

建议第一次只改最关键的 4 组字段：

### 1. server

```json
"server": {
  "host": "127.0.0.1",
  "port": 8765,
  "auto_push_replies": false,
  "poll_interval_ms": 1500
}
```

说明：

- `host` / `port` 决定页面地址
- `auto_push_replies`
  - `false`：适合先本地联调，不自动把每条回复推给 AIGCPanel
  - `true`：适合 AIGCPanel 已经联通并稳定后开启

### 2. session

```json
"session": {
  "room_title": "一川桑语数字人直播间",
  "product": "一川桑语 NFC60%桑葚复合果汁饮料",
  "host_name": "主播小桑",
  "next_live_time": "本周五晚上 8 点"
}
```

说明：

- 页面初始标题、主播名、商品、预告时间都从这里来

### 3. integrations.feishu

```json
"feishu": {
  "webhook_env": "FEISHU_WEBHOOK_URL",
  "webhook_url": ""
}
```

说明：

- 二选一即可
- 要么直接把 `webhook_url` 写进去
- 要么设置系统环境变量 `FEISHU_WEBHOOK_URL`

### 4. integrations.aigcpanel

```json
"aigcpanel": {
  "enabled": false,
  "base_url": "http://127.0.0.1:8888",
  "probeBaseUrls": [
    "http://127.0.0.1:8888",
    "http://127.0.0.1:3030"
  ]
}
```

第一次建议：

1. 先保持 `enabled: false`
2. 本地演示跑通之后，再改成 `true`
3. 然后去页面点 `Ping`

如果 `Ping` 成功，再继续配 `entry` / `entryArgs` / `resultRoots`

## 七、接飞书 Webhook

### 方式 1：直接写配置

把你的 Webhook 地址填到：

```json
"webhook_url": "https://open.feishu.cn/..."
```

### 方式 2：用环境变量

PowerShell 临时设置：

```powershell
$env:FEISHU_WEBHOOK_URL = "https://open.feishu.cn/..."
```

### 验证方法

1. 启动页面
2. 点击“发送飞书测试”
3. 看飞书群里是否收到测试消息

### 投诉弹幕联动验证

然后再手动输入一条投诉类弹幕，例如：

```text
质量太差了
```

如果分类进了 D 类，它会触发同一条飞书告警链路。

## 八、接 AIGCPanel 真人音色链路

这是最关键也最容易卡住的一段，我按最稳的顺序写。

### 先记住一个原则

这个仓库只是“接 AIGCPanel”的桥，不负责替你在 AIGCPanel 里自动创建音色、模型和数字人。

所以顺序一定是：

1. 先在 AIGCPanel 软件里把声音、模板、视频都做出来
2. 再回到这个仓库接 `Ping` / `提交当前播报` / `查询任务`

如果 AIGCPanel 软件里手工都还不能正常合成，那仓库这边也不可能自动成功。

### 0. 小白先看这组官方入口

建议把下面这些页面先收藏，做一步看一步：

1. 下载页: [https://aigcpanel.com/zh/download](https://aigcpanel.com/zh/download)
2. Windows 安装教程: [https://aigcpanel.com/zh/document/69](https://aigcpanel.com/zh/document/69)
3. 声音克隆步骤: [https://aigcpanel.com/zh/document/8](https://aigcpanel.com/zh/document/8)
4. 声音合成步骤: [https://aigcpanel.com/zh/document/9](https://aigcpanel.com/zh/document/9)
5. 视频合成步骤: [https://aigcpanel.com/zh/document/10](https://aigcpanel.com/zh/document/10)
6. 数字人直播说明: [https://aigcpanel.com/zh/document/32](https://aigcpanel.com/zh/document/32)
7. 直播推流配置: [https://aigcpanel.com/zh/document/40](https://aigcpanel.com/zh/document/40)

### 第 1 步：先在 AIGCPanel 里准备资产

在 AIGCPanel 里确认：

1. 模型已经下载完成，并且是绿色可用状态
2. 已经完成至少一个声音克隆
3. 已经准备好一个数字人模板或视频模板

如果没有这些资产，bridge 就算写得再对，也拿不到真人结果。

### 第 2 步：你在 AIGCPanel 软件里具体要怎么点

下面这段就是给第一次接触的人照着点的。

#### 2.1 安装并打开软件

1. 打开下载页: [https://aigcpanel.com/zh/download](https://aigcpanel.com/zh/download)
2. Windows 电脑一般选 `64位芯片`
3. 双击安装包，一路点“下一步”
4. 安装完成后，桌面会出现 AIGCPanel 图标
5. 第一次启动时，先不要急着接仓库，先把软件本体跑通

#### 2.2 先把模型下好并启动

你进入 AIGCPanel 后，先做这一件事：

1. 进入“模型管理”或资源下载页
2. 下载至少一个可用的声音模型
3. 如果你要做视频，再下载一个可用的视频/口型模型
4. 下载完成后点击“启动”
5. 看到模型状态变成绿色，再继续下一步

对小白来说，这一步最重要的判断标准只有一句：

```text
模型必须是绿色运行状态
```

如果还是灰色、红色、启动失败，就先不要继续后面的克隆和视频合成。

#### 2.3 先做一次声音克隆

参考官方步骤: [https://aigcpanel.com/zh/document/8](https://aigcpanel.com/zh/document/8)

具体动作可以照着做：

1. 先准备一段 `5-10 秒` 的干净人声
2. 进入 AIGCPanel 的“我的音色”或“声音克隆”相关页面
3. 点击“添加音色”或上传参考音频
4. 选择刚才已经启动为绿色的声音模型
5. 选择你刚上传的音色
6. 输入一段测试文案，第一次建议控制在 `30-100` 字以内
7. 点击“开始克隆”或“提交”
8. 等待生成完成后，直接试听结果

做到这里，你至少应该得到一个能播放的克隆结果。

如果这里都还没有试听成功，就不要急着回仓库接桥。

#### 2.4 再做一次普通声音合成

参考官方步骤: [https://aigcpanel.com/zh/document/9](https://aigcpanel.com/zh/document/9)

建议你再做一次普通 TTS 合成，目的是确认“模型能说话”，不是只验证克隆页面。

顺序一般是：

1. 进入“声音合成”
2. 选择已经绿色运行的声音模型
3. 选择一个可用音色
4. 输入一段短文案
5. 点击“开始合成”
6. 等待生成完成后试听

只要这一步也能正常出音频，后面接 bridge 的成功率会高很多。

#### 2.5 上传数字人形象并做一次视频合成

参考官方步骤: [https://aigcpanel.com/zh/document/10](https://aigcpanel.com/zh/document/10)

你可以按这个顺序做：

1. 先准备一段主播本人正脸、稳定、光线均匀的视频
2. 进入“数字人形象管理”或类似入口，上传形象视频
3. 再进入“视频合成”
4. 选择刚刚上传的数字人形象
5. 选择绿色运行的视频模型
6. 选择声音来源
7. 输入一段测试文案，或者选择刚才生成的音频
8. 点击“开始生成视频”
9. 等待生成完成后，检查口型、音视频同步、人物画面是否正常

做到这里，你才算真正有了“可被仓库接入”的本地数字人资产。

#### 2.6 如果你的目标是像直播间一样持续播报

参考官方说明:

1. 数字人直播说明: [https://aigcpanel.com/zh/document/32](https://aigcpanel.com/zh/document/32)
2. 直播推流配置: [https://aigcpanel.com/zh/document/40](https://aigcpanel.com/zh/document/40)

你可以先不急着推流到抖音。

先确认下面这 4 个结果已经在 AIGCPanel 软件里发生过：

1. 至少一个声音模型能正常启动
2. 至少一个声音克隆结果能试听
3. 至少一个视频合成结果能播放
4. 你能在软件里找到这些结果文件或任务记录

### 第 3 步：先让 AIGCPanel 自己单独能工作

先不要急着接仓库。

你要先在 AIGCPanel 软件里自己验证：

1. 输入一段测试文案
2. 能正常合成声音
3. 能正常合成数字人视频

只有这一步成功，后面的 bridge 联调才有意义。

### 第 4 步：回到仓库前，你最好记下这 4 类信息

1. AIGCPanel launcher 的实际端口
2. AIGCPanel 输出音频或视频的本地目录
3. 你机器上实际存在的工作流入口路径
4. 你准备使用的主播名、商品名、默认播报文案

这些信息之后都会映射到 `config/live-bridge.json`。

### 第 5 步：打开本地配置

编辑：

```text
config/live-bridge.json
```

把 `aigcpanel.enabled` 改成：

```json
"enabled": true
```

### 第 6 步：确认 launcher 地址

默认优先探测：

1. `http://127.0.0.1:8888`
2. `http://127.0.0.1:3030`

如果你的 AIGCPanel 不是这两个端口，就手动改：

```json
"base_url": "http://127.0.0.1:你的端口"
```

### 第 7 步：填写 entry / entryArgs

如果你的 AIGCPanel 远端 `/config` 已经能返回 launcher 合同，可以先不手填。

如果不会自动返回，你就需要自己填本机真实工作流入口，例如：

```json
"entry": "python",
"entryArgs": [
  "C:/path/to/aigcpanel/workflows/live_avatar.py",
  "--text",
  "${TEXT}",
  "--host",
  "${HOST_NAME}",
  "--product",
  "${PRODUCT_NAME}"
]
```

这里一定要注意：

- 示例里的 `C:/path/to/aigcpanel/...` 只是模板
- 你必须改成你机器上真实存在的工作流路径

### 第 8 步：配置结果目录

如果 AIGCPanel 会把音频、视频输出到本地文件，推荐把这些目录写进：

```json
"resultRoots": [
  "C:/path/to/aigcpanel/outputs",
  "C:/path/to/aigcpanel/cache"
]
```

这样 bridge 才能安全地把本地结果映射成页面可回放地址。

### 第 9 步：先做 Ping

启动 bridge 后，进入页面，先点：

```text
Ping
```

你希望看到的结果是：

1. `ok: true`
2. 不是 `URLError`
3. 状态区域里 AIGCPanel 不再显示连接失败

### 第 10 步：手动提交当前播报

先在页面里生成一条当前播报，再点：

```text
提交当前播报
```

然后再点：

```text
查询任务
```

你要观察 3 件事：

1. 有没有返回 `token`
2. 有没有查询到任务状态
3. 有没有真实音频 / 视频结果回到页面

### 第 11 步：再考虑开启 auto_push_replies

只有在以下条件都成立时，才建议把 `auto_push_replies` 改成 `true`：

1. `Ping` 稳定成功
2. `提交当前播报` 稳定成功
3. `查询任务` 能稳定拿到真实结果

否则先保持 `false`，继续手动联调更稳。

## 九、接真实弹幕源

仓库里已经有一个 relay 脚本：

```text
scripts/connect_douyin_barragegrab.py
```

### 第 1 步：确保安装依赖

```powershell
pip install websocket-client
```

### 第 2 步：先启动本地 bridge

```powershell
python scripts/live_bridge.py
```

### 第 3 步：再启动你的 BarrageGrab 或其他兼容源

确保它的 WebSocket 地址能连上。

### 第 4 步：启动 relay

```powershell
python scripts/connect_douyin_barragegrab.py --bridge-url http://127.0.0.1:8765/api/barrage --websocket-url ws://127.0.0.1:8888
```

### 第 5 步：观察页面

如果成功，你应该能看到：

1. 页面右侧弹幕流开始滚动
2. 弹幕源状态从等待变成已连接 / receiving
3. 新弹幕会自动进入分类和回复流程

## 十、推荐你实际照着走一遍的“完整流程”

如果你想从零做到全链路，建议按这个清单执行：

### 阶段 A：先只看本地效果

1. `Copy-Item config\live-bridge.example.json config\live-bridge.json`
2. `python scripts/live_bridge.py --load-demo`
3. 打开 `http://127.0.0.1:8765`
4. 确认页面能开、脚本能看、弹幕能显示

### 阶段 B：确认人工干预链路

1. 手动输入一条播报内容
2. 手动注入一条普通弹幕
3. 人工回复一条弹幕
4. 手动输入一条投诉弹幕

### 阶段 C：接飞书

1. 配置 `FEISHU_WEBHOOK_URL`
2. 点击“发送飞书测试”
3. 再发一条投诉弹幕

### 阶段 D：接 AIGCPanel

1. 在 AIGCPanel 里确认模型、音色、模板都准备好
2. 把 `aigcpanel.enabled` 改成 `true`
3. 配好真实 `base_url`
4. 配好真实 `entry` / `entryArgs`
5. 页面先点 `Ping`
6. 再点 `提交当前播报`
7. 再点 `查询任务`
8. 确认页面开始使用真实返回媒体

### 阶段 E：接真实弹幕源

1. 启动 bridge
2. 启动 BarrageGrab
3. 启动 relay 脚本
4. 观察真实弹幕是否进入页面

### 阶段 F：生成复盘

1. 让页面里先有一些弹幕和回复
2. 点击“生成本场复盘”
3. 去 `data/review-reports/` 看输出

## 十一、常用命令汇总

### 启动本地演示

```powershell
python scripts/live_bridge.py --load-demo
```

### 正常启动本地 bridge

```powershell
python scripts/live_bridge.py
```

### 改端口启动

```powershell
python scripts/live_bridge.py --port 9000
```

### 接入 BarrageGrab relay

```powershell
python scripts/connect_douyin_barragegrab.py --bridge-url http://127.0.0.1:8765/api/barrage --websocket-url ws://127.0.0.1:8888
```

### 跑测试

```powershell
python -m unittest discover -s tests
```

## 十二、常见问题排查

### 1. 页面打不开

先检查服务是否启动成功。

看终端里有没有：

```text
Live studio bridge is running at http://127.0.0.1:8765
```

如果没有，说明服务没正常起来。

### 2. `8765` 端口被占用

执行：

```powershell
netstat -ano -p TCP | findstr :8765
```

然后：

```powershell
Stop-Process -Id <PID> -Force
```

### 3. AIGCPanel `Ping` 报错 `URLError`

这通常说明：

1. AIGCPanel 没打开
2. launcher 接口没启动
3. `base_url` 端口写错了
4. 软件刚装好，但模型 / 模板 / 工作流还没准备完

### 4. 页面显示 AIGCPanel 已启用，但没有真人声音

优先检查：

1. AIGCPanel 里是否真的有声音克隆记录
2. 是否真的有数字人视频模板
3. `entry` / `entryArgs` 是否是你机器上的真实路径
4. `resultRoots` 是否包含了 AIGCPanel 实际输出目录
5. 你是否已经先在 AIGCPanel 软件里手工跑通过一次声音合成和一次视频合成

### 5. 点“提交当前播报”没反应

先确认页面里是否已经有“当前播报”。

如果当前回复为空，提交时本来就没有内容可推。

### 6. 接飞书没有收到消息

先排查：

1. `webhook_url` 是否填对
2. 环境变量 `FEISHU_WEBHOOK_URL` 是否真的生效
3. 飞书机器人是否允许当前群接收

### 7. 接弹幕源没动静

检查顺序：

1. bridge 是否先启动
2. WebSocket 地址是否正确
3. `websocket-client` 是否安装
4. 外部协议是否符合 `barragegrab_type3`

如果不是这一套协议，需要改归一化逻辑。

## 十三、目录结构

```text
apps/live-studio/                本地直播控制台页面
config/                          配置模板与本机配置
data/product-catalog/            商品数据源
data/barrage-logs/               弹幕日志输出
data/review-reports/             复盘报告输出
docs/guides/                     操作指南
scripts/live_bridge.py           本地 bridge 启动入口
scripts/connect_douyin_barragegrab.py   弹幕 relay 启动入口
scripts/showman_runtime/         运行时核心逻辑
skills/                          业务技能与参考资料
tests/                           运行时测试
```

## 十四、建议你接着看的文档

如果你已经把 README 跑通了，接下来建议按这个顺序继续看：

1. [P1-本地直播控制台与真实接入联调.md](docs/guides/P1-本地直播控制台与真实接入联调.md)
2. [P0-AIGCPanel安装与数字人制作.md](docs/guides/P0-AIGCPanel安装与数字人制作.md)

第一份告诉你“仓库怎么接”，第二份告诉你“AIGCPanel 里怎么把资产准备好”。

## 十五、最后给你的建议

如果你是第一次跑这个项目，不要一上来就追求“真人原声一步到位”。

最稳的做法是：

1. 先跑本地演示
2. 再确认手动播报和人工回复
3. 再接飞书
4. 最后才接 AIGCPanel 真人链路

只要你按这个顺序来，定位问题会轻松很多。
