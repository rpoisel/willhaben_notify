import datetime
import logging
from logging.handlers import SysLogHandler

from wn_db import User, Subscription, SentOffer, Url
from crawl import WHCrawlFactory

class Scheduler(object):
    def __init__(self, telegram, dbsession):
        super().__init__()
        self.__logger = logging.getLogger('telegram')
        self.__logger.addHandler(SysLogHandler())
        self.__peers = None
        self.__dialogs = None
        self.__last = datetime.datetime.now()
        self.__telegram = telegram
        self.__dbsession = dbsession

    def tick(self):
        if not self.__telegram.isInitialized():
            return

        now = datetime.datetime.now()
        totalseconds = (now - self.__last).total_seconds()
        if totalseconds >= 1:
            self.__last = now
            self.schedule(now=now)

    def schedule(self, now):
        # iterate through subscriptions
        for user, subscription, subscription_url in self.__dbsession.query(User, Subscription, Url).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id).all():
            # determine which subscriptions have to be queried again
            if self.__isSubscriptionDue(now, subscription):
                # query relevant subscription pages
                crawler = WHCrawlFactory.getCrawler(subscription_url.location)
                self.__processOffers(crawler.crawl(), self.__dbsession, user, subscription)
                # update last_query to now
                subscription.last_query = now
                self.__dbsession.commit()

    def __processOffers(self, items, session, user, subscription):
        # iterate thorugh offers
        for offer in items:
            offer_url_id = self.__createUrlIfNotExists(session, offer.getUrl())
            # determine whether offer.getUrl() has already been sent
            if self.__hasOfferNotBeenSent(session, offer_url_id):
                # if no, send offer
                if False:
                    self.__telegram.send_msg(user.first_name, user.last_name, offer.getUrl())
                else:
                    self.__telegram.send_grpmsg(user.first_name, user.last_name, offer.getUrl())
                # and add to sent_offers
                session.add(SentOffer(user_id=subscription.user_id, url_id=offer_url_id))
                session.commit()

    def __createUrlIfNotExists(self, session, url):
        # determine whether offer.getUrl() exists in urls
        queryResult = session.query(Url).filter(Url.location == url)
        if queryResult.count() == 0:
            # if no, add to urls table
            newUrl = Url(location=url)
            session.add(newUrl)
            session.flush()
            return newUrl.id
        return queryResult.first().id

    def __hasOfferNotBeenSent(self, session, offer_url_id):
        return session.query(SentOffer, Subscription).filter(Subscription.user_id == SentOffer.user_id).filter(SentOffer.url_id == offer_url_id).count() == 0

    def __isSubscriptionDue(self, now, subscription):
        return subscription.last_query is None or (now - subscription.last_query).total_seconds() >= subscription.query_period


