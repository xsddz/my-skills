# 数据契约

本文档定义脚本输出的数据结构与字段含义。

## 帖子对象

`full` 命令返回帖子数组，每个元素结构如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str | 帖子标题 |
| `url` | str | 讨论页链接 |
| `article_url` | str\|null | 原文链接；HN 外链帖有值，V2EX 固定为 null |
| `article_content` | str\|null | 帖子正文，Markdown 格式 |
| `author` | str\|null | 作者 |
| `time` | str\|null | 发布时间 |
| `points` | int\|null | 点赞数；HN 为 int，V2EX 固定为 null |
| `reply_count` | int | 回复总数 |
| `comments` | list | 完整评论树（评论节点对象数组） |
| `platform` | str | 平台名称（`Hacker News` 或 `V2EX`） |

## 详情结果对象

`comments` 命令返回单条帖子的解析结果：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `title` | str\|null | 帖子标题 |
| `url` | str\|null | 讨论页链接 |
| `article_url` | str\|null | 原文链接 |
| `article_content` | str\|null | 帖子正文，Markdown 格式 |
| `reply_count` | int | 回复总数 |
| `comments` | list | 完整评论树（评论节点对象数组） |

## 评论节点对象

评论树中每个节点的结构：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | str | 评论 ID |
| `author` | str\|null | 评论作者 |
| `time` | str\|null | 评论时间 |
| `content` | str | 评论内容，Markdown 格式 |
| `replies` | list | 子评论数组，递归结构 |