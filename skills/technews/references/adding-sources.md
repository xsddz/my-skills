# 数据源配置与扩展指南

本文档说明 `technews` 技能如何管理数据源 URL、抓取节奏，以及如何新增平台支持。

## 当前结构

技能当前采用“每个平台一个脚本”的结构：

- `scripts/hn.py`
- `scripts/v2ex.py`
- `scripts/fetch.sh`
- `sources.json`

每个平台脚本统一提供三个子命令：

- `posts`：解析列表页 HTML
- `comments`：解析详情页 HTML
- `full`：自动从 `sources.json` 读取列表页配置，抓取列表页并批量补全详情

## 数据源配置文件

`full` 模式使用的列表页 URL 与抓取间隔都放在 `sources.json`：

```json
{
    "hn": {
        "list_urls": [
            "https://news.ycombinator.com"
        ],
        "request_delay_seconds": 0.0
    },
    "v2ex": {
        "list_urls": [
            "https://www.v2ex.com/?tab=tech",
            "https://www.v2ex.com/?tab=hot",
            "https://www.v2ex.com/?tab=all"
        ],
        "request_delay_seconds": 0.0
    }
}
```

字段说明：

- `list_urls`：该平台需要抓取的列表页 URL 数组
- `request_delay_seconds`：顺序抓取时两次请求之间的等待秒数

## 调整现有数据源

### 增加或删除列表页 URL

直接修改 `sources.json` 对应平台的 `list_urls`。

### 控制抓取频率

如果需要降低请求频率，增大 `request_delay_seconds` 即可。

建议值：

- `0.0`：本地快速试验
- `0.5`：轻量节流
- `1.0` 或以上：更保守的顺序抓取

## 新增平台的步骤

新增平台时，不再拆成 `posts.py` 和 `comments.py` 两个文件，而是新增一个统一脚本。

### 1. 新增平台脚本

示例：新增 `scripts/reddit.py`

脚本应提供：

- `parse_posts(html)`
- `parse_comments(html)`
- `fetch_full(urls=None)`

并通过命令行暴露：

- `python3 scripts/reddit.py posts --json`
- `python3 scripts/reddit.py comments --json`
- `python3 scripts/reddit.py full --json`

### 2. 在 `sources.json` 中加入平台配置

```json
"reddit": {
    "list_urls": [
        "https://www.reddit.com/r/programming/"
    ],
    "request_delay_seconds": 1.0
}
```

### 3. 对齐统一数据结构

新平台脚本必须遵循 `references/data-contract.md` 中的字段约定。

### 4. 更新 `SKILL.md`

在主技能文档里补充：

- 触发说明中是否纳入新平台
- 脚本入口用法
- 需要时更新输出排序或分类规则

## 验证方式

### 验证列表解析

```bash
bash scripts/fetch.sh "<列表页URL>" | python3 scripts/<platform>.py posts --json
```

### 验证详情解析

```bash
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/<platform>.py comments --json
```

### 验证完整抓取

```bash
python3 scripts/<platform>.py full --json
```

验证重点：

- URL 是否去重正确
- `article_content` 和评论 `content` 是否保留 Markdown 结构
- `reply_count` 是否合理
- 抓取间隔配置是否生效
