---
id: 7
title: "HTTPS 页面下 HTTP 请求被阻止（Mixed Content）的原因与解决方案"
created: "2026-06-08 02:05:14"
source: "weixin"
tags:
  - http
  - https
  - wwb-security
---

# HTTPS 页面下 HTTP 请求被阻止（Mixed Content）的原因与解决方案

## 原因

HTTPS 页面下的 JS 发起 HTTP 请求时，浏览器会报错并阻止：

> **Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure resource 'http://...'. This request has been blocked; the content must be served over HTTPS.**

根本原因是浏览器的**安全策略**——加密页面（HTTPS）中混入明文请求（HTTP）会破坏传输安全，中间人可以轻松窃听或篡改 HTTP 响应的内容，相当于把 HTTPS 的外壳戳了个洞。

---

## 解决方案

### 1. 直接改目标为 HTTPS

最简单直接。把请求地址从 http:// 改成 https://，前提是后端支持 HTTPS。

```js
fetch('https://api.example.com/data')  // ✅
```

### 2. Nginx 反向代理（生产环境最常用）

浏览器请求你的 Nginx HTTPS 地址，Nginx 在服务端内部用 HTTP 转发给后端：

```nginx
location /api/ {
    proxy_pass http://192.168.1.100:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

注意点：CORS、WebSocket 升级、超时配置。

### 3. upgrade-insecure-requests

HTML 头部或 Nginx 响应头加一行，浏览器自动把所有 HTTP 请求升级为 HTTPS：

```html
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
```

```nginx
add_header Content-Security-Policy "upgrade-insecure-requests";
```

前提是目标地址也支持 HTTPS。

### 4. Service Worker 拦截转发

注册 SW 拦截 fetch，重写 HTTP 为 HTTPS：

```js
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.protocol === 'http:') {
    url.protocol = 'https:';
    event.respondWith(fetch(url));
  }
});
```

前端代码不用改，但需维护 SW 生命周期。

### 5. 同源部署 / 相对路径

如果前端和后端同域，用相对路径或协议相对 URL：

```js
fetch('/api/data')               // 同源 ✅
fetch('//api.example.com/data')  // 协议相对 ✅
```

协议随页面自动继承，不触发混合内容。

### 6. 换传输方式

| 场景 | 替代方案 |
|------|----------|
| 实时数据 | WebSocket (wss://) |
| 单向数据流 | Server-Sent Events |
| 静态资源 | HTTPS 直链 |

---

## 方案对比

| 方案 | 修改量 | 是否改前端代码 | 适用场景 |
|------|--------|---------------|----------|
| 改目标为 HTTPS | 最小 | 是 | 后端支持 HTTPS |
| Nginx 反向代理 | 中等 | 否 | 后端不支持 HTTPS |
| upgrade-insecure-requests | 最小 | 否 | 后端支持 HTTPS |
| Service Worker | 较大 | 否 | 复杂场景、PWA |
| 相对 URL / 同源 | 最小 | 是 | 同源部署 |

**生产推荐：** 后端支持 HTTPS → 直接改；不支持 → Nginx 代理；不想碰代码 → upgrade-insecure-requests。