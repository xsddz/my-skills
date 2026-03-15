#!/usr/bin/env python3
"""
V2EX 脚本
用法:
  posts    - 从列表页 HTML 提取帖子列表（配合 fetch.sh 使用）
  comments - 从详情页 HTML 提取评论树（配合 fetch.sh 使用）
  full     - 自动抓取所有列表页并批量获取评论，输出完整数据集

示例:
  bash scripts/fetch.sh "https://www.v2ex.com/?tab=tech" | python3 scripts/v2ex.py posts --json
  bash scripts/fetch.sh "https://www.v2ex.com/t/1234567" | python3 scripts/v2ex.py comments --json
  python3 scripts/v2ex.py full --json
"""

import sys
import json
import re
import subprocess
import os
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4 import NavigableString, Tag

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(BASE, 'sources.json')
SITE_BASE = 'https://www.v2ex.com'


def _load_source_config():
    default = {
        'list_urls': [
            "https://www.v2ex.com/?tab=tech",
            "https://www.v2ex.com/?tab=hot",
            "https://www.v2ex.com/?tab=all",
        ],
        'request_delay_seconds': 0.0,
    }
    try:
        with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = data.get('v2ex', {})
        return {
            'list_urls': config.get('list_urls') or default['list_urls'],
            'request_delay_seconds': float(config.get('request_delay_seconds', 0.0) or 0.0),
        }
    except Exception:
        return default


# ─────────────────────────── posts ───────────────────────────

def parse_posts(html):
    """解析 V2EX 列表页，返回帖子列表"""
    soup = BeautifulSoup(html, 'html.parser')
    posts = []

    for cell in soup.select('div.cell.item'):
        title_tag = cell.select_one('a.topic-link')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        url = title_tag.get('href')
        if url and not url.startswith('http'):
            url = 'https://www.v2ex.com' + url

        topic_info = cell.select_one('span.topic_info')
        if not topic_info:
            continue

        author_tag = topic_info.select_one('strong > a')
        author = author_tag.get_text(strip=True) if author_tag else None

        time_val = None
        time_tag = topic_info.select_one('span[title]')
        if time_tag:
            time_val = time_tag.get('title', '').strip()
        else:
            for span in topic_info.select('span'):
                txt = span.get_text(strip=True)
                if re.match(r'\d+分钟前|\d+小时前|\d+天前', txt):
                    time_val = txt
                    break

        replies_tag = cell.select_one('a.count_livid')
        replies = int(replies_tag.get_text(strip=True)) if replies_tag else 0

        last_reply_by = None
        for elem in topic_info.descendants:
            if isinstance(elem, str) and '最后回复来自' in elem:
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
            'url': url,
            'article_url': None,
            'article_content': None,
            'author': author,
            'time': time_val,
            'points': None,
            'reply_count': replies,
            'last_reply_by': last_reply_by,
            'comments': [],
            'platform': 'V2EX',
        })

    return posts


# ─────────────────────────── comments ───────────────────────────

def _extract_comment_id(div):
    div_id = div.get('id', '')
    return div_id[2:] if div_id.startswith('r_') else div_id

def _extract_floor_number(div):
    no_span = div.find('span', class_='no')
    if no_span:
        try:
            return int(no_span.get_text(strip=True))
        except Exception:
            return None
    return None

def _extract_author(div):
    strong = div.find('strong')
    if not strong:
        return None
    a_tag = strong.find('a')
    return a_tag.get_text(strip=True) if a_tag else strong.get_text(strip=True)

def _extract_time(div):
    ago_span = div.find('span', class_='ago')
    if not ago_span:
        return None
    if ago_span.get('title'):
        time_str = ago_span['title'].strip()
        if 'T' in time_str:
            dt = time_str.replace('T', ' ').split('.')[0]
            return f"{dt} +08:00"
        return time_str
    return ago_span.get_text(strip=True)

def _normalize_content_text(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _absolute_url(href):
    if not href:
        return href
    return urljoin(SITE_BASE, href)

def _render_content(node):
    if node is None:
        return ''

    def render_inline(current):
        if isinstance(current, NavigableString):
            return str(current)

        if not isinstance(current, Tag):
            return ''

        if current.name == 'br':
            return '\n'

        if current.name == 'img':
            src = _absolute_url(current.get('src'))
            return f'![]({src})' if src else ''

        if current.name == 'a':
            href = _absolute_url(current.get('href'))
            text = ''.join(render_inline(child) for child in current.children).strip()
            if not href:
                return text
            if not text:
                return href
            if text == href:
                return href
            return f'[{text}]({href})'

        if current.name == 'code' and current.parent and current.parent.name != 'pre':
            text = ''.join(render_inline(child) for child in current.children).strip()
            return f'`{text}`' if text else ''

        return ''.join(render_inline(child) for child in current.children)

    def render_block(current, quote_level=0):
        if isinstance(current, NavigableString):
            return str(current)

        if not isinstance(current, Tag):
            return ''

        if current.name == 'blockquote':
            inner = _normalize_content_text(''.join(render_block(child, quote_level + 1) for child in current.children))
            if not inner:
                return ''
            prefix = '> ' * (quote_level + 1)
            return '\n'.join(f'{prefix}{line}' if line else prefix.rstrip() for line in inner.split('\n')) + '\n\n'

        if current.name == 'pre':
            code_tag = current.find('code')
            code_text = code_tag.get_text('\n', strip=False) if code_tag else current.get_text('\n', strip=False)
            return f'```\n{code_text.rstrip()}\n```\n\n'

        if current.name == 'hr':
            return '\n---\n\n'

        if current.name in ('p', 'div', 'section', 'article', 'li'):
            text = _normalize_content_text(''.join(render_block(child, quote_level) for child in current.children))
            if not text:
                return ''
            if current.name == 'li':
                return f'- {text}\n'
            return f'{text}\n\n'

        if current.name in ('ul', 'ol'):
            items = ''.join(render_block(child, quote_level) for child in current.children)
            return f'{items}\n' if items else ''

        if current.name == 'code':
            return render_inline(current)

        return ''.join(render_inline(child) for child in current.children)

    markdown = ''.join(render_block(child) for child in node.children)
    if not markdown.strip():
        markdown = render_inline(node)
    return _normalize_content_text(markdown)

def _extract_content(div):
    content_div = div.find('div', class_='reply_content')
    if not content_div:
        return ''
    for unwanted in content_div.select('div.topic_assets, a.imessage'):
        unwanted.decompose()
    return _render_content(content_div)

def _count_replies(comments):
    total = 0
    for c in comments:
        total += len(c['replies'])
        if c['replies']:
            total += _count_replies(c['replies'])
    return total

def _extract_title(soup):
    topic_title = soup.select_one('#Main .header h1')
    if topic_title:
        return topic_title.get_text(strip=True)

    title_tag = soup.find('title')
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)
    for prefix in ('V2EX » ', 'V2EX | ', 'V2EX - '):
        if title.startswith(prefix):
            return title[len(prefix):]
    suffix = ' - V2EX'
    if title.endswith(suffix):
        return title[:-len(suffix)]
    return title

def _extract_canonical_url(soup):
    link = soup.find('link', rel='canonical')
    if link and link.get('href'):
        return link['href']
    return None

def _extract_article_content(soup):
    topic_content = soup.select_one('#Main > .box .cell .topic_content')
    if not topic_content:
        return None
    text = _render_content(topic_content)
    return text or None


def parse_comments(html):
    """解析 V2EX 详情页，返回评论结果 dict"""
    soup = BeautifulSoup(html, 'html.parser')
    comment_divs = soup.find_all('div', id=re.compile(r'^r_\d+$'), class_='cell')

    if not comment_divs:
        return {
            'title': _extract_title(soup),
            'url': _extract_canonical_url(soup),
            'article_url': None,
            'article_content': _extract_article_content(soup),
            'total_comments': 0,
            'total_replies': 0,
            'comments': [],
        }

    floor_to_node = {}
    roots = []

    for div in comment_divs:
        floor = _extract_floor_number(div)
        node = {
            'id': _extract_comment_id(div),
            'author': _extract_author(div),
            'time': _extract_time(div),
            'content': _extract_content(div),
            'replies': [],
        }
        if floor is not None:
            floor_to_node[floor] = node
        roots.append(node)

    for node in roots[:]:
        m = re.search(r'@[^\n#]*#(\d+)', node['content'])
        if m:
            try:
                parent_floor = int(m.group(1))
            except Exception:
                continue
            if parent_floor in floor_to_node:
                parent_node = floor_to_node[parent_floor]
                if node in roots:
                    roots.remove(node)
                parent_node['replies'].append(node)

    total_replies = _count_replies(roots)
    return {
        'title': _extract_title(soup),
        'url': _extract_canonical_url(soup),
        'article_url': None,
        'article_content': _extract_article_content(soup),
        'total_comments': len(roots),
        'total_replies': total_replies,
        'comments': roots,
    }


# ─────────────────────────── full ───────────────────────────

def _fetch_html(url):
    result = subprocess.run(
        ["bash", "scripts/fetch.sh", url],
        capture_output=True, text=True, timeout=30, cwd=BASE
    )
    return result.stdout


def fetch_full(urls=None):
    """抓取所有列表页并批量获取评论，返回完整帖子数组"""
    config = _load_source_config()
    if urls is None:
        urls = config['list_urls']
    delay_seconds = config['request_delay_seconds']

    seen, posts = set(), []
    for index, url in enumerate(urls):
        if index > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        html = _fetch_html(url)
        for p in parse_posts(html):
            if p['url'] not in seen:
                seen.add(p['url'])
                posts.append(p)

    print(f"[full] 共 {len(posts)} 篇帖子，开始批量抓取评论...", file=sys.stderr)
    for i, p in enumerate(posts):
        print(f"  [{i+1}/{len(posts)}] {p['title'][:60]}", file=sys.stderr)
        try:
            if i > 0 and delay_seconds > 0:
                time.sleep(delay_seconds)
            html = _fetch_html(p['url'])
            data = parse_comments(html)
            p['article_url'] = data.get('article_url', p.get('article_url'))
            p['article_content'] = data.get('article_content', p.get('article_content'))
            p['comments'] = data.get('comments', [])
            p['total_comments'] = data.get('total_comments', 0)
            p['total_replies'] = data.get('total_replies', 0)
        except Exception as e:
            print(f"    跳过: {e}", file=sys.stderr)
            p.setdefault('comments', [])
            p.setdefault('total_comments', 0)
            p.setdefault('total_replies', 0)

    return posts


# ─────────────────────────── main ───────────────────────────

def _read_input(source):
    if source == '-':
        return sys.stdin.read()
    with open(source, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    subcmd = args[0]
    as_json = '--json' in args

    if subcmd == 'posts':
        source = args[1] if len(args) > 1 and not args[1].startswith('-') else '-'
        html = _read_input(source)
        posts = parse_posts(html)
        if as_json:
            print(json.dumps(posts, ensure_ascii=False, indent=2))
        else:
            print(f'✅ 提取到 {len(posts)} 个帖子\n')
            for i, p in enumerate(posts[:10], 1):
                print(f"{i}. {p['title']}")
                print(f"   链: {p['url']}")
                print(f"   作者: {p['author'] or '(未知)'}  时间: {p['time'] or '(未知)'}")
                print(f"   回复: {p['reply_count']}", end='')
                if p['last_reply_by']:
                    print(f" | 最后回复: {p['last_reply_by']}")
                else:
                    print()
                print()

    elif subcmd == 'comments':
        source = args[1] if len(args) > 1 and not args[1].startswith('-') else '-'
        html = _read_input(source)
        result = parse_comments(html)
        if as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            comments = result.get('comments', [])
            print(f'✅ 提取到 {len(comments)} 条根评论\n')
            for i, c in enumerate(comments[:5], 1):
                print(f"{i}. @{c['author']} ({c['time']})")
                content = c['content']
                print(f"   {content[:80]}{'...' if len(content) > 80 else ''}")
                print(f"   ↳ {len(c['replies'])} 条回复")
                print()

    elif subcmd == 'full':
        posts = fetch_full()
        if as_json:
            print(json.dumps(posts, ensure_ascii=False))
        else:
            print(f'✅ 完整抓取完成，共 {len(posts)} 篇帖子')

    else:
        print(f'未知子命令: {subcmd}', file=sys.stderr)
        print('可用子命令: posts | comments | full', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
