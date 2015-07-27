import requests
from lxml import html

url = 'http://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?WORKSHOPEQUIPMENT_DETAIL=3&areaId=3&CATEGORY%2FMAINCATEGORY=8210&CATEGORY%2FSUBCATEGORY=8329&ISPRIVATE=1&PRICE_FROM=0&PRICE_TO=300'

def main():
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
