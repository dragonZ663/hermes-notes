---
id: 5
title: "Hermes Notes 公网访问方案分析"
created: "2026-06-07 08:46:13"
source: "conversation"
tags:
  - hermes-notes
  - vitepress
  - network
  - tunnel
---

# Hermes Notes 公网访问方案分析

讨论了三种公网访问 Hermes Notes Vitepress 站点的方案：

1. Cloudflare Tunnel（推荐）— 免费，HTTPS，不依赖入站端口
   - 安装 cloudflared，一条命令启动隧道
   - 可绑定自定义域名

2. ngrok — 快速测试用，免费版 URL 随机、有速率限制

3. Tailscale Funnel — 私密网络方案

核心结论：公网访问需穿越 3 层障碍（路由器 NAT → Windows 防火墙 → WSL2 NAT），隧道方案从出站发起连接，避免入站端口问题，是最省心的选择。