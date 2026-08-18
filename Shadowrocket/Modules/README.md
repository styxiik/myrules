# Shadowrocket Modules

Shadowrocket 直接导入仓库根目录的 `META.yaml` 作为主配置，不再维护单独的 `Shadowrocket-META.yaml`。

主配置保持 Mihomo / Shadowrocket 共用；所有 Shadowrocket 专属能力都放在「配置 -> 模块」中单独订阅。这样不会把 Shadowrocket 专属语法写进 Mihomo 配置。

## Tailscale

Shadowrocket 原生 Tailscale 全局模组使用专属 `TAILSCALE` 规则策略，而 Mihomo 不认识这个策略名，因此 Tailscale 的 Shadowrocket 专属规则放在本目录的 `Tailscale.sgmodule`：

https://raw.githubusercontent.com/styxiik/myrules/main/Shadowrocket/Modules/Tailscale.sgmodule

启用前先在 Shadowrocket 设置中启用原生 Tailscale 功能。模块负责把 `*.ts.net`、`100.64.0.0/10` 和 Tailscale IPv6 ULA 流量交给 `TAILSCALE` 策略。

共享的 `Clash/ClashDirect.yaml` 仍保留 `100.64.0.0/10` 与 `fd7a:115c:a1e0::/48`，用于 Windows Mihomo / Tailscale 共存。

## 推荐原生模块

### Block HTTPDNS — blackmatrix7
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/BlockHTTPDNS/BlockHTTPDNS.sgmodule

### 知乎增强 / 去广告 — blackmatrix7
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/ZhihuAssistant/ZhihuAssistantPlus/zhihu_plus.sgmodule

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

`sources.json` 保存当前模块订阅地址；`.github/workflows/check-module-upstreams.yml` 每周检查这些 URL 是否仍可访问，也支持手动执行。
