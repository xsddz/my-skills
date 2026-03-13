---
name: wikitnow
description: '将本地目录或文件同步到飞书/Lark 知识库，自动创建层级 wiki 页面。用户说"发布到飞书"、"同步到知识库"、"上传 docs 目录"、"推送 markdown"时必须使用此技能。用户说"从飞书拉取"、"下载知识库文档"、"备份飞书文档"时也必须使用此技能。也适用于排查同步失败、配置凭证、配置排除规则等场景。'
---

# wikitnow

将本地目录或文件快速同步到飞书知识库，自动创建层级页面并渲染 Markdown 内容；也支持从飞书拉取文档为本地 Markdown 文件。

## 同步工作流（重要）

用户发起同步请求时，必须先预览、再确认、最后推送，不得跳步：

### 第一步：预览并请求确认

运行预览命令，将**完整输出原文**（一字不改）以代码块呈现给用户，并附上确认话术：

```bash
wikitnow sync <path>
```

预览完成后询问：**"以上内容确认推送到 `<target>`？"**

如果用户未提供目标 URL，此时一并询问。

### 第二步：推送

用户确认后，执行正式写入：

```bash
wikitnow sync <path> --target <url>
```

有 `--target` = 正式写入；无 `--target` = 安全预览。

## 命令参考

### 同步发布

```bash
wikitnow sync <path>                          # 预览模式（只读，不写入）
wikitnow sync <path> --target <url>           # 正式推送
wikitnow sync <path1> <path2> --target <url>  # 多路径推送
wikitnow sync <path> --target <url> --code-block=false  # 内容直接排版，不以代码块包裹
```

### 文档拉取

```bash
wikitnow pull <Wiki URL|docToken>                        # 预览：输出到控制台
wikitnow pull <Wiki URL|docToken> --output ./backup.md   # 保存到本地文件
wikitnow pull <Wiki URL|docToken> --output ./backup.md --force  # 覆盖已有文件
wikitnow pull <Wiki URL|docToken> --lang en              # 指定语言（zh/en/ja，默认 zh）
wikitnow pull <docToken> | grep "关键词"                 # 管道组合使用
```

### 凭证管理

```bash
wikitnow auth setup [--provider feishu]  # 配置凭证（交互式）
wikitnow auth check [--provider feishu]  # 验证凭证是否有效
```

凭证文件：`~/.wikitnow/config.json`；CI/CD 可用环境变量 `WIKITNOW_FEISHU_APP_ID` / `WIKITNOW_FEISHU_APP_SECRET`。

### 平台查看

```bash
wikitnow provider list  # 列出所有支持的知识库平台
```

### 配置管理

```bash
wikitnow config show-ignore                            # 查看当前生效的排除规则
wikitnow config init-ignore                            # 在当前目录生成 .wikitnow/ignore
wikitnow config init-ignore --force                    # 强制覆盖已有文件
wikitnow config init-ignore --dest ~/.wikitnow/ignore  # 指定输出路径（用户全局）
```

排除规则文件 `.wikitnow/ignore` 语法与 `.gitignore` 兼容，查找优先级（找到即停）：
1. `<同步目录>/.wikitnow/ignore` — 项目级
2. `<父目录>/.wikitnow/ignore` — 向上逐级查找
3. `~/.wikitnow/ignore` — 用户全局

> 隐藏文件（`.` 开头）始终被跳过，不受规则文件影响。

## 安装与配置

本技能依赖 `wikitnow` CLI：https://github.com/xsddz/wikitnow。

```bash
# 安装（macOS/Linux）
curl -fsSL https://raw.githubusercontent.com/xsddz/wikitnow/main/scripts/install.sh | bash

# 配置凭证（交互式）
wikitnow auth setup

# 验证凭证是否有效
wikitnow auth check
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 命令找不到（command not found） | 参考【安装与配置】章节完成安装 |
| 认证失败 | 运行 `wikitnow auth check` 验证凭证，或重新运行 `wikitnow auth setup` |
| 文件被跳过 | 运行 `wikitnow config show-ignore` 检查排除规则 |
| 目标 URL 无效 | 确认是飞书知识库节点链接（`https://…/wiki/…`） |
