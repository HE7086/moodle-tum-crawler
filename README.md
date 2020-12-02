# moodle-tum-crawler
web crawler for moodle.tum.de  
use webdriver to bypass the shibboleth login system

## requirements
```
requests
lxml
selenium
```

## usage
### [moodle Crawler](./moodleCrawler.py)
download all the files on the moodle page / in a folder of the main moodle page  
note that if the page uses some none-default styles, the script won't work
> ./moodleCrawler.py
#### configuration
* set you username and password in the code
```
username = 'ge12abc'
password = '12345'
```
* set the course ID in the code. you can get the course ID by opening the course page in a browser and look at its url, the number at the end of it is the ID we want (which is likely 5 digits)
```
courseID = '12345'
```
* set the folder to download, by default is `./downloads`
```
targetFolder = 'downloads'
```
* set the file extension filter. Only files with given extensions will be downloaded. If the list is empty, all the files will be downloaded.
```
fileExtensions = ['.pdf', '.zip', '.tar.gz']
```
#### miscellaneous
* `url` and `courseURL` should be the same for everyone
* make sure chrome/chromium is installed and the executable is in the `PATH`
* if you want to use firefox or other browers, just modify the webdriver

### [simple http crawler](./simpleHTTPcrawler.py)
crawl the files on the simple http file server, recursively
> ./simpleHTTPcrawler.py
#### configuration
* set the url and targetFolder, just like above
```
url = 'https://example.com'
targetFolder = 'downloads'
```

#### known issue
* sometimes ssl certificates cannot be verified
