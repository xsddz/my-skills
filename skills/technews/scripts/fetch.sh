#!/usr/bin/env bash
# fetch.sh - 通用 HTML 抓取工具
# 用法: ./fetch.sh <URL> [output_file]
# 如果提供第二个参数，保存到文件；否则输出到 stdout

set -e

URL="${1:?错误: 请提供 URL 参数}"
OUTPUT="${2:-}"

# 模拟真实浏览器的请求头
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
ACCEPT_LANGUAGE="zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
REFERER="https://www.google.com/"

# 抓取 HTML
HTML=$(curl -s \
  -A "$USER_AGENT" \
  -H "Accept: $ACCEPT" \
  -H "Accept-Language: $ACCEPT_LANGUAGE" \
  -H "Referer: $REFERER" \
  --compressed \
  "$URL")

# 输出
if [ -n "$OUTPUT" ]; then
  echo "$HTML" > "$OUTPUT"
  echo "✅ 已保存至: $OUTPUT"
else
  echo "$HTML"
fi
