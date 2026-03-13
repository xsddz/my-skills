# 添加新数据源指南

本文档说明如何为 `tech-news` 技能添加新的平台支持。

## 概览

需要实现以下脚本（可选）：

- **`<platform>posts.py`** - 列表解析器，输出帖子数组
- **`<platform>comments.py`** - 详情解析器，输出单帖评论树（用于详情层）

## 输入规范

脚本接受单个参数：
- `<html_file>` - HTML 文件路径
- 或 `-` - 从 stdin 读取

用法：
```bash
python3 <platform>posts.py <文件或->
python3 <platform>comments.py <文件或->
```

## 输出规范

### 列表输出结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str | 帖子标题 |
| `url` | str | 帖子讨论页链接 |
| `article_url` | str\|null | 外部原文链接（无则 `null`） |
| `author` | str | 作者 |
| `time` | str | 发布时间（`YYYY-MM-DD HH:MM:SS +08:00`） |
| `points` | int\|null | 点赞数（无则 `null`） |
| `reply_count` | int | 评论数 |
| `last_reply_by` | str\|null | 最后回复人（无则 `null`） |
| `comments` | list | 评论列表（应返回 `[]`） |
| `platform` | str | 平台名称 |

输出为 JSON 数组（多个帖子）。

### 详情输出结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str | 帖子标题 |
| `url` | str | 讨论页 URL |
| `article_url` | str\|null | 外部原文链接 |
| `total_comments` | int | 根评论数量 |
| `total_replies` | int | 嵌套回复总数 |
| `comments` | list | 嵌套评论树（`id, author, time, content, replies[]`） |

输出为单个 JSON 对象。

## 极简模板

### 列表解析器

```python
#!/usr/bin/env python3
import sys, json
from bs4 import BeautifulSoup

def parse_platform(html):
    soup = BeautifulSoup(html, 'html.parser')
    # TODO: 提取 posts 数组
    return posts

def main():
    src = sys.argv[1]
    html = sys.stdin.read() if src == '-' else open(src).read()
    posts = parse_platform(html)
    print(json.dumps(posts, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
```

### 详情解析器

```python
#!/usr/bin/env python3
import sys, json
from bs4 import BeautifulSoup

def parse_platform_comments(html):
    soup = BeautifulSoup(html, 'html.parser')
    # TODO: 提取 title, url, article_url, comments 树
    return {
        'title': ...,
        'url': ...,
        'article_url': ...,
        'total_comments': ...,
        'total_replies': ...,
        'comments': ...
    }

def main():
    src = sys.argv[1]
    html = sys.stdin.read() if src == '-' else open(src).read()
    result = parse_platform_comments(html)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
```

## 参考实现

- 列表：`scripts/hnposts.py`, `scripts/v2exposts.py`
- 详情：`scripts/hncomments.py`, `scripts/v2excomments.py`

## 更新文档

在 `SKILL.md` 的 `## URL 获取` 下添加新平台的列表页 URL。
