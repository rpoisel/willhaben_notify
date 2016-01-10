from time import sleep
import datetime
import logging
from logging import StreamHandler
from logging.handlers import SysLogHandler
from threading import Event

from crawl import WHCrawlFactory
from wn_db import User, Subscription, SentOffer, Url


class Scheduler(object):
    def __init__(self, db, telegram):
        super().__init__()
        self.__logger = logging.getLogger('telegram')
        syslogHandler = StreamHandler()
        syslogHandler.setLevel(logging.INFO)
        self.__logger.addHandler(syslogHandler)

        self.__db = db
        self.__telegram = telegram

        self.__event = Event()
        self.__event.set()

    def shutdown(self):
        self.__event.clear()

    def run(self):
        dbSession = self.__db.getSession()

        while self.__event.is_set():
            self.processSubscriptions(dbSession)
            self.processUpdates(dbSession)
            sleep(1)

        dbSession.close()

    def processSubscriptions(self, dbSession):
        now = datetime.datetime.now()
        # iterate through subscriptions
        for user, subscription, subscription_url in dbSession.query(User, Subscription, Url).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id).all():
            # determine which subscriptions have to be queried again
            if self.__isSubscriptionDue(now, subscription):
                # query relevant subscription pages
                crawler = WHCrawlFactory.getCrawler(subscription_url.location)
                self.__processOffers(crawler.crawl(), dbSession, user, subscription)
                # update last_query to now
                subscription.last_query = now
                dbSession.commit()

    def processUpdates(self, dbSession):
        self.__telegram.getUpdates(dbSession)

    def __processOffers(self, items, session, user, subscription):
        # iterate thorugh offers
        for offer in items:
            offer_url_id = self.__createUrlIfNotExists(session, offer.getUrl())
            # determine whether offer.getUrl() has already been sent
            if self.__hasOfferNotBeenSent(session, offer_url_id):
                self.__telegram.send_msg(user.telegram_id, offer.getUrl())
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
