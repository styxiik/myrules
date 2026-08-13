# Shadowrocket Modules

本目录只记录 Shadowrocket 模块来源，不镜像仍在维护的上游模块。

原则：

1. 优先使用原作者/主维护仓库提供的 Shadowrocket / Surge 原生模块。
2. 不再引用已经删除的 `ddgksf2013/Modules`。
3. Quantumult X 继续优先使用对应项目维护的 QX 原生配置；只有没有原生 Shadowrocket 版本的功能才考虑后续转换。
4. 模块涉及 HTTPS MITM。Shadowrocket 的 CA 证书应在设备本地生成和信任，不要把 CA 私钥或 p12 提交到公开 GitHub。

## 推荐原生模块

### Block HTTPDNS — blackmatrix7

Quantumult X 当前使用 blackmatrix7 的 QX 原生版本；Shadowrocket 使用同仓库的原生 sgmodule：

https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/BlockHTTPDNS/BlockHTTPDNS.sgmodule

### 知乎增强 / 去广告 — blackmatrix7

Quantumult X 继续使用项目维护的 `script/zheye/zheye.snippet`；Shadowrocket 使用原生 Plus 模块：

https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/ZhihuAssistant/ZhihuAssistantPlus/zhihu_plus.sgmodule

### 百度贴吧 — app2smile

Quantumult X：

https://raw.githubusercontent.com/app2smile/rules/master/module/tieba-qx.conf

Shadowrocket：

https://raw.githubusercontent.com/app2smile/rules/master/module/tieba.sgmodule

### Spotify — app2smile

Quantumult X：

https://raw.githubusercontent.com/app2smile/rules/master/module/spotify.conf

Shadowrocket / Surge module：

https://raw.githubusercontent.com/app2smile/rules/master/module/spotify.module

### YouTube 去广告 / 增强 — Maasea

Shadowrocket 使用 Maasea 当前维护的原生模块：

https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule

Quantumult X 暂时继续使用当前仍在维护的 ddgksf2013 Rewrite 封装，直到确认一个同等功能、由原作者维护的 QX 原生入口。

## 暂不使用已删除的墨鱼 Modules

历史上的：

`https://github.com/ddgksf2013/Modules/raw/main/Adblock.sgmodule`

已经不是有效的官方上游，因此不应继续写进新配置。第三方备份仅用于审计历史，不作为自动订阅源。

当前仍在维护的 `ddgksf2013/Rewrite` 可继续作为 Quantumult X 的上游来源，例如彩云天气、微信小程序、喜马拉雅、网易云、Q-Search、豆瓣和微信 URL 解锁。Shadowrocket 对这些功能后续采用“有原生上游则直连原生；没有才转换”的方式处理。

## Shadowrocket 导入

在 Shadowrocket 的模块管理中分别添加上面的远程模块 URL。不要把它们复制合并成一个本地大模块，这样上游更新可以直接生效，也更容易定位某个模块出问题时的来源。
