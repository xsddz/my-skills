#!/usr/bin/env python3
"""
V2EX 详情页评论解析器
从 V2EX 主题页（/t/<ID>）提取嵌套评论树
"""

import sys
import json
import re
from bs4 import BeautifulSoup

def extract_comment_id(div):
    """提取评论 ID（从 id 属性，格式通常为 r_12345）"""
    div_id = div.get('id', '')
    if div_id.startswith('r_'):
        return div_id[2:]  # 去掉 "r_" 前缀
    return div_id or ''

def extract_floor_number(div):
    """提取楼层号（从 <span class="no"> 元素）"""
    # 在整条评论范围内查找
    no_span = div.find('span', class_='no')
    if no_span:
        try:
            return int(no_span.get_text(strip=True))
        except:
            return None
    return None

def extract_parent_id(div):
    """提取父评论 ID（从 data-reply-to 属性）"""
    return div.get('data-reply-to', '')

def extract_author(div):
    """提取评论作者"""
    strong = div.find('strong')
    if not strong:
        return None
    a_tag = strong.find('a')
    return a_tag.get_text(strip=True) if a_tag else strong.get_text(strip=True)

def extract_time(div):
    """提取评论时间（绝对时间）"""
    # 寻找 <span class="ago" title="..."> 或 <span class="ago"> 中的绝对时间
    ago_span = div.find('span', class_='ago')
    if not ago_span:
        return None
    # 优先取 title（ISO 或标准格式）
    if ago_span.get('title'):
        time_str = ago_span['title'].strip()
        # 规范化到 YYYY-MM-DD HH:MM:SS +08:00
        if 'T' in time_str:
            dt = time_str.replace('T', ' ').split('.')[0]
            return f"{dt} +08:00"
        return time_str
    # 中文相对时间如 "2分钟前" 暂不转换
    return ago_span.get_text(strip=True)

def extract_content(div):
    """提取评论内容（class="reply_content" 的 div）"""
    content_div = div.find('div', class_='reply_content')
    if not content_div:
        return ''
    # 保留文本，移除不必要的元素（如图片占位符）
    for unwanted in content_div.select('div.topic_assets, a.imessage'):
        unwanted.decompose()
    return content_div.get_text(strip=True)

def count_replies(comments):
    """递归统计所有回复数量"""
    total = 0
    for c in comments:
        total += len(c['replies'])
        if c['replies']:
            total += count_replies(c['replies'])
    return total

def extract_title(soup):
    """从 <title> 提取标题，去掉 'V2EX » ' 等前缀"""
    title_tag = soup.find('title')
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)
    for prefix in ('V2EX » ', 'V2EX | ', 'V2EX - '):
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    return title

def extract_canonical_url(soup):
    """从 <link rel='canonical'> 提取讨论页 URL"""
    link = soup.find('link', rel='canonical')
    if link and link.get('href'):
        return link['href']
    return None

def parse_v2ex_comments(html):
    """解析 V2EX 详情页，返回嵌套评论树"""
    soup = BeautifulSoup(html, 'html.parser')
    # 评论容器：<div id="r_12345" class="cell">
    comment_divs = soup.find_all('div', id=re.compile(r'^r_\d+$'), class_='cell')

    if not comment_divs:
        return []

    # 第一遍：收集所有评论，映射 floor -> node
    floor_to_node = {}
    roots = []

    for div in comment_divs:
        cid = extract_comment_id(div)
        floor = extract_floor_number(div)
        author = extract_author(div)
        time_str = extract_time(div)
        content = extract_content(div)

        node = {
            'id': cid,
            'author': author,
            'time': time_str,
            'content': content,
            'replies': []
        }
        if floor is not None:
            floor_to_node[floor] = node
        roots.append(node)  # 先全部加入根，后面再根据 parent_floor 调整

    # 第二遍：确定父子关系
    # V2EX 在 reply_content 中通过 "@用户名 #楼层" 表示对某条评论的回复
    for node in roots[:]:  # 复制列表以便修改
        content = node['content']
        # 匹配 @...#N（允许 HTML 标签残留，但通过 get_text 已清除）
        match = re.search(r'@[^\n#]*#(\d+)', content)
        if match:
            try:
                parent_floor = int(match.group(1))
            except:
                continue
            if parent_floor in floor_to_node:
                parent_node = floor_to_node[parent_floor]
                if node in roots:
                    roots.remove(node)
                parent_node['replies'].append(node)

    return roots

def main():
    if len(sys.argv) < 2:
        print('Usage: python v2exitem.py <html_file|-> [--json]', file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    if source == '-':
        html = sys.stdin.read()
    else:
        with open(source, 'r', encoding='utf-8') as f:
            html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    comments = parse_v2ex_comments(html)

    if '--json' in sys.argv:
        total_replies = count_replies(comments)
        result = {
            'title': extract_title(soup),
            'url': extract_canonical_url(soup),
            'article_url': None,  # V2EX 通常无外部原文链接
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
