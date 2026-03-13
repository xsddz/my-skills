#!/usr/bin/env python3
"""
HN 详情页评论解析器
从 HN 讨论页（item?id=...）提取嵌套评论树
"""

import sys
import json
import re
from bs4 import BeautifulSoup

def extract_comment_id(tr):
    """从 tr 的 id 提取 comment ID（如 com_abc123）"""
    return tr.get('id', '').replace('com_', '')

def extract_indent_level(tr):
    """从 td.ind 的 indent 属性提取缩进级别（0,1,2...）"""
    indent_td = tr.find('td', class_='ind')
    if indent_td and indent_td.has_attr('indent'):
        try:
            return int(indent_td['indent'])
        except:
            return 0
    return 0

def extract_author(tr):
    """提取评论作者"""
    a_tag = tr.find('a', class_='hnuser')
    return a_tag.get_text(strip=True) if a_tag else None

def extract_time(tr):
    """提取评论时间（绝对时间）"""
    age_span = tr.find('span', class_='age')
    if not age_span:
        return None
    # 优先取 title 属性（通常是 "2025-03-08T14:48:51 1741445331"）
    if age_span.get('title'):
        title = age_span['title'].strip()
        # 提取 ISO 部分（YYYY-MM-DDTHH:MM:SS）
        iso_match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', title)
        if iso_match:
            dt = iso_match.group().replace('T', ' ')
            return f"{dt} +08:00"
        # 否则直接返回
        return title
    # 否则取文本（相对时间，暂不转换）
    return age_span.get_text(strip=True)

def extract_content(tr):
    """提取评论内容（commtext  div）"""
    commtext = tr.find('div', class_='commtext')
    if not commtext:
        return ''
    return commtext.get_text(strip=True)

def count_replies(comments):
    """递归统计所有回复数量"""
    total = 0
    for c in comments:
        total += len(c['replies'])
        if c['replies']:
            total += count_replies(c['replies'])
    return total

def extract_title(soup):
    """从 <title> 提取标题，去掉 'Hacker News: ' 前缀"""
    title_tag = soup.find('title')
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)
    prefix = 'Hacker News: '
    if title.startswith(prefix):
        title = title[len(prefix):]
    return title

def extract_canonical_url(soup):
    """从 <link rel='canonical'> 提取讨论页 URL"""
    link = soup.find('link', rel='canonical')
    if link and link.get('href'):
        return link['href']
    return None

def extract_article_url(soup):
    """尝试从页面中提取外部原文链接"""
    # HN 页面通常在标题行有一个链接指向外部文章
    # 查找 class='titleline' 内的 <a> 且 href 不是以 / 开头的（即外部链接）
    titleline = soup.find('span', class_='titleline')
    if titleline:
        a = titleline.find('a')
        if a and a.get('href') and not a['href'].startswith('/'):
            return a['href']
    # 也可以从 meta 标签尝试
    meta = soup.find('meta', property='og:url')
    if meta and meta.get('content'):
        url = meta['content']
        # 如果 og:url 就是讨论页，则返回 canonical
        if 'news.ycombinator.com/item' in url:
            return None
        return url
    return None

def parse_hn_comments(html):
    """解析 HN 详情页，返回嵌套评论树"""
    soup = BeautifulSoup(html, 'html.parser')
    comment_rows = soup.find_all('tr', class_='comtr')

    if not comment_rows:
        return []

    # 临时存储扁平评论（使用 _level 作为内部字段）
    flat = []
    for row in comment_rows:
        cid = extract_comment_id(row)
        level = extract_indent_level(row)
        author = extract_author(row)
        time_str = extract_time(row)
        content = extract_content(row)
        flat.append({
            'id': cid,
            '_level': level,  # 内部用
            'author': author,
            'time': time_str,
            'content': content,
            'replies': []  # 稍后填充
        })

    # 用栈重建树
    roots = []
    stack = []  # [(_level, comment_dict)]

    for c in flat:
        level = c['_level']
        # 弹出所有 >= 当前 level 的栈项
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1]['replies'].append(c)
        else:
            roots.append(c)
        stack.append((level, c))

    # 清理内部字段
    for node in flat:
        node.pop('_level', None)

    return roots

def main():
    if len(sys.argv) < 2:
        print('Usage: python hnitem.py <html_file|-> [--json]', file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    if source == '-':
        html = sys.stdin.read()
    else:
        with open(source, 'r', encoding='utf-8') as f:
            html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    comments = parse_hn_comments(html)

    if '--json' in sys.argv:
        total_replies = count_replies(comments)
        result = {
            'title': extract_title(soup),
            'url': extract_canonical_url(soup),
            'article_url': extract_article_url(soup),
            'total_comments': len(comments),
            'total_replies': total_replies,
            'comments': comments
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'✅ 提取到 {len(comments)} 条根评论\n')
        for i, c in enumerate(comments[:5], 1):
            print(f"{i}. @{c['author']} ({c['time']})")
            print(f"   {c['content'][:80]}{'...' if len(c['content']) > 80 else ''}")
            print(f"   ↳ {len(c['replies'])} 条回复")
            print()

if __name__ == '__main__':
    main()
