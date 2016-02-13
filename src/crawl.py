import random
import re

import requests
from lxml import html


class WHItem(object):

    def __init__(self, element):
        super().__init__()
        self.__text = element.find(".//span").text.strip()
        self.__url = element.find_class('info-1 w-brk ln-2')[0].attrib['href']
        self.__imgUrl = element.find_class('image media-object')[0].attrib['src']

    def getText(self):
        return self.__text

    def getUrl(self):
        return "http://www.willhaben.at" + self.__url

    def getImgUrl(self):
        return self.__imgUrl

    def __repr__(self, *args, **kwargs):
        return self.__text + "@" + self.__url + "<" + self.__imgUrl + ">"


class CrawlerBase(object):

    USER_AGENTS = [
                  'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
                  'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
                  'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
                  'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
                  'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
                  'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36'
                  ]

    PROXIES_DICT = {
                   "http"  : 'http://localhost:8118',
                   "https" : 'http://localhost:8118'
                   }

    def __init__(self, url):
        super().__init__()
        self._url = url

    def __makeRequest(self):
        try:
            httpHeaders = {'User-Agent': random.choice(CrawlerBase.USER_AGENTS)}
            return requests.get(self._url, headers=httpHeaders, proxies=CrawlerBase.PROXIES_DICT).text
        except:
            return ''

    def __getElements(self, pageSource):
        tree = html.fromstring(pageSource)
        return tree.xpath(self._getElementsXpath())

    def _getElementsXpath(self):
        raise Exception('Not implemented')

    def _getItemClass(self):
        raise Exception('Not implemented')

    def getShortestValidPeriod(self):
        return 7200

    def crawl(self):
        items = []
        pageSource = self.__makeRequest()
        elements = self.__getElements(pageSource)
        ItemClass = self._getItemClass()
        for element in elements:
            items.append(ItemClass(element))
        return items


class WHCrawler(CrawlerBase):

    def __init__(self, url):
        super().__init__(url)

    def _getElementsXpath(self):
        return '//li[contains(@class, "media")]'

    def _getItemClass(self):
        return WHItem


class WHCrawlFactory(object):

    CRAWLERS = { 'www.willhaben.at' : WHCrawler }
    FQDN_REGEX = re.compile("https?://([^/]+)")

    @staticmethod
    def crawlerExists(url):
        return WHCrawlFactory.__getBaseUrl(url) in WHCrawlFactory.CRAWLERS

    @staticmethod
    def isCrawlingPeriodValid(url, period):
        try:
            crawler = WHCrawlFactory.getCrawler(url)
            return period > crawler.getShortestValidPeriod()
        except Exception as exc:
            return False

    @staticmethod
    def getCrawler(url):
        if not WHCrawlFactory.crawlerExists(url):
            raise Exception("Unsupported URL")
        return WHCrawlFactory.CRAWLERS[WHCrawlFactory.__getBaseUrl(url)](url)

    @staticmethod
    def __getBaseUrl(url):
        match = WHCrawlFactory.FQDN_REGEX.search(url)
        if match is None:
            raise Exception('Invalid URL given.')
        return match.group(1)


def main():
    url = 'http://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?WORKSHOPEQUIPMENT_DETAIL=3&areaId=3&CATEGORY%2FMAINCATEGORY=8210&CATEGORY%2FSUBCATEGORY=8329&ISPRIVATE=1&PRICE_FROM=0&PRICE_TO=300'
    try:
        if not WHCrawlFactory.crawlerExists(url):
            print('Crawler does not exist.')
            return
        crawler = WHCrawlFactory.getCrawler(url)
        for offer in crawler.crawl():
            print('"' + offer.getText() + '" @ ' + offer.getUrl() + ", " + offer.getImgUrl())
    except Exception as err:
        print("Error: {0}".format(err))

if __name__ == "__main__":
    main()
