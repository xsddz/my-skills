---
name: wikitnow
description: '将本地目录或文件同步到飞书/Lark 知识库，自动创建层级 wiki 页面。用户说"发布到飞书"、"同步到知识库"、"上传 docs 目录"、"推送 markdown"时必须使用此技能。也适用于排查同步失败、配置凭证、配置排除规则等场景。'
---

# wikitnow

将本地目录或文件快速同步到飞书知识库，自动创建层级页面并渲染 Markdown 内容。

## 前置条件

本技能依赖 `wikitnow` CLI：https://github.com/xsddz/wikitnow。
若尚未安装，运行：

```bash
curl -fsSL https://raw.githubusercontent.com/xsddz/wikitnow/main/scripts/install.sh | bash
```

安装后运行 `wikitnow auth check` 确认凭证有效；若未配置，运行 `wikitnow auth setup` 完成初始化。

## 同步工作流（重要）

用户首次发起同步请求时，**必须先执行预览，再请求确认，最后才执行正式推送**：

1. **预览**：运行 `wikitnow sync <path>`，将命令的完整输出原文展示给用户，不要归纳或省略
2. **确认**：询问用户 "以上内容确认推送到 `<target>`？"
3. **推送**：用户确认后，运行 `wikitnow sync <path> --target <url>` 执行正式写入

如果用户首次请求时未提供目标 URL，在预览完成后一并询问。

## 命令参考

### 同步发布

```bash
wikitnow sync <path>                          # 预览模式（只读，不写入）
wikitnow sync <path> --target <url>           # 正式推送
wikitnow sync <path1> <path2> --target <url>  # 多路径推送
wikitnow sync <path> --target <url> --code-block=false  # 纯文本上传（不用代码块包裹）
```

> **关键**：有 `--target` = 正式写入；无 `--target` = 安全预览。不存在 `--apply` 标志。

### 凭证管理

```bash
wikitnow auth setup              # 配置凭证（交互式）
wikitnow auth check              # 验证凭证是否有效
```

凭证文件：`~/.wikitnow/config.json`；CI/CD 可用环境变量 `WIKITNOW_FEISHU_APP_ID` / `WIKITNOW_FEISHU_APP_SECRET`。

### 配置管理

```bash
wikitnow config show-ignore                          # 查看当前生效的排除规则
wikitnow config init-ignore                          # 在当前目录生成 .wikitnow/ignore
wikitnow config init-ignore --force                  # 强制覆盖已有文件
wikitnow config init-ignore --dest ~/.wikitnow/ignore  # 指定输出路径（用户全局）
```

排除规则文件 `.wikitnow/ignore` 语法与 `.gitignore` 兼容，查找优先级（找到即停）：
1. `<同步目录>/.wikitnow/ignore` — 项目级
2. `<父目录>/.wikitnow/ignore` — 向上逐级查找
3. `~/.wikitnow/ignore` — 用户全局
4. `/usr/local/etc/wikitnow/ignore` — 系统默认

> 隐藏文件（`.` 开头）始终被跳过，不受规则文件影响。

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 认证失败 | 运行 `wikitnow auth check` 验证凭证 |
| 文件被跳过 | 运行 `wikitnow config show-ignore` 检查排除规则 |
| 目标 URL 无效 | 确认是飞书知识库节点链接（`https://…/wiki/…`） |
