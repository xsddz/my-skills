#!/usr/bin/env python3
import sys
import json
import re
from bs4 import BeautifulSoup

def parse_v2ex(html):
    soup = BeautifulSoup(html, 'html.parser')
    posts = []
    
    # 定位所有 <div class="cell item">
    for cell in soup.select('div.cell.item'):
        # 标题链接
        title_tag = cell.select_one('a.topic-link')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        url = title_tag.get('href')
        if url and not url.startswith('http'):
            url = 'https://www.v2ex.com' + url
        
        # topic_info
        topic_info = cell.select_one('span.topic_info')
        if not topic_info:
            continue
        
        # 作者
        author_tag = topic_info.select_one('strong > a')
        author = author_tag.get_text(strip=True) if author_tag else None
        
        # 节点
        node_tag = topic_info.select_one('a.node')
        node = node_tag.get_text(strip=True) if node_tag else None
        
        # 时间
        time = None
        time_tag = topic_info.select_one('span[title]')
        if time_tag:
            time = time_tag.get('title', '').strip()
        else:
            # 相对时间如 "2分钟前"
            for span in topic_info.select('span'):
                txt = span.get_text(strip=True)
                if re.match(r'\d+分钟前|\d+小时前|\d+天前', txt):
                    time = txt
                    break
        
        # 回复数
        replies_tag = cell.select_one('a.count_livid')
        replies = int(replies_tag.get_text(strip=True)) if replies_tag else 0
        
        # 最后回复人（可选）
        last_reply_by = None
        # 查找包含"最后回复来自"的文本节点
        for elem in topic_info.descendants:
            if isinstance(elem, str) and '最后回复来自' in elem:
                # 找到这个字符串后，下一个 <strong><a> 就是最后回复人
                parent = elem.parent
                if parent:
                    strong = parent.find_next('strong')
                    if strong:
                        a_tag = strong.find('a')
                        if a_tag:
                            last_reply_by = a_tag.get_text(strip=True)
                break
        
        posts.append({
            'title': title,
            'url': url,  # 帖子主题页链接（用于获取评论）
            'article_url': None,  # V2EX 帖子通常无外部原文链接
            'author': author,
            'time': time,  # V2EX 已经是 "YYYY-MM-DD HH:MM:SS +08:00"
            'points': None,
            'reply_count': replies,
            'last_reply_by': last_reply_by,
            'comments': [],
            'platform': 'V2EX'
        })
    
    return posts

def main():
    if len(sys.argv) < 2:
        print('Usage: python v2extract.py <html_file|-> [--json]', file=sys.stderr)
        print('  <html_file>: HTML 文件路径 或 "-" 表示从 stdin 读取', file=sys.stderr)
        sys.exit(1)
    
    source = sys.argv[1]
    if source == '-':
        html = sys.stdin.read()
    else:
        with open(source, 'r', encoding='utf-8') as f:
            html = f.read()
    
    posts = parse_v2ex(html)
    
    if '--json' in sys.argv:
        print(json.dumps(posts, ensure_ascii=False, indent=2))
    else:
        print(f'✅ 提取到 {len(posts)} 个帖子\n')
        for i, p in enumerate(posts[:10], 1):
            print(f"{i}. {p['title']}")
            print(f"   链: {p['url']}")
            print(f"   作者: {p['author'] or '(未知)'}")
            print(f"   时间: {p['time'] or '(未知)'}")
            print(f"   回复: {p['reply_count']}", end='')
            if p['last_reply_by']:
                print(f" | 最后回复: {p['last_reply_by']}")
            else:
                print()

if __name__ == '__main__':
    main()