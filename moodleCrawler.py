#!/usr/bin/env python3

import argparse
import asyncio
import getpass
import logging
import os
import requests
import time

from lxml import etree
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def setup_driver(driver) -> WebDriver:
    """
    Setting up the webdriver
    :param driver: name of the webdriver to use, either chrome or firefox
    :return: the corresponding webdriver in headless mode
    """
    if driver == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless")
        return webdriver.Chrome(options=options)
    elif driver == "firefox":
        options = FirefoxOptions()
        options.add_argument("-headless")
        return webdriver.Firefox(options=options)
    else:
        raise RuntimeError(f"Unknown webdriver: {driver}")


def login(driver: WebDriver, username: str, password: str) -> list[dict[str, str]]:
    """
    Login into the Moodle system
    :param driver: generated webdriver
    :param username: username
    :param password: password
    :return: session cookies if successfully logged in
    """
    url = "https://www.moodle.tum.de/?lang=en"
    driver.get(url)
    driver.find_element(by="link text", value="With TUM ID").click()
    driver.find_element(by="id", value="username").send_keys(username)
    driver.find_element(by="id", value="password").send_keys(password)
    driver.find_element(by="id", value="btnLogin").click()
    if driver.current_url == "https://login.tum.de/idp/profile/SAML2/Redirect/SSO?execution=e1s1":
        time.sleep(1)
    if driver.current_url != "https://www.moodle.tum.de/my/":
        print(driver.current_url)
        raise RuntimeError("Login Failed! check your credentials!")
    else:
        logging.debug("Login Succeeded")
        return driver.get_cookies()


def download_file(session: requests.Session, url: str, output: str, args):
    """
    Download a single file
    :param session: the request session to use (for cookies)
    :param url: url of the file
    :param output: folder to store the file
    :param args: commandline arguments
    :return: None
    """
    r = session.head(url)
    if 'location' in r.headers:
        name = r.headers['location'].rsplit('/', 1)[-1]
    else:
        name = r.url.rsplit('/', 1)[-1].rsplit('?', 1)[0]
    name = unquote(name)
    _, ext = os.path.splitext(name)
    if ext in args.exts or len(args.exts) == 0:
        path = os.path.join(output, name)
        if not args.dryrun:
            r = session.get(url)
            if os.path.exists(path) and not args.overwrite:
                logging.info(f"{path} already exists! Use --overwrite to force download")
            else:
                with open(path, 'wb') as f:
                    f.write(r.content)
        logging.info(f"Downloaded file: {path}")
    else:
        logging.info(f"Skipping file: {name}")


def download_page(session: requests.Session, name: str, url: str, args, pattern: str, loop):
    """
    Parse and download the links in a page that matches the pattern
    :param session: the request session to use (for cookies)
    :param name: folder name to store the downloads
    :param url: url of the page
    :param args: command line arguments
    :param pattern: xpath for choosing the elements
    :param loop: event loop to run the file downloader
    :return: None
    """
    logging.debug(f"Downloading page: {url}")
    # I'm too lazy to implement a recursive downloader, as no course use that many folders
    path = os.path.join(args.output, unquote(name[0])) if len(name) > 0 else args.output
    if not os.path.exists(path) and not args.dryrun:
        logging.debug(f"Creating subfolder: {path}")
        os.makedirs(path)

    r = session.get(url)
    for lnk in etree.HTML(r.text).xpath(pattern):
        loop.run_in_executor(None, download_file, session, lnk, path, args)


def download_course(session, course, args):
    """
    Parse and download the files for a given course
    :param session: the request session to use (for cookies)
    :param course: the course ID to be parsed
    :param args: command line arguments
    :return: None
    """
    course_url = "https://www.moodle.tum.de/course/view.php"
    page = session.get(course_url, params={'id': course})
    html = etree.HTML(page.text)
    loop = asyncio.new_event_loop()

    title = unquote(html.xpath("/html/head/title/text()")[0])
    if title in ["Error", "Fehler"]:
        raise RuntimeError(f"Failed to find course {course}")

    logging.info(f"Downloading course {course}: {title}")
    links = html.xpath('//*[@class="aalink"]') + html.xpath('//a[@class="fp-filename-icon"]/@href') + \
        html.xpath('//div[@class="summary"]/div[@class="no-overflow"]/p/a')
    for link in links:
        r = session.head(link.xpath("@href")[0])
        name = link.xpath('span/text()')
        if "resource" in r.url:
            loop.run_in_executor(None, download_file, session, r.url, args.output, args)
        elif "folder" in r.url:
            download_page(session, name, r.url, args, '//*[@class="fp-filename-icon"]/a/@href', loop)
        elif "assign" in r.url:
            download_page(session, name, r.url, args, '//*[@class="fileuploadsubmission"]/a/@href', loop)
        elif "course/section" in r.url:
            loop.run_in_executor(None, download_file, session, r.url, args.output, args)

    # try download all the links
    if args.force:
        for link in html.xpath('//a'):
            try:
                name = link.xpath('span/text()')
                r = session.head(link.xpath("@href")[0])
                download_page(session, name, r.url, args, '//a/@href', loop)
            except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema):
                pass


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Webcrawler for Moodle")
    parser.add_argument("-u", "--username", dest="username", metavar="USERNAME", type=str, nargs=1,
                        help="username for login")
    parser.add_argument("-p", "--password", dest="password", metavar="PASSWORD", type=str, nargs=1,
                        help="password for login")
    parser.add_argument("-o", "--output", dest="output", metavar="DEST", type=str, nargs=1, default=".",
                        help="location of output folder (default: pwd)")
    parser.add_argument("-d", "--driver", dest="driver", metavar="DRIVER", type=str, nargs=1, default="chrome",
                        help="webdriver use to bypass login system (default: chrome, alternative: firefox)")
    parser.add_argument("-e", "--exts", dest="exts", metavar="EXTS", type=str, nargs=1,
                        help="comma separated list of extensions to download (default: pdf only)")
    parser.add_argument("-a", "--all", dest="exts_all", action="store_true",
                        help="download all files")
    parser.add_argument("-f", "--force", dest="force", action="store_true",
                        help="force download all the hyperlinks, useful for courses that do not use standard template")
    parser.add_argument("--dry-run", dest="dryrun", action="store_true",
                        help="do not actually download the file")
    parser.add_argument("--overwrite", dest="overwrite", action="store_true",
                        help="overwrite local file if it exists already")
    parser.add_argument("courses", metavar="courses", type=str, nargs="*",
                        help="list of IDs of the target courses")
    args = parser.parse_args()

    if len(args.courses) == 0:
        parser.print_help()
        exit()

    if args.exts:
        args.exts = args.exts.split(",")
    else:
        args.exts = [".pdf"]

    if args.exts_all:
        args.exts = []

    if args.username == "" or args.username is None or args.password == "" or args.password is None:
        args.username = input("Username: ")
        args.password = getpass.getpass()

    driver = setup_driver(args.driver[-1] if isinstance(args.driver, list) else args.driver)
    cookies = login(driver, args.username, args.password)
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie["name"], cookie["value"])

    if not os.path.exists(args.output) and not args.dryrun:
        logging.info(f"Output folder not exist, creating: {args.output}")
        os.makedirs(args.output)

    for course in args.courses:
        download_course(s, course, args)

    driver.close()


if __name__ == "__main__":
    main()
