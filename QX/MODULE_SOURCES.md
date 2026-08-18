# Quantumult X 模块来源审计

目标：优先使用仍在维护的原作者或主维护仓库，不因为 Shadowrocket 迁移而把 QX 改成已删除或第三方备份来源。

## 直接保留的主维护来源

- BlockHTTPDNS：blackmatrix7 `rewrite/QuantumultX/BlockHTTPDNS/BlockHTTPDNS.conf`
- 知乎：blackmatrix7 `script/zheye/zheye.snippet`
- 百度贴吧：app2smile `module/tieba-qx.conf`
- Spotify：app2smile `module/spotify.conf`

这些项目同时提供 Shadowrocket 原生模块时，Shadowrocket 直接使用对应原生版本，不做 QX 到 Shadowrocket 的转换。

## 继续保留 ddgksf2013/Rewrite 的项目

`ddgksf2013/Rewrite` 当前仓库仍存在且仍有维护记录，因此 QX 中彩云天气、微信小程序、YouTube QX 封装、喜马拉雅、网易云、Q-Search、豆瓣、Google Redirect 和微信 URL 解锁等功能暂时保留现有来源。

这和已经删除的 `ddgksf2013/Modules` 不同：后者不再作为 Shadowrocket 新配置的订阅上游。

## Shadowrocket 对应策略

Shadowrocket 直接导入根目录 `META.yaml`；专属功能通过模块单独安装：

- 本仓库：Tailscale 路由模块
- blackmatrix7：BlockHTTPDNS、知乎
- app2smile：贴吧、Spotify
- Maasea：YouTube.Enhance

其余没有可靠原生上游的功能先不自动转换进主配置，等上机测试稳定后再逐个补齐。

## 节点订阅

- Quantumult X 继续使用 `MyownQX订阅`，保留现有 parser 逻辑。
- Mihomo/Clash 与 Shadowrocket 共用根目录 `META.yaml`，继续使用 `MyownMETA订阅`。
