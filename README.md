# Deprecated
Moodle is updated with its own downloader, use that instead.

# moodle-tum-crawler
web crawler for moodle.tum.de  
use webdriver to bypass the shibboleth login system

## requirements
* python3
```
requests
lxml
selenium
```
* `chromedriver` or `geckodriver` must be in your `PATH`
    - note that for some versions of selenium, you also need to install `firefox` itself in order to use its driver
```
# Arch Linux
sudo pacman -S chromium geckodriver

# debian based Linux
sudo apt install chromium-chromedriver firefox-geckodriver

# MacOS
brew install --cask chromedriver
brew install geckodriver

# Windows
idk
```

## usage
### [moodle Crawler](./moodleCrawler.py)
> v2 update: complete refactor

```
usage: moodleCrawler.py [-h] [-u USERNAME] [-p PASSWORD] [-o DEST] [-d DRIVER] [-e EXTS] [-a] [-f] [--dry-run] [--overwrite] [courses ...]

Webcrawler for Moodle

positional arguments:
  courses               list of IDs of the target courses

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        username for login
  -p PASSWORD, --password PASSWORD
                        password for login
  -o DEST, --output DEST
                        location of output folder (default: pwd)
  -d DRIVER, --driver DRIVER
                        webdriver use to bypass login system (default: chrome, alternative: firefox)
  -e EXTS, --exts EXTS  comma separated list of extensions to download (default: pdf only)
  -a, --all             download all files
  -f, --force           force download all the hyperlinks, useful for courses that do not use standard template
  --dry-run             do not actually download the file
  --overwrite           overwrite local file if it exists already
```

You can either specify your credentials through commandline arguments or enter them later during the execution

#### course ID
* In order to find the ID of a course, you need to first open the moodle page of that course
* the course ID is then at the end of the url, likely a 5-digit number
* e.g. if the url of the course page is `https://www.moodle.tum.de/course/view.php?id=12345`, then its ID is 12345

#### example
* download all PDFs from course 12345 while specifying credentials in the command line
```
$ python3 moodleCrawler.py -u ge12abc -p password 12345
```
* download all files from course 12345 and 67890, store them in the folder "downloads"
```
$ python3 moodleCrawler.py -a -o downloads 12345 67890
```
* download all mp4 files using firefox (note the extension format)
```
$ python3 moodleCrawler.py -e .mp4 -d firefox 12345
```
* try download all the files from a course that uses non-standard template
```
$ python3 moodleCrawler.py -a -f 12345
```

### [simple http crawler](./simpleHTTPcrawler.py)
crawl the files on the simple http file server, recursively
> ./simpleHTTPcrawler.py
#### configuration
* set the url and targetFolder in the file
```
url = 'https://example.com'
targetFolder = 'downloads'
```

#### known issue
* sometimes ssl certificates cannot be verified
