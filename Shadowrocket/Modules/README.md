# Shadowrocket

Shadowrocket 不再直接导入根目录的 `META.yaml`，也不需要另外安装 All-in-One 模块。

## 唯一需要订阅的主配置

```
https://raw.githubusercontent.com/styxiik/myrules/main/Shadowrocket/Shadowrocket.conf
```

`Shadowrocket/Shadowrocket.conf` 是**自动生成文件，不手工维护**。

## 单一配置源

人工维护仍然以根目录 `META.yaml` 为唯一主配置：

```
META.yaml
   ├─ proxy-groups / proxy-providers
   ├─ rules / rule-providers
   ├─ dns
   └─ hosts
        │
        ▼
scripts/build_shadowrocket_config.py
        │
        ├─ Shadowrocket/Rules/*.list
        └─ Shadowrocket/Shadowrocket.conf
```

生成器会读取 META 中的 rule-provider `behavior`，同时检查 payload 实际内容：

- `classical`：保留原生规则类型。
- `domain`：转换为 Shadowrocket 的 `DOMAIN / DOMAIN-SUFFIX / DOMAIN-WILDCARD`。
- `ipcidr`：转换为 `IP-CIDR / IP-CIDR6`，并按 META 的 `no-resolve` 语义生成。
- 如果 payload 本身已经带 `DOMAIN-SUFFIX` 等类型，则优先按实际内容转换，不盲信错误的 provider metadata。

因此 Shadowrocket 不再直接读取 Clash 的 `payload:` YAML，也不会丢失 `behavior: domain/ipcidr` 的语义。

## 模块已内联到主配置

`Shadowrocket/Modules/All-in-One.sgmodule` 仍作为**构建中间产物**自动聚合上游，但 Shadowrocket 客户端不再需要安装它。

它目前聚合：

- Tailscale
- ZhihuAssistantPlus / blackmatrix7
- Startup Ads / blackmatrix7
- Tieba / app2smile
- Spotify / app2smile
- YouTube Enhance / Maasea
- Google CN 重定向
- Shadowrocket 原生 QUIC 设置

随后生成器把模块的以下 section 直接并入最终 `Shadowrocket.conf`：

- `[General]`
- `[Rule]`
- `[Host]`
- `[URL Rewrite]`
- `[Header Rewrite]`
- `[Script]`
- `[MITM]`

模块中的 `{{{参数}}}` 会在构建时使用模块当前默认值展开，因此最终主配置不会残留只能在模块环境中解释的占位符。

## 自动更新

`.github/workflows/update-shadowrocket-bundle.yml` 会在以下情况下自动重建：

- `META.yaml` 修改
- `Clash/**` 修改
- Shadowrocket 模块源或聚合脚本修改
- Shadowrocket 配置生成器修改
- 每日定时任务
- 手工 workflow dispatch

Action 会先生成 `All-in-One.sgmodule`，再生成原生规则集和最终 `Shadowrocket.conf`，最后只提交机器生成产物。

所以正常使用时只需要维护：

1. `META.yaml`
2. 必要时维护 `Shadowrocket/Modules/sources.json`

不要手工编辑 `Shadowrocket/Shadowrocket.conf` 或 `Shadowrocket/Rules/*.list`。

## 节点订阅

META 中的 proxy-provider 名称会直接映射到 Shadowrocket 策略组的订阅筛选，例如：

```
美国优先 = fallback,MYOWN,use=true,policy-regex-filter=...
```

因此 Shadowrocket 中的节点订阅名称需要继续与 META provider 名称一致（当前为 `MYOWN`）。

## Tailscale

Tailscale 规则会在最终配置中保持高优先级：

- `*.ts.net -> TAILSCALE`
- `100.64.0.0/10 -> TAILSCALE`
- `fd7a:115c:a1e0::/48 -> TAILSCALE`

这样可以覆盖共享 META/Clash 中针对这些网段的通用直连规则。
