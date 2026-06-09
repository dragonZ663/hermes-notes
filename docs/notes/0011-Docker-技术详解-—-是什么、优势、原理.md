---
id: 11
title: "Docker 技术详解 — 是什么、优势、原理"
created: "2026-06-09 10:25:42"
source: "conversation"
tags:
  - docker
  - devops
---

# Docker 技术详解 — 是什么、优势、原理

## Docker 是什么？

Docker 是一个**容器化平台**。把应用及其所有依赖打包成一个标准化单元（镜像），在任何机器上都能一致地运行（容器）。

---

## 传统方式 vs Docker 方式

| 传统方式 | Docker 方式 |
|---------|------------|
| 本地装好依赖能跑 → 服务器缺包就炸 | 写 Dockerfile 打包 → 构建镜像 → 到处运行 |
| 环境不一致，"我机器上能跑" | 开发/测试/生产完全一致 |

---

## 核心概念

```
Dockerfile（配方）→ 构建 → 镜像（Image，只读模板）
                              ↓
                         容器（Container，运行实例）
```

- **镜像（Image）**：只读模板，类比 .iso 或 class
- **容器（Container）**：镜像的运行实例，类比进程或 instance
- **Dockerfile**：定义如何构建镜像的"配方"
- **Registry（如 Docker Hub）**：存镜像的"应用商店"

---

## Docker 的优势

| 优势 | 说明 |
|------|------|
| **环境一致性** | 开发/测试/生产完全一样 |
| **轻量** | 共享宿主机内核，无完整 OS 开销 |
| **秒级启动** | 容器秒级，VM 分钟级 |
| **隔离性** | 各自文件系统/网络/进程空间 |
| **可移植** | 一次构建，到处运行 |
| **版本管理** | 镜像可 tag、回滚、分环境 |
| **微服务友好** | 每个服务一个容器，独立部署扩缩 |

---

## Docker vs 虚拟机

```
┌──────────────────┐    ┌──────────────────┐
│  App A │ App B   │    │  App A │ App B   │
├──────────────────┤    ├──────────────────┤
│ GuestOS│ GuestOS │    │  Docker Engine   │
├──────────────────┤    ├──────────────────┤
│   Hypervisor     │    │     Host OS      │
├──────────────────┤    ├──────────────────┤
│     Host OS      │    │    Hardware      │
└──────────────────┘    └──────────────────┘
    虚拟机（几GB/分钟级）        Docker（几十MB/秒级）
```

**VM**：每个含完整 OS，独占资源
**Docker**：共享宿主机内核，仅应用层隔离

---

## 三大底层原理

### 1. Namespace — 隔离

Linux Namespace 让容器以为自己是独立机器：

| 类型 | 隔离内容 |
|------|---------|
| PID | 进程号 — 容器里只看自己的进程树 |
| Network | 网络栈 — 独立 IP、端口 |
| Mount | 文件系统挂载点 |
| UTS | 主机名和域名 |
| User | 用户和用户组 |
| IPC | 进程间通信 |

Docker 创建容器时，给进程组套上 6 层 Namespace 隔离。

### 2. Cgroups — 限额

Control Groups 控制资源使用上限：

```bash
docker run --cpus=1 --memory=512m my-app
```

超出限额 → 内核限制或杀掉进程，防止一个容器撑爆宿主机。

### 3. UnionFS — 分层镜像

镜像由多层只读层堆叠，加一层可写容器层：

```
┌──────────────┐  ← 容器层（可写，容器删除后消失）
├──────────────┤
│  修改的配置   │  ← 当前层
├──────────────┤
│  nginx:latest│  ← 镜像层（只读）
├──────────────┤
│  debian:base │  ← 基础层
└──────────────┘
```

**好处：**
- 多容器共享同一基础层 → 磁盘占用极小
- 构建只重新编译变动层 → 速度快
- 拉取只下载差分层 → 节省带宽

---

## 实操示例

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```bash
docker build -t my-app .          # 构建镜像
docker run -p 8080:80 my-app      # 运行容器
docker push my-app                # 推送到仓库

# 服务器上
docker pull my-app
docker run -d -p 80:80 my-app
```

---

## 一句话总结

> **Docker = Namespace（隔离） + Cgroups（限额） + UnionFS（分层打包），把你的应用和运行环境打包成标准化可移植单元。**
