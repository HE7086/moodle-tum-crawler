#!/usr/bin/env python3

import requests
import os
from urllib.parse import unquote
from lxml import etree

url = 'https://example.com'
targetFolder = 'downloads'


def save_file(folder, response):
    if not os.path.exists(folder):
        print('target folder not found, creating: ' + folder)
        os.makedirs(folder)
    filename = unquote(response.url.split('/')[-1].split('?')[0])
    filepath = os.path.join(targetFolder, filename)
    print('saving file: ' + filepath)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def parse_href(baseURL, href):
    if href[:7] in ['http://', 'https:/']:
        return href
    else:
        return baseURL + '/' + href


def crawl(folder, session, response):
    html = etree.HTML(response.text)
    links = html.xpath('//a/@href')
    rurl = response.url
    for link in links:
        if link == '../':
            continue
        r = session.get(parse_href(rurl, link))
        if r.headers['Content-Type'][:9] == 'text/html':
            crawl(os.path.join(folder, link.split('/')[-1]), session, r)
        else:
            save_file(folder, r)


def main():
    s = requests.Session()
    r = s.get(url)
    crawl(targetFolder, s, r)


if __name__ == '__main__':
    main()
