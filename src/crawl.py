import random

import requests
from lxml import html


class Offer(object):

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


class WHCrawl(object):

    userAgents = [
                  'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
                  'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
                  'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
                  'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
                  'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
                  'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36'
                  ]

    def __init__(self, url):
        super().__init__()
        httpHeaders = {'User-Agent': random.choice(WHCrawl.userAgents)}
        page = requests.get(url, headers=httpHeaders)
        tree = html.fromstring(page.text)
        elements = tree.xpath('//li[contains(@class, "media")]')
        self.__offers = []
        for element in elements:
            self.__offers.append(Offer(element))

    def getOffers(self):
        return self.__offers


def main():
    url = 'http://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?WORKSHOPEQUIPMENT_DETAIL=3&areaId=3&CATEGORY%2FMAINCATEGORY=8210&CATEGORY%2FSUBCATEGORY=8329&ISPRIVATE=1&PRICE_FROM=0&PRICE_TO=300'
    page = requests.get(url)
    tree = html.fromstring(page.text)
    offers = tree.xpath('//li[contains(@class, "media")]')
    for offer in offers:
        offer_text = offer.find(".//span").text
        offer_url = offer.find_class('info-1 w-brk ln-2')[0].attrib['href']
        offer_img = offer.find_class('image media-object')[0].attrib['src']
        print('"' + offer_text.strip() + '" @ http://www.willhaben.at' + offer_url + ", " + offer_img)

if __name__ == "__main__":
    main()
