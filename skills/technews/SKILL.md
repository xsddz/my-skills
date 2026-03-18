---
name: technews
description: 获取 Hacker News 和 V2EX 的技术社区动态，生成概览文档，并在用户按序号或 URL 追问时生成详情文档。用户提到“看看今天 HN 有什么”“V2EX 最近有啥”“帮我刷一下技术新闻”“整理成文档”“把这些热点发我”“根据上面的序号展开讲讲”“帮我看看这个帖子”“展开这条”等场景时都应使用本技能，即使用户没有明确提到 technews。
---

# Tech News

聚合 Hacker News 和 V2EX 热门帖子，先生成概览文档，再按用户选择生成详情文档。

## 任务目录与命名

- 所有产物统一存放在 `technews/` 目录（不存在则创建）
- 概览批次命名基准：`YYYY-MM-DD-HHMMSS-PLATFORM`
- 隐藏数据文件：`technews/.YYYY-MM-DD-HHMMSS-PLATFORM.json`
- 概览文档：`technews/YYYY-MM-DD-HHMMSS-PLATFORM.md`
- 详情文档：`technews/YYYY-MM-DD-HHMMSS-PLATFORM-NN.md`

## 核心工作流

### 阶段一：抓取并生成概览

每次进入阶段一都视为一次新的资讯获取请求，重新抓取最新数据。

1. 根据用户意图确定平台范围：只提 HN 就只抓 HN，只提 V2EX 就只抓 V2EX，未指定则两个都抓。
2. 以当前时间戳和平台标识确定本批次命名基准：`YYYY-MM-DD-HHMMSS-PLATFORM`（单平台如 `<批次基准>-HN`，双平台如 `<批次基准>-HN-V2EX`）。
3. 对每个平台使用完整抓取命令，并直接输出到该批次隐藏 JSON 文件：
   - HN：`python3 scripts/hn.py full --json --output "technews/.YYYY-MM-DD-HHMMSS-HN.json"`
   - V2EX：`python3 scripts/v2ex.py full --json --output "technews/.YYYY-MM-DD-HHMMSS-V2EX.json"`
   - 双平台合并基准：`technews/.YYYY-MM-DD-HHMMSS-HN-V2EX.json`
4. 基于步骤 3 得到的帖子数据，按平台分别聚类（不跨平台混合），分类名贴近当批内容的实际主题。
5. 按 [references/output-format.md](references/output-format.md) 规定的内容结构与翻译方式，将聚类结果生成概览文档，保存为 `technews/YYYY-MM-DD-HHMMSS-PLATFORM.md`。
6. 将概览文档的完整内容发送给用户。

### 阶段二：生成详情文档

1. 用户回复序号（对应概览中的全局编号，支持多个）或直接提供帖子 URL。
2. 按序号从概览文档中定位帖子的讨论页 URL；用户直接提供 URL 时直接使用。
3. 用 URL 在对应概览的隐藏 JSON 文件中查找完整帖子数据。未命中或文件不存在时，根据 URL 判断平台并重新抓取，并将结果写入临时详情数据文件：
   - HN：`bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/hn.py comments --json --output "technews/.<批次基准>-HN-<NN>.detail.json"`
   - V2EX：`bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/v2ex.py comments --json --output "technews/.<批次基准>-V2EX-<NN>.detail.json"`
4. 基于步骤 3 命中的帖子数据或临时详情数据，按 [references/output-format.md](references/output-format.md) 规定的内容结构与翻译方式生成详情文档。
5. 将详情文档保存到 `technews/` 目录，文件命名为 `YYYY-MM-DD-HHMMSS-PLATFORM-NN.md`（NN 为两位全局序号，时间戳沿用概览的命名基准；无概览时使用当前时间戳）。
6. 将本次生成的详情文档完整内容发送给用户。

## 命令参考

调试解析结果或扩展数据源时，参阅 [references/adding-sources.md](references/adding-sources.md)。

### Hacker News

```bash
python3 scripts/hn.py full --json --output "technews/.<批次基准>-HN.json"
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/hn.py comments --json --output "technews/.<批次基准>-HN-<NN>.detail.json"
```

### V2EX

```bash
python3 scripts/v2ex.py full --json --output "technews/.<批次基准>-V2EX.json"
bash scripts/fetch.sh "<讨论页URL>" | python3 scripts/v2ex.py comments --json --output "technews/.<批次基准>-V2EX-<NN>.detail.json"
```

## 参考文档

- [references/output-format.md](references/output-format.md)：概览与详情模板、翻译规则、展示要求
- [references/data-contract.md](references/data-contract.md)：统一字段约定与输出数据结构
- [references/adding-sources.md](references/adding-sources.md)：数据源配置、抓取频率、扩展新平台
