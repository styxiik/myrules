# Quantumult X 模块来源审计

目标：优先使用仍在维护的原作者或主维护仓库，不因为 Shadowrocket 迁移而把 QX 改成已删除或第三方备份来源。

## 直接保留的主维护来源

- BlockHTTPDNS：blackmatrix7 `rewrite/QuantumultX/BlockHTTPDNS/BlockHTTPDNS.conf`
- 知乎：blackmatrix7 `script/zheye/zheye.snippet`
- 百度贴吧：app2smile `module/tieba-qx.conf`
- Spotify：app2smile `module/spotify.conf`

这些项目同时提供 Shadowrocket 原生模块时，Shadowrocket 使用对应原生版本，不做 QX 到 Shadowrocket 的转换。

## 继续保留 ddgksf2013/Rewrite 的项目

`ddgksf2013/Rewrite` 当前仓库仍存在且仍有维护记录，因此 QX 中彩云天气、微信小程序、YouTube QX 封装、喜马拉雅、网易云、Q-Search、豆瓣、Google Redirect 和微信 URL 解锁等功能暂时保留现有来源。

这和已经删除的 `ddgksf2013/Modules` 不同：后者不再作为 Shadowrocket 新配置的订阅上游。

## Shadowrocket 最终架构

- 主配置直接使用根目录 `META.yaml`，不再维护单独的 Shadowrocket 配置文件。
- Shadowrocket 专属能力统一由 `Shadowrocket/Modules/All-in-One.sgmodule` 提供。
- All-in-One 自动聚合 Tailscale、BlockHTTPDNS、知乎、贴吧、Spotify、YouTube Enhance，并固定保留 Google CN 重定向所需的 HTTP Engine / URL Rewrite / MITM 配置。
- `scripts/build_shadowrocket_bundle.py` 与 `update-shadowrocket-bundle.yml` 负责自动更新聚合模块。
- `sources.json` 仅作为上游清单和构建输入，不是 Shadowrocket 直接订阅格式。

## 节点订阅

- Quantumult X 继续使用 `MyownQX订阅`，保留现有 parser 逻辑。
- Mihomo/Clash 与 Shadowrocket 共用根目录 `META.yaml`，继续使用 `MyownMETA订阅`。
