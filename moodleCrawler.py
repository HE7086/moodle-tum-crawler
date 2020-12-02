#!/usr/bin/env python3

import requests
import os
import time
from urllib.parse import unquote
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

username = 'ge12abc'
password = '12345'
courseID = '67890'
targetFolder = 'downloads'
fileExtensions = ['.pdf', '.zip', '.tar.gz']

url = 'https://www.moodle.tum.de/?lang=en'
courseURL = 'https://www.moodle.tum.de/course/view.php'
count = 0
size = 0


# save the file from response to given folder
def save_file(folder, response):
    global count
    global size
    filename = unquote(response.url.split('/')[-1].split('?')[0])
    _, extension = os.path.splitext(filename)
    if extension in fileExtensions or not fileExtensions:
        filepath = os.path.join(folder, filename)
        print('saving file: ' + filepath)
        with open(filepath, 'wb') as file:
            file.write(response.content)
        count += 1
        size += os.path.getsize(filepath)
    else:
        print('skip the file: ' + filename)


# set up the web driver
chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

startTime = time.time()

# login
print('Login ', end='', flush=True)
driver.get(url)
print('. ', end='', flush=True)
driver.find_element_by_link_text('With TUM ID').click()
print('. ', end='', flush=True)
driver.find_element_by_id('username').send_keys(username)
driver.find_element_by_id('password').send_keys(password)
print('. ', end='', flush=True)
driver.find_element_by_id('btnLogin').click()
if driver.current_url[8:13] == 'login':
    print('Login Failed! please check your credentials!')
    exit()
else:
    print('Login Successful')
    print('=' * 20)

loginTime = time.time()

# crawl
s = requests.Session()
for c in driver.get_cookies():
    s.cookies.set(c['name'], c['value'])

coursePage = s.get(courseURL, params={'id': courseID})
html = etree.HTML(coursePage.text)
title = unquote(html.xpath('/html/head/title/text()')[0])

if title in ['Error', 'Fehler']:
    print('Course ID not found')
    exit()

print('crawling course: ' + title)
links = html.xpath('//*[@class="aalink"]')

if not os.path.exists(targetFolder):
    print('target folder not found, creating: ' + targetFolder)
    os.makedirs(targetFolder)

# download files
for link in links:
    r = s.get(link.xpath('@href')[0])
    # simple files
    if 'resource' in r.url:
        save_file(targetFolder, r)
    # folders, not recursive
    elif 'folder' in r.url:
        folder = os.path.join(targetFolder, unquote(link.xpath('span/text()')[0]))
        if not os.path.exists(folder):
            print('creating: folder' + folder)
            os.makedirs(folder)

        for ln in etree.HTML(r.text).xpath('//*[@class="fp-filename-icon"]/a/@href'):
            save_file(folder, s.get(ln))
# folders on main site
for link in html.xpath('//*[@class="fp-filename-icon"]/a/@href'):
    save_file(targetFolder, s.get(link))

downloadTime = time.time()

# statistics
print('=' * 20)
print('-->crawling complete<--')
print('files downloaded:    {}'.format(count))
print('bytes downloaded:    {}'.format(size))
print('average speed:       {}'.format(size / (downloadTime - loginTime)))
print('time elapsed:        {}s'.format(downloadTime - startTime))
print('login time usage:    {}s'.format(loginTime - startTime))
print('download time usage: {}s'.format(downloadTime - loginTime))
