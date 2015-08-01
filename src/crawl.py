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

    def __init__(self, url):
        super().__init__()
        page = requests.get(url)
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
