from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

import json
import os
import requests

ICON = "https://slate.com/media/sites/slate-com/icon.400x400.png"
URL = "https://slate.com/news-and-politics/jurisprudence"
HEADERS = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 '
        'Safari/605.1.15'
}


def log(message):
    now = datetime.now(ZoneInfo('America/New_York'))
    print(now.strftime('%Y-%m-%d %H:%M:%S') + " " + message)


# noinspection PyUnusedLocal
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Cache-Control': 'max-age=14400'},
        'body': get_json_feed(False)
    }


def sorter(el):
    return el["date_published"]


def get_json_feed(debug):
    log("HTTP Start " + URL)
    html = requests.get(URL, headers=HEADERS)
    log("HTTP End")

    if debug:
        post_file = open("data.html", "w")
        post_file.write(html.text)
        post_file.close()

    log("Parse Start")
    page = BeautifulSoup(html.text, 'html.parser')
    log("Parse End")

    feed_items = []
    for article in page.find_all('a', {'class': 'topic-story'}):
        article_url = article.get(key='href')
        current_soup = BeautifulSoup(requests.get(article_url).content, 'html.parser')
        current_body = current_soup.find('div', {'class': 'article__content'})

        for junk in (current_body("aside") + current_body('div', {'class': 'slate-ad__label'})
                     + current_body('div', {'class': 'social-share'})):
            junk.decompose()

        article_title = article.find_next('b', {'class': 'topic-story__hed'}).text.strip()
        article_author = article.find_next('span', {'class': 'topic-story__author'}).text
        article_body = str(current_body)
        article_date = current_soup.find('time').get(key='content')

        log(article_title)

        feed_article = {
            'id': article_url,
            'title': article_title,
            'authors': [{'name': article_author}],
            'url': article_url,
            'content_html': article_body,
            'date_published': article_date,
            'image': ICON,
            'banner_image': ICON,
        }
        feed_items.append(feed_article)

    feed = {
        'version': 'https://jsonfeed.org/version/1.1',
        'title': 'Slate Jurisprudence',
        'home_page_url': URL,
        'user_comment': 'Generated by https://github.com/prenagha/slate-jurisprudence-jsonfeed',
        'icon': ICON,
        'favicon': ICON,
        'items': sorted(feed_items, key=sorter, reverse=True)
    }
    log("END")
    return json.dumps(feed, indent=2)


def test_feed():
    log('TEST START')
    debug = 'LAMBDA_NAME' not in os.environ
    feed_str = get_json_feed(debug)
    if debug:
        feed_file = open("feed.json", "w")
        feed_file.write(feed_str)
        feed_file.close()
    assert ('date_published' in feed_str)
    log('TEST END')


if __name__ == '__main__':
    test_feed()
