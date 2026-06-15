---
id: 16
title: "Playwright Locator 选择策略与 ARIA Role 详解"
created: "2026-06-15 06:14:05"
source: "conversation"
tags:
  - playwright
  - testing
  - automation
---

# Playwright Locator 选择策略与 ARIA Role 详解

## 一、Playwright 两大 Locator 方法

### `get_by_text()` — 按可见文本找元素

```python
await page.get_by_text("Username and password").click()
```

**含义：** 在页面中找到文本内容包含/匹配指定字符串的元素。

**适合场景：**
- 点击普通文本区域（tab、列表项、卡片标题、菜单项）
- 页面提示文案/描述文案校验
- 某些组件没有良好语义结构时兜底

**风险与注意点：**
- 容易匹配到多个元素（strict mode violation）
- 文本稍微变动就容易失效（"Username and password" → "Use username and password"）
- 受国际化影响较大

---

### `get_by_role()` — 按语义角色 + 可访问名称找元素

```python
await page.get_by_role("button", name="Continue").click()
```

**含义：** 找到一个角色是 `button`，且可访问名称是 `Continue` 的元素。

**适合场景：**
- 标准交互控件：按钮、链接、输入框、复选框、单选
- 希望脚本更稳定、更贴近用户行为
- 团队协作时代码可读性更高

**风险与注意点：**
- 要求页面语义较好，否则可能找不到
- `name` 指的是 accessible name，不单纯是 innerText

---

## 二、ARIA Role 详解

### 什么是 ARIA Role？

**ARIA** = Accessible Rich Internet Applications

**一句话：** ARIA role 用来告诉浏览器和辅助技术（如读屏软件）：这个元素"在语义上是什么"。

### 为什么需要 ARIA role？

HTML 原生标签有默认语义：

| 标签 | 默认 role |
|------|-----------|
| `<button>` | button |
| `<a href>` | link |
| `<input type="text">` | textbox |

但现代前端框架大量使用自定义组件：

```html
<div class="btn-primary" onclick="submit()">Continue</div>
```

视觉上是按钮，但浏览器不知道它是按钮，屏幕阅读器也不知道，Playwright 的 `get_by_role("button")` 也找不到。ARIA role 就是补充语义：

```html
<div class="btn-primary" role="button" onclick="submit()">Continue</div>
```

### 常见 ARIA Role

**交互类：** `button`, `link`, `textbox`, `checkbox`, `radio`, `switch`

**结构类：** `dialog`（弹窗）, `alert`, `tablist`, `tab`, `menu`, `menuitem`

**表格类：** `table`, `row`, `cell`

---

## 三、Accessible Name（可访问名称）

在 `get_by_role("button", name="Continue")` 中，`name` 指的是 **accessible name**，它的来源不只是元素文本，还可能来自：

- 元素文本内容
- `aria-label`
- `aria-labelledby`
- `<label>` 关联
- `alt` 属性
- `title` 属性

### DevTools 中查看 ARIA Role

Chrome DevTools：
1. 右键元素 → Inspect
2. 打开 **Accessibility panel**
3. 查看 **Role** 和 **Name**

这两个正是 Playwright `get_by_role()` 定位的依据。

---

## 四、实战选择原则

### 推荐优先级（从高到低）

| 优先级 | 方法 | 适用场景 |
|--------|------|----------|
| 1 | `get_by_role()` | 标准交互控件：button, link, textbox, checkbox 等 |
| 2 | `get_by_label()` | 表单输入框 |
| 3 | `get_by_placeholder()` | 无 label 但 placeholder 稳定的输入框 |
| 4 | `get_by_text()` | 普通文本点击、文案校验、无语义元素 |
| 5 | `locator("css/xpath")` | 以上都不合适时的最后手段 |

### 一句话经验法则

> **交互控件优先用 `get_by_role()`，普通文本或无语义元素再用 `get_by_text()`。**

### 页面分类策略

**有语义页面（推荐）：** button 是 button，tab 是 tab → 用 `get_by_role()`，稳定可靠

**无语义页面（很多内部系统）：** 全是 div，没有 role → 只能用 `get_by_text()` 或 CSS selector

---

## 五、两个方法的本质区别

| 维度 | `get_by_text()` | `get_by_role()` |
|------|----------------|-----------------|
| 依赖什么 | 页面文本 | ARIA 语义 |
| 稳定性 | 文本变动易失效 | 抗 DOM 结构变动 |
| 准确度 | 容易误匹配 | 范围更精确 |
| 可读性 | 一般 | 好（一眼知道操作什么元素） |
| 页面要求 | 低 | 需要良好语义结构 |

---

## 六、两行代码的实践分析

```python
await page.get_by_text("Username and password").click()      # 文本入口，get_by_text 合理
await page.get_by_role("button", name="Continue").click()     # 按钮，get_by_role 更标准
```

第一行说明该元素可能是一个 tab 或文本选择项，没有明确语义角色，按文本找自然。

第二行是标准按钮，用 `get_by_role("button", name="Continue")` 比 `get_by_text("Continue")` 更稳——页面其他位置也可能出现相同文本，但加上 role 限定能把范围收窄。