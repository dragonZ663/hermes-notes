---
id: 6
title: "详解：从本地笔记到GitHub Pages — Vitepress自动化部署全流程"
created: "2026-06-07 15:19:01"
source: "cli"
tags:
  - vitepress
  - github-pages
  - ci-cd
  - tutorial
---

# 详解：从本地笔记到GitHub Pages — Vitepress自动化部署全流程

# 详解：从本地笔记到 GitHub Pages

## 一个简单的问题

你在本地写了一篇 Markdown 笔记，想让全世界都能看到它。怎么做到？

最原始的方案：买一台服务器，装 Nginx，配置域名，把 HTML 文件传上去。又贵又麻烦。

更好的方案：**静态站点生成器 + 免费托管 + 自动化部署**。这就是我们正在用的方案。

---

## 三个核心角色

### 1. Vitepress — 把 Markdown 变成 HTML

Vitepress 是一个**静态站点生成器**（Static Site Generator, SSG）。它的工作很简单：

```
输入（你写的）              输出（浏览器能看的）
─────────────────────      ─────────────────────
README.md                  index.html
notes/笔记1.md   ───────→  notes/笔记1.html
notes/笔记2.md             notes/笔记2.html
                           assets/style.css
                           assets/app.js
```

**为什么不用 WordPress 或动态网站？**

| 特性 | 静态站点（Vitepress） | 动态站点（WordPress） |
|------|----------------------|----------------------|
| 服务器成本 | 免费（GitHub Pages） | 需要 VPS/主机 |
| 速度 | 极快（纯 HTML） | 每次请求查数据库 |
| 安全性 | 无需担心注入攻击 | 需要持续打补丁 |
| 维护 | 零运维 | 要更新 PHP/数据库 |
| 适合 | 个人笔记、文档站 | 电商、社区、博客 |

### 2. GitHub Pages — 免费托管

GitHub Pages 是 GitHub 提供的一项免费服务：你把 HTML 文件放到仓库里，它负责让全世界访问。

- 免费：Public 仓库免费
- 自动 CDN：全球节点加速
- 可绑定自定义域名
- 带宽上限：每月 100GB，对个人笔记站绰绰有余

### 3. GitHub Actions — 自动化流水线

GitHub Actions 是 GitHub 的 CI/CD（持续集成/持续部署）服务。

**CI（持续集成）**：每次你推代码，自动执行构建流程（安装依赖、编译、打包）
**CD（持续部署）**：构建完成后，自动把产物发布到指定位置

在我们这个场景里：

```
你 git push
    │
    ▼
GitHub 收到代码
    │
    ▼
Actions 触发（.github/workflows/deploy.yml）
    │
    ├── 1. actions/checkout@v4          → 拉取你的代码
    ├── 2. actions/setup-node@v4        → 安装 Node.js
    ├── 3. npm ci                        → 安装 vitepress 依赖
    ├── 4. npm run build                 → vitepress 把 Markdown 编译成 HTML
    ├── 5. actions/upload-pages-artifact → 把生成的 HTML 上传为部署产物
    └── 6. actions/deploy-pages@v4       → 把产物发布到 GitHub Pages
                                              │
                                              ▼
                                         你的网站更新了！
```

这就是**「推送即上线」**的完整链路。

---

## 完整数据流

从你在终端写笔记到用户浏览器看到页面的全过程：

```
┌──────────────────────────────────────────────┐
│              你的本地电脑                      │
│                                              │
│  Markdown 笔记 (SQLite 数据库)                │
│       │                                      │
│       ▼                                      │
│  sync_vitepress.py                            │
│  （将笔记同步为 docs/ 下的 .md 文件）          │
│       │                                      │
│       ▼                                      │
│  Vitepress 源文件 (docs/ 目录)                │
│       │                                      │
│       ▼                                      │
│  git add → git commit → git push              │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              GitHub（远程仓库）                │
│                                              │
│  GitHub Actions 检测到 push                   │
│       │                                      │
│       ▼                                      │
│  拉取代码 → 安装 Node.js → npm ci            │
│       │                                      │
│       ▼                                      │
│  vitepress build → 生成 HTML/CSS/JS          │
│       │                                      │
│       ▼                                      │
│  上传产物 → 部署到 GitHub Pages               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              全球用户                         │
│                                              │
│  浏览器访问 https://dragonZ663.github.io/     │
│          hermes-notes/                       │
│       │                                      │
│       ▼                                      │
│  GitHub 的 CDN 返回 HTML 页面                │
│  浏览器加载并渲染 → 你看到的笔记网站          │
└──────────────────────────────────────────────┘
```

---

## 关键抉择背后的原理

### 为什么用 npm ci 而不是 npm install？

```
npm ci      → 读取 package-lock.json，精确安装（CI 环境用）
npm install → 读取 package.json，可能更新 lockfile（开发环境用）
```

- npm ci 更快（跳过依赖解析，直接下载）
- npm ci 保证构建可复现（同一份 lockfile 在任何机器上都安装完全一样的版本）
- npm ci 如果发现 package.json 和 lockfile 不一致，直接报错

这就是为什么第一次构建失败了——当时 package.json 里没有 vitepress，但 lockfile 里有它，两者不一致。

### 为什么需要配置 base 路径？

GitHub Pages 上你的站点地址是：

```
https://dragonZ663.github.io/hermes-notes/
```

注意 hermes-notes/ 这个子路径。如果 Vitepress 认为自己的根路径是 /，那它生成的 CSS/JS 链接会是：

```html
<link rel="stylesheet" href="/assets/style.css" />
```

浏览器会去请求：https://dragonZ663.github.io/assets/style.css（404！）

但实际上应该请求的是：https://dragonZ663.github.io/hermes-notes/assets/style.css

所以必须告诉 Vitepress：我的根路径不是 /，而是 /hermes-notes/。

```ts
// docs/.vitepress/config.ts
base: '/hermes-notes/'
```

如果用了自定义域名（比如 yournote.com），就没有子路径问题，base 设为 '/' 即可。

### 为什么 Actions 需要写权限？

```yaml
permissions:
  contents: read      # 读取代码
  pages: write        # 写入 GitHub Pages
  id-token: write     # 身份验证 - deploy-pages 需要
```

GitHub Actions 默认只有读取权限。要发布到 Pages，必须显式授予 pages: write 权限。

---

## 日常使用流程

### 记笔记

```bash
cd ~/.hermes/notes
python3 notes_cli.py create "我的新笔记" "# 笔记内容"
```

### 同步并发布

```bash
python3 sync_vitepress.py  # 同步到 Vitepress
git add .
git commit -m "新笔记：xxx"
git push                    # 自动部署到网站
```

等 1-2 分钟，网站自动更新。

### 本地预览

```bash
cd docs
npm run dev
# 访问 http://localhost:5173/hermes-notes/
```

---

## 故障排查

| 症状 | 检查点 |
|------|--------|
| Actions 失败 | 打开 GitHub Actions 页面看具体哪个步骤报错 |
| 页面空白 | 检查 base 路径是否正确，检查浏览器开发者工具的 Network 面板 |
| 修改没生效 | 确认 git push 成功，等 Actions 跑完 |
| 排版错乱 | 本地 npm run dev 预览确认 |

---

## 总结

这套架构的核心思想是**关注点分离**：

| 层 | 工具 | 职责 |
|----|------|------|
| 数据层 | SQLite + notes CLI | 存储和管理笔记 |
| 转换层 | sync_vitepress.py | 把结构化数据转成 Markdown 文件 |
| 生成层 | Vitepress | 把 Markdown 编译成 HTML/CSS/JS |
| 部署层 | GitHub Actions | 自动化构建和发布 |
| 托管层 | GitHub Pages | 免费 CDN 全球分发 |

每一层只做一件事，层与层之间通过**文件系统**（Markdown 文件）和**版本控制**（Git）连接，松耦合、易替换。哪天你想换掉 Vitepress 用 Docusaurus，或者换掉 GitHub Pages 用 Cloudflare Pages，只需要换对应那一层就行，其他部分完全不受影响。
