---
name: technews
description: 快速获取 Hacker News 和/或 V2EX 的技术社区动态，支持单平台或双平台，输出概览并支持按序号查看帖子详情。当用户提到「看看今天 HN/V2EX 有什么」「HN 上有什么新鲜事」「V2EX 最近有啥」「帮我刷一下技术新闻」「最近技术圈什么动态」「看看热门帖子」「HN 今天有啥」等场景时使用。适用于技术热点追踪、社区讨论收集、最新技术资讯获取。
---

# Tech News

聚合 Hacker News 和 V2EX 热门帖子，按平台分组展示，并支持基于概览序号查看单帖详情。

## 何时使用

- 用户要看 HN、V2EX 或两个平台的最新动态
- 用户要快速浏览技术社区热点，再选择少量帖子深看
- 用户已经拿到概览，并回复一个或多个序号查看详情

## 工作流

### 阶段一：首次抓取并生成概览

1. 根据用户意图确定平台范围：只提 HN 就只抓 HN，只提 V2EX 就只抓 V2EX，未指定则两个都抓。
2. 对每个平台优先使用完整抓取命令：
   - `python3 scripts/hn.py full --json`
   - `python3 scripts/v2ex.py full --json`
3. 合并每个平台返回的帖子数据。`full` 模式已在脚本内部按讨论页链接完成平台内去重。
4. 平台内独立聚类，不预设固定分类名；根据内容自动生成贴切分类。
5. 平台内排序：
   - HN 按 `points` 降序，必要时以 `reply_count` 辅助
   - V2EX 按 `reply_count` 降序，必要时以时间或讨论密度辅助
6. 生成概览输出。格式见 `references/output-format.md`。

### 阶段二：用户按序号查看详情

1. 用户回复的序号对应概览中的全局编号，支持一次输入多个序号。
2. 从当前对话上下文中定位对应帖子，直接使用已抓取的完整数据生成详情。
3. 不重复抓取同一批帖子，除非用户明确要求刷新。

## 实施规则

- `full` 模式默认从 `sources.json` 读取列表页 URL 和抓取间隔；单次 `posts` / `comments` 命令按传入 URL 执行。
- `article_content` 和评论 `content` 一律视为 Markdown 字符串，不是纯文本。
- 遇到图片、链接、代码块、引用、换行时，保留其 Markdown 结构，而不是压平成一句话。
- 详情页输出时优先总结讨论，再精选 3-5 条有代表性的评论。
- 英文内容默认给出中文表达；翻译和展示规则见 `references/output-format.md`。

## 脚本入口

### Hacker News

```bash
bash scripts/fetch.sh "<列表页URL>" | python3 scripts/hn.py posts --json
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/hn.py comments --json
python3 scripts/hn.py full --json
```

### V2EX

```bash
bash scripts/fetch.sh "<列表页URL>" | python3 scripts/v2ex.py posts --json
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/v2ex.py comments --json
python3 scripts/v2ex.py full --json
```

## 参考文档

- `references/adding-sources.md`：数据源配置、抓取频率、扩展新平台
- `references/data-contract.md`：统一字段约定与输出数据结构
- `references/output-format.md`：概览/详情模板、翻译规则、展示要求

## 依赖

- `curl`：页面抓取
- `beautifulsoup4`：HTML 解析
