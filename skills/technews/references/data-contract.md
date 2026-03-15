# 数据契约

本文档定义 `technews` 技能各脚本的统一输出字段，便于后续聚合、排序、翻译和详情展示。

## 设计原则

- 顶层字段尽量统一，平台差异通过 `null` 或额外字段表达
- 正文和评论内容统一输出为 Markdown 字符串
- `full` 模式返回的帖子对象应是“可直接展示”的完整数据结构

## 帖子对象

每篇帖子在 `full` 结果中的标准结构如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str | 帖子标题 |
| `url` | str | 讨论页链接；当前也是聚合去重依据 |
| `article_url` | str\|null | 原文链接；V2EX 通常为 `null`，HN 外链帖通常有值 |
| `article_content` | str\|null | 帖子原文正文，使用 Markdown 表达 |
| `author` | str\|null | 作者 |
| `time` | str\|null | 发布时间 |
| `points` | int\|null | 点赞数；HN 有值，V2EX 通常为 `null` |
| `reply_count` | int | 列表页中的回复数 |
| `last_reply_by` | str\|null | 最后回复人；V2EX 常见，HN 通常为 `null` |
| `comments` | list | 完整评论树 |
| `platform` | str | 平台名称 |
| `total_comments` | int | 根评论数量 |
| `total_replies` | int | 嵌套回复总数 |

### 平台扩展字段

允许保留平台特有字段，但不能替代通用字段。

例如：

- HN 可保留 `item_id`
- 未来 V2EX 若补充节点、标签、点击数，也应作为额外字段存在

## 评论节点对象

评论树中的每个节点结构如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | str | 评论 ID |
| `author` | str\|null | 评论作者 |
| `time` | str\|null | 评论时间 |
| `content` | str | 评论内容，使用 Markdown 表达 |
| `replies` | list | 子评论数组，递归结构 |

## Markdown 内容语义

`article_content` 与评论 `content` 不是普通纯文本，而是 Markdown 字符串。渲染目标：在文本环境中尽量保留原始结构。

应保留的元素：

- 段落
- 空行
- `br` 换行
- `blockquote` 引用
- `pre/code` 代码块
- 链接
- 图片
- 分隔线

### 示例 1：普通链接

HTML：

```html
<a href="https://example.com">example</a>
```

Markdown：

```md
[example](https://example.com)
```

### 示例 2：链接文本本身就是 URL

HTML：

```html
<a href="https://example.com">https://example.com</a>
```

Markdown：

```md
https://example.com
```

### 示例 3：纯图片内容

HTML：

```html
<a href="https://i.imgur.com/demo.png"><img src="https://i.imgur.com/demo.png"></a>
```

Markdown：

```md
![](https://i.imgur.com/demo.png)
```

## 聚合约定

- 平台内按 `url` 去重
- 概览生成阶段使用通用字段，不依赖平台特有字段
- 详情展示阶段优先使用 `article_content`、`comments`、`total_comments`、`total_replies`