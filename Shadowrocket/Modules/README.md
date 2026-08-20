# Shadowrocket Modules

Shadowrocket 直接导入仓库根目录的 `META.yaml` 作为主配置，不再维护单独的 `Shadowrocket-META.yaml`。

主配置保持 Mihomo / Shadowrocket 共用；所有 Shadowrocket 专属能力都放在「配置 -> 模块」中。这样不会把 Shadowrocket 专属语法写进 Mihomo 配置。

## 推荐：一个链接更新全部模块

只需要在 Shadowrocket「配置 -> 模块 -> 右上角 +」添加下面这个远程模块：

https://raw.githubusercontent.com/styxiik/myrules/main/Shadowrocket/Modules/All-in-One.sgmodule

`All-in-One.sgmodule` 自动聚合以下内容：

- Tailscale
- BlockHTTPDNS / blackmatrix7
- ZhihuAssistantPlus / blackmatrix7
- Startup Ads 开屏去广告 / blackmatrix7
- Tieba / app2smile
- Spotify / app2smile
- YouTube Enhance / Maasea

同时固定加入本仓库自己的基础配置：

- `block-quic = all`：Shadowrocket 原生全局禁用 QUIC / UDP 443
- `^https?://(www\.)?g\.cn` 302 到 `https://www.google.com`
- `^https?://(www\.)?google\.cn` 302 到 `https://www.google.com`

`.github/workflows/update-shadowrocket-bundle.yml` 每天拉取这些上游的最新模块，由 `scripts/build_shadowrocket_bundle.py` 按 section 重新生成 `All-in-One.sgmodule`。生成器不会直接拼接多个 `[MITM]`，而是合并并去重 hostname，统一使用 `%APPEND%`；模块参数和 `force-http-engine-hosts` 也会合并保留。

因此 Shadowrocket 端只维护这一条远程模块 URL。以后使用模块页面的「更新模块」或自动后台更新，就会刷新整套聚合模块。

如果某个上游临时失效，生成 workflow 会失败并保留上一版可用的 `All-in-One.sgmodule`，不会把空文件覆盖到主分支。

## 为什么不直接使用第三方“大而全” All-in-One

当前公开可确认的 Shadowrocket `AllInOne.sgmodule` 主要来自 blackmatrix7，而不是 ddgksf2013 当前维护的模块仓库。blackmatrix7 的 AllInOne 覆盖范围非常广，会带入大量与本配置目标无关的规则、脚本和 MITM hostname；同时不同功能的独立原生模块更新节奏可能更快。

因此本仓库采用“精选上游 + 自动聚合”的方式：人工只维护少量上游入口，实际内容由原作者维护，GitHub Action 自动生成单一模块链接。这样既保留一键更新体验，也减少无关规则和冲突风险。

## Tailscale

Shadowrocket 原生 Tailscale 全局模组使用专属 `TAILSCALE` 规则策略，而 Mihomo 不认识这个策略名，因此 Tailscale 的 Shadowrocket 专属规则保留在本目录的 `Tailscale.sgmodule`，并由 All-in-One 自动聚合：

https://raw.githubusercontent.com/styxiik/myrules/main/Shadowrocket/Modules/Tailscale.sgmodule

启用前先在 Shadowrocket 设置中启用原生 Tailscale 功能。模块负责把 `*.ts.net`、`100.64.0.0/10` 和 Tailscale IPv6 ULA 流量交给 `TAILSCALE` 策略。

共享的 `Clash/ClashDirect.yaml` 仍保留 `100.64.0.0/10` 与 `fd7a:115c:a1e0::/48`，用于 Windows Mihomo / Tailscale 共存。

## 独立模块地址（备用）

如果需要单独启停某一功能，仍可以不用 All-in-One，改为分别安装以下模块。

### Block HTTPDNS — blackmatrix7
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/BlockHTTPDNS/BlockHTTPDNS.sgmodule

### 知乎增强 / 去广告 — blackmatrix7
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/ZhihuAssistant/ZhihuAssistantPlus/zhihu_plus.sgmodule

### 开屏去广告 — blackmatrix7
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/script/startup/startup.sgmodule

### 百度贴吧 — app2smile
https://raw.githubusercontent.com/app2smile/rules/master/module/tieba.sgmodule

### Spotify — app2smile
https://raw.githubusercontent.com/app2smile/rules/master/module/spotify.module

### YouTube 去广告 / 增强 — Maasea
https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule

## 原则

1. `META.yaml` 是唯一主配置和节点订阅入口，继续使用 `MyownMETA订阅` 占位符。
2. 不再向 Clash YAML 写 `modules:`；实测 Shadowrocket 转换器会忽略该字段。
3. 优先使用原作者/主维护仓库提供的 Shadowrocket / Surge 原生模块。
4. 不再引用已删除的 `ddgksf2013/Modules`。
5. 模块涉及 HTTPS MITM 时，CA 证书只在设备本地生成和信任，不把证书私钥或 p12 提交到 GitHub。
6. 模块规则优先于主配置，因此 Shadowrocket 专属的 Tailscale 规则可以覆盖共享 META 中的通用直连逻辑。

## 机器可读清单与自动检查

`sources.json` 保存各个上游模块地址，是构建 All-in-One 的来源清单，不是给 Shadowrocket 直接订阅的格式。`.github/workflows/check-module-upstreams.yml` 每周检查这些 URL 是否仍可访问，也支持手动执行。
