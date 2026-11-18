# Cloudflare Tunnel DIRECT exceptions

Verified: 2026-11-18. Source: [Cloudflare Tunnel firewall requirements](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/).

These are cloudflared's outbound Tunnel endpoints on TCP/UDP port 7844, not the CDN addresses returned when visitors resolve a hosted website.

## Published IP set

`region1.v2.argotunnel.com` IPv4:

```text
198.41.192.167
198.41.192.67
198.41.192.57
198.41.192.107
198.41.192.27
198.41.192.7
198.41.192.227
198.41.192.47
198.41.192.37
198.41.192.77
```

`region2.v2.argotunnel.com` IPv4:

```text
198.41.200.13
198.41.200.193
198.41.200.33
198.41.200.233
198.41.200.53
198.41.200.63
198.41.200.113
198.41.200.73
198.41.200.43
198.41.200.23
```

`region1.v2.argotunnel.com` IPv6:

```text
2606:4700:a0::1
2606:4700:a0::2
2606:4700:a0::3
2606:4700:a0::4
2606:4700:a0::5
2606:4700:a0::6
2606:4700:a0::7
2606:4700:a0::8
2606:4700:a0::9
2606:4700:a0::10
```

`region2.v2.argotunnel.com` IPv6:

```text
2606:4700:a8::1
2606:4700:a8::2
2606:4700:a8::3
2606:4700:a8::4
2606:4700:a8::5
2606:4700:a8::6
2606:4700:a8::7
2606:4700:a8::8
2606:4700:a8::9
2606:4700:a8::10
```

## Subscription policy

META.yaml bypasses TUN for the covering prefixes `198.41.192.0/24`, `198.41.200.0/24`, `2606:4700:a0::/123`, and `2606:4700:a8::/123`. These are operational aggregations containing the published addresses, not an official promise that every IP in each prefix is a Tunnel endpoint.

High-priority DIRECT rules cover those four prefixes and the `argotunnel.com` / `cftunnel.com` domain suffixes. IP rules handle IP-only connections; domain rules cover discovery and Tunnel TLS hostnames. They precede broad Cloudflare/CDN and non-CN proxy rules. Ordinary Cloudflare CDN routing remains unchanged.

Quantumult X has matching local DIRECT rules. Shadowrocket inherits DIRECT rules and TUN exclusions from META.yaml through scripts/build_shadowrocket_config.py. Regenerate artifacts after editing META.yaml, then run scripts/verify_routing_invariants.py.

Refresh the subscription to receive the change. Existing connections may need to reconnect. Direct access still depends on the current network permitting port 7844; these rules cannot prevent ISP outages or Cloudflare failures.

The published IP set is a dated snapshot. Recheck the linked official documentation if Cloudflare changes its endpoints. FedRAMP-specific endpoints and optional update/API destinations are outside this standard Tunnel repair.
