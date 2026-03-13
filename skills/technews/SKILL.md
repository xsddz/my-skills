---
name: technews
description: 快速获取 Hacker News 和/或 V2EX 的技术社区动态，支持单平台或双平台，提供概览+序号交互查看详情。当用户说「看看今天 HN/V2EX 有什么」「HN 上有什么新鲜事」「V2EX 最近有啥新鲜事」「帮我刷一下技术新闻」「最近技术圈什么动态」「看看热门帖子」「HN 今天有啥」等时立即触发。适用于技术热点追踪、社区讨论收集、最新技术资讯获取。
---

# Tech News

快速聚合 HN 和/或 V2EX 热门帖子，全量抓取所有列表页后合并去重，按平台分组展示，通过序号快速查看感兴趣帖子的评论详情。

## 处理流程

### 阶段一：数据准备（首次触发时执行）

1. **确定平台范围** - 根据用户意图确定要抓取的平台（只提到 HN 就只抓 HN，只提到 V2EX 就只抓 V2EX，未指定则两个都抓）
2. **全量抓取列表** - 对每个平台，抓取"列表页配置"中所有列表页 URL，合并结果后按帖子讨论页 URL 去重
3. **批量抓取评论** - 对去重后的每篇帖子抓取讨论页，获取完整评论树并合并到帖子信息中
4. **平台内分类** - 对每个平台内的帖子独立聚类，不预设类别，生成贴切的分类名称
5. **平台内排序** - HN 按 points 降序；V2EX 按 reply_count 降序；同值时互补
6. **生成概览输出** - 全局连续序号，按平台区块 → 分类区块 → 条目列表输出（格式见[概览格式](#概览格式)）

### 阶段二：详情响应（用户回复序号时）

1. **定位帖子** - 用户回复的序号即概览中的全局连续编号，从对话上下文中按此编号找到对应帖子（含已抓取的完整评论数据）；支持一次输入多个序号
2. **生成详情输出** - 直接用已有数据按详情格式输出，无需重新抓取（格式见[详情格式](#详情格式)）

## 列表页配置

### Hacker News

默认抓取以下列表页（全部合并去重）：
- 首页：`https://news.ycombinator.com`

### V2EX

默认抓取以下列表页（全部合并去重）：
- 技术：`https://www.v2ex.com/?tab=tech`
- 最热：`https://www.v2ex.com/?tab=hot`
- 全部：`https://www.v2ex.com/?tab=all`

### 脚本用法

抓取帖子列表：
```bash
bash scripts/fetch.sh "<列表页URL>" | python3 scripts/hnposts.py - --json
bash scripts/fetch.sh "<列表页URL>" | python3 scripts/v2exposts.py - --json
```

抓取帖子评论：
```bash
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/hncomments.py - --json
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/v2excomments.py - --json
```

抓取 V2EX 全部列表页并合并去重（示例）：
```python
import subprocess, json

urls = [
    "https://www.v2ex.com/?tab=tech",
    "https://www.v2ex.com/?tab=hot",
    "https://www.v2ex.com/?tab=all",
]
seen, posts = set(), []
for url in urls:
    html = subprocess.check_output(["bash", "scripts/fetch.sh", url], text=True)
    result = subprocess.run(
        ["python3", "scripts/v2exposts.py", "-", "--json"],
        input=html, capture_output=True, text=True
    )
    for p in json.loads(result.stdout):
        if p["url"] not in seen:
            seen.add(p["url"])
            posts.append(p)
```

## 输出格式

### 翻译规则

**触发条件**：
- **标题**：英文标题附中文翻译，格式 `原标题 (中文翻译)`；已含中文则省略
- **摘要**：统一中文输出
- **评论内容**：英文评论附中文翻译，格式 `（中文翻译：...）`；已含中文则省略

**翻译质量要求**：

1. **避免欧化句式**：不要按英文语序直译，应按中文"流水句"习惯重组。遇到 "X is Y because Z" 式长句，拆成两个短句表达。目标：朗读时不绕口。

2. **术语处理**：广泛通用的技术术语保留英文（如 AI、API、LLM、PR、CLI、SaaS），冷僻缩写或专有概念须附中文说明（如 `RLHF（基于人类反馈的强化学习）`）；禁止中英混杂（如 ❌"这个方案很 elegant"→ ✅"这个方案很优雅"）。

3. **情感色彩一致**：原文中性词译成中性词，褒义词译成褒义词，不随意添加评价。例如 "brutal"（直接/犀利）≠ "残酷"，"neat"（简洁/巧妙）≠ "整洁"。

4. **保留用户名**：`@username` 格式原样保留，不翻译。

5. **句子长度控制**：单句超过 40 字时主动拆分，确保可读性。

### 概览格式

```
## [平台图标] 平台名称

### [分类名] (X条)

1. **原标题 (中文翻译)** - 作者          # 标题为中文时省略括号部分
   🔥 点赞数  💬 评论数  ·  [讨论](url) | [原文](url)   # V2EX无点赞数时省略🔥部分；无原文链接时省略 | [原文]
   💬 评论摘要：（中文）核心讨论内容摘要，约20-50字
---

2. **标题2** - 作者2
   💬 评论数  ·  [讨论](url)
   💬 ...
---

回复序号查看详细评论，可同时输入多个序号（如：1 3 5）
```

**规则**：
- 序号全局连续（跨平台递增）
- 链接使用 Markdown 内联格式（`[文字](url)`）
- 只有一个平台时省略平台标题行

### 详情格式

```
## 帖子详情 #N

**原标题 (中文翻译)**                   # 标题为中文时省略括号部分
👤 作者  ·  ⏰ YYYY-MM-DD HH:MM  ·  🔥 点赞数  ·  💬 总评论数   # V2EX无点赞数时省略🔥部分
🔗 [讨论页](url) | [原文](url)          # 无原文链接时省略 | [原文]
📊 统计：根评论 N 条 | 嵌套回复 M 条

---

📝 讨论总结
（中文）约100-150字，提炼整帖核心观点、争议点和共识

---

⭐ 精彩评论（精选 3-5 条）

1. @author1 (时间) [🔥 点赞数]          # 无点赞数据时省略 [🔥 ...]
   内容：...（原文）
   （中文翻译：...）                     # 原评论主要为英文时附加
   ↳ Y 条回复                           # 无回复时省略此行

2. @author2 (时间)
   内容：...
   （中文翻译：...）

...
```

## 数据格式

### 帖子数据（汇总）

列表抓取并去重后批量填充评论，每篇帖子的完整数据结构如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str | 帖子标题 |
| `url` | str | 帖子讨论页链接（去重依据） |
| `article_url` | str\|null | 原文链接；HN 有值，V2EX 通常为 `null` |
| `author` | str | 作者 |
| `time` | str | 发布时间（`YYYY-MM-DD HH:MM:SS +08:00`） |
| `points` | int\|null | 点赞数（HN有，V2EX为null） |
| `reply_count` | int | 评论数 |
| `last_reply_by` | str\|null | 最后回复人（V2EX有，HN为null） |
| `platform` | str | 平台名称 |
| `total_comments` | int | 根评论数量（评论抓取后填充） |
| `total_replies` | int | 嵌套回复总数（评论抓取后填充） |
| `comments` | list | 完整评论树，批量抓取后填充，每条包含 `id, author, time, content, replies[]` |

## 参考文档

- 添加新数据源指南: `references/adding-sources.md`

## 依赖

- **curl** - 页面抓取
- **beautifulsoup4** - HTML 解析（`pip install beautifulsoup4` 或 `apt install python3-bs4`）
