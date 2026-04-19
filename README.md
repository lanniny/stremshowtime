# stremshowtime

本仓库是一个本地数字人直播控制台与联调项目，聚焦三个方向：

- 本地直播间风格的演示页与控制台
- 弹幕接入、人工回复、自动播报与复盘链路
- AIGCPanel / 飞书 / 外部弹幕源的真实集成边界

## 主要能力

- `apps/live-studio/` 提供本地直播控制台
- `scripts/live_bridge.py` 提供统一 HTTP bridge
- `scripts/showman_runtime/` 提供脚本生成、弹幕处理、AIGCPanel 桥接、会话状态等运行时
- `config/live-bridge.example.json` 提供本地联调配置模板
- `tests/test_live_bridge_runtime.py` 覆盖关键运行时测试

## 快速开始

1. 可选：复制配置模板

```powershell
Copy-Item config\live-bridge.example.json config\live-bridge.json
```

2. 启动本地 bridge

```powershell
python scripts/live_bridge.py
```

3. 打开浏览器

```text
http://127.0.0.1:8765
```

4. 如果只想看完整演示流

```powershell
python scripts/live_bridge.py --load-demo
```

## AIGCPanel 说明

仓库已经接入 AIGCPanel launcher / remote config 探测与任务轮询逻辑，但要获得“真人原声”效果，仍需要在本机 AIGCPanel 中准备好：

- 可用的 TTS / 声音克隆模型
- 已完成的音色克隆记录
- 可用的数字人视频模板

如果这些资产不存在，bridge 会正常工作，但无法回放你原来的真人音色结果。

## 测试

```powershell
python -m unittest discover -s tests
```

## 目录概览

```text
apps/                   本地直播控制台
config/                 配置模板
data/                   运行日志与复盘输出
docs/                   指南与需求文档
scripts/                bridge 与运行时
skills/                 业务技能与参考资料
tests/                  运行时测试
```
