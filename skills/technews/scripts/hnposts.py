#!/usr/bin/env python3
"""
Hacker News 提取脚本
从 HN 首页提取帖子信息（标题、链接、作者、时间、点赞、评论数）
"""

import sys
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def parse_hn(html):
    """解析 Hacker News 首页"""
    soup = BeautifulSoup(html, 'html.parser')
    posts = []

    # HN 的帖子行是 <tr class="athing submission">
    rows = soup.find_all('tr', class_='athing')

    for row in rows:
        # 标题和链接
        titleline = row.find('span', class_='titleline')
        if not titleline:
            continue
        title_el = titleline.find('a')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        article_url = title_el.get('href', '')

        # 帖子 ID（用于构造 HN 讨论页）
        item_id = row.get('id', '')
        discussion_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id else article_url

        # 下一行包含元数据（subtext）
        subtext = row.find_next_sibling('tr')
        if not subtext:
            continue
        subtext = subtext.find('td', class_='subtext')
        if not subtext:
            continue

        # 作者
        author_el = subtext.find('a', href=re.compile(r'user\?id='))
        author = author_el.get_text(strip=True) if author_el else ''

        # 时间 (age span, 优先取 title 属性中的绝对时间)
        age_el = subtext.find('span', class_='age')
        time_str = ''
        if age_el:
            if age_el.get('title'):
                time_str = age_el['title'].strip()
            else:
                # 相对时间如 "3 hours ago"
                time_str = age_el.get_text(strip=True)

        # 点赞数
        score_el = subtext.find('span', class_='score')
        points = 0
        if score_el:
            score_text = score_el.get_text(strip=True)
            match = re.search(r'(\d+)', score_text)
            if match:
                points = int(match.group(1))

        # 评论数
        comments = 0
        # HN 的评论链接通常在同一 subtext 中，格式："| <a href="item?id=XXX">NNN&nbsp;comments</a>"
        comment_links = subtext.find_all('a', href=re.compile(r'item\?id='))
        for link in comment_links:
            txt = link.get_text(strip=True)
            if 'comment' in txt:
                # 提取数字
                m = re.search(r'(\d+)', txt.replace('&nbsp;', ' '))
                if m:
                    comments = int(m.group(1))
                    break

        # 时间格式化：将 "2026-02-28T10:41:55 1772275315" 转为 "YYYY-MM-DD HH:MM:SS +08:00"
        time_formatted = ''
        if time_str:
            iso_part = time_str.split()[0]  # "2026-02-28T10:41:55"
            dt = iso_part.replace('T', ' ')
            time_formatted = f"{dt} +08:00"

        # HN 讨论页链接（用于获取评论）
        discussion_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id else article_url

        posts.append({
            'title': title,
            'url': discussion_url,  # 帖子讨论页链接（用于获取评论）
            'article_url': article_url,  # 原文链接（外部来源）
            'item_id': item_id,
            'author': author,
            'time': time_formatted,
            'points': points,
            'reply_count': comments,
            'last_reply_by': None,
            'comments': [],
            'platform': 'Hacker News'
        })

    return posts

def main():
    if len(sys.argv) < 2:
        print('Usage: python hnextract.py <html_file|-> [--json]', file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    if source == '-':
        html = sys.stdin.read()
    else:
        with open(source, 'r', encoding='utf-8') as f:
            html = f.read()

    posts = parse_hn(html)

    if '--json' in sys.argv:
        print(json.dumps(posts, ensure_ascii=False, indent=2))
    else:
        print(f'✅ 提取到 {len(posts)} 个 HN 帖子\n')
        for i, p in enumerate(posts[:15], 1):
            print(f"{i}. {p['title']}")
            print(f"   链: {p['url']}")
            print(f"   作者: {p['author'] or '(未知)'}")
            print(f"   时间: {p['time'] or '(未知)'}")
            print(f"   点赞: {p['points']} | 评论: {p['reply_count']}")
            print()

if __name__ == '__main__':
    main()
