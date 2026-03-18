#!/usr/bin/env python3
"""
Hacker News 脚本
用法:
  posts    - 从列表页 HTML 提取帖子列表（配合 fetch.sh 使用）
  comments - 从详情页 HTML 提取评论树（配合 fetch.sh 使用）
  full     - 自动抓取所有列表页并批量获取评论，输出完整数据集

示例:
  bash scripts/fetch.sh "https://news.ycombinator.com" | python3 scripts/hn.py posts --json
  bash scripts/fetch.sh "https://news.ycombinator.com/item?id=43213940" | python3 scripts/hn.py comments --json
  python3 scripts/hn.py full --json
  python3 scripts/hn.py full --json --output "technews/.<批次基准>-HN.json"
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
SITE_BASE = 'https://news.ycombinator.com'


def _load_source_config():
    default = {
        'list_urls': ["https://news.ycombinator.com"],
        'request_delay_seconds': 0.0,
    }
    try:
        with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = data.get('hn', {})
        return {
            'list_urls': config.get('list_urls') or default['list_urls'],
            'request_delay_seconds': float(config.get('request_delay_seconds', 0.0) or 0.0),
        }
    except Exception:
        return default


# ─────────────────────────── posts ───────────────────────────

def parse_posts(html):
    """解析 HN 列表页，返回帖子列表"""
    soup = BeautifulSoup(html, 'html.parser')
    posts = []

    rows = soup.find_all('tr', class_='athing')

    for row in rows:
        titleline = row.find('span', class_='titleline')
        if not titleline:
            continue
        title_el = titleline.find('a')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        article_url = title_el.get('href', '')

        item_id = row.get('id', '')

        subtext = row.find_next_sibling('tr')
        if not subtext:
            continue
        subtext = subtext.find('td', class_='subtext')
        if not subtext:
            continue

        author_el = subtext.find('a', href=re.compile(r'user\?id='))
        author = author_el.get_text(strip=True) if author_el else ''

        age_el = subtext.find('span', class_='age')
        time_str = ''
        if age_el:
            if age_el.get('title'):
                time_str = age_el['title'].strip()
            else:
                time_str = age_el.get_text(strip=True)

        score_el = subtext.find('span', class_='score')
        points = 0
        if score_el:
            m = re.search(r'(\d+)', score_el.get_text(strip=True))
            if m:
                points = int(m.group(1))

        comments = 0
        for link in subtext.find_all('a', href=re.compile(r'item\?id=')):
            txt = link.get_text(strip=True)
            if 'comment' in txt:
                m = re.search(r'(\d+)', txt.replace('\xa0', ' '))
                if m:
                    comments = int(m.group(1))
                    break

        time_formatted = ''
        if time_str:
            iso_part = time_str.split()[0]
            time_formatted = f"{iso_part.replace('T', ' ')} +08:00"

        discussion_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id else article_url

        posts.append({
            'title': title,
            'url': discussion_url,
            'article_url': article_url,
            'article_content': None,
            'item_id': item_id,
            'author': author,
            'time': time_formatted,
            'points': points,
            'reply_count': comments,
            'last_reply_by': None,
            'comments': [],
            'platform': 'Hacker News',
        })

    return posts


# ─────────────────────────── comments ───────────────────────────

def _extract_comment_id(tr):
    return tr.get('id', '').replace('com_', '')

def _extract_indent_level(tr):
    indent_td = tr.find('td', class_='ind')
    if indent_td and indent_td.has_attr('indent'):
        try:
            return int(indent_td['indent'])
        except Exception:
            return 0
    return 0

def _extract_author(tr):
    a = tr.find('a', class_='hnuser')
    return a.get_text(strip=True) if a else None

def _extract_time(tr):
    age_span = tr.find('span', class_='age')
    if not age_span:
        return None
    if age_span.get('title'):
        title = age_span['title'].strip()
        m = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', title)
        if m:
            return f"{m.group().replace('T', ' ')} +08:00"
        return title
    return age_span.get_text(strip=True)

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

def _extract_content(tr):
    commtext = tr.find('div', class_='commtext')
    if not commtext:
        return ''
    return _render_content(commtext)

def _count_replies(comments):
    total = 0
    for c in comments:
        total += len(c['replies'])
        if c['replies']:
            total += _count_replies(c['replies'])
    return total

def _extract_title(soup):
    title_tag = soup.find('title')
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)
    prefix = 'Hacker News: '
    return title[len(prefix):] if title.startswith(prefix) else title

def _extract_canonical_url(soup):
    link = soup.find('link', rel='canonical')
    if link and link.get('href'):
        return link['href']
    return None

def _extract_article_url(soup):
    titleline = soup.find('span', class_='titleline')
    if titleline:
        a = titleline.find('a')
        if a and a.get('href') and not a['href'].startswith('/'):
            return a['href']
    return None

def _extract_article_content(soup):
    toptext = soup.find('div', class_='toptext')
    if not toptext:
        return None
    text = _render_content(toptext)
    return text or None


def parse_comments(html):
    """解析 HN 详情页，返回评论结果 dict"""
    soup = BeautifulSoup(html, 'html.parser')
    comment_rows = soup.find_all('tr', class_='comtr')

    flat = []
    for row in comment_rows:
        flat.append({
            'id': _extract_comment_id(row),
            '_level': _extract_indent_level(row),
            'author': _extract_author(row),
            'time': _extract_time(row),
            'content': _extract_content(row),
            'replies': [],
        })

    roots = []
    stack = []
    for c in flat:
        level = c['_level']
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1]['replies'].append(c)
        else:
            roots.append(c)
        stack.append((level, c))

    for node in flat:
        node.pop('_level', None)

    return {
        'title': _extract_title(soup),
        'url': _extract_canonical_url(soup),
        'article_url': _extract_article_url(soup),
        'article_content': _extract_article_content(soup),
        'reply_count': len(roots),
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
        except Exception as e:
            print(f"    跳过: {e}", file=sys.stderr)
            p.setdefault('comments', [])

    return posts


# ─────────────────────────── main ───────────────────────────

def _read_input(source):
    if source == '-':
        return sys.stdin.read()
    with open(source, 'r', encoding='utf-8') as f:
        return f.read()


def _extract_output_path(args):
    output_path = None
    cleaned_args = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in ('-o', '--output'):
            if i + 1 >= len(args):
                print('参数错误: --output 需要文件路径', file=sys.stderr)
                sys.exit(2)
            output_path = args[i + 1]
            i += 2
            continue
        cleaned_args.append(token)
        i += 1
    return cleaned_args, output_path


def _emit_json(data, output_path=None, pretty=False):
    text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
    if output_path:
        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'✅ JSON 已保存: {output_path}', file=sys.stderr)
        return
    print(text)


def main():
    args = sys.argv[1:]
    args, output_path = _extract_output_path(args)
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    subcmd = args[0]
    as_json = '--json' in args
    if output_path:
        as_json = True

    if subcmd == 'posts':
        source = args[1] if len(args) > 1 and not args[1].startswith('-') else '-'
        html = _read_input(source)
        posts = parse_posts(html)
        if as_json:
            _emit_json(posts, output_path, pretty=True)
        else:
            print(f'✅ 提取到 {len(posts)} 个 HN 帖子\n')
            for i, p in enumerate(posts[:15], 1):
                print(f"{i}. {p['title']}")
                print(f"   链: {p['url']}")
                print(f"   作者: {p['author'] or '(未知)'}  时间: {p['time'] or '(未知)'}")
                print(f"   点赞: {p['points']} | 评论: {p['reply_count']}")
                print()

    elif subcmd == 'comments':
        source = args[1] if len(args) > 1 and not args[1].startswith('-') else '-'
        html = _read_input(source)
        result = parse_comments(html)
        if as_json:
            _emit_json(result, output_path, pretty=True)
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
            _emit_json(posts, output_path, pretty=False)
        else:
            print(f'✅ 完整抓取完成，共 {len(posts)} 篇帖子')

    else:
        print(f'未知子命令: {subcmd}', file=sys.stderr)
        print('可用子命令: posts | comments | full', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
