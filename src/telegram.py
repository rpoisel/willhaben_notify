import datetime
import logging
from logging.handlers import SysLogHandler
from os.path import expanduser

from wn_db import WNDB, User, Subscription, SentOffer, Url
from crawl import WHCrawl

import tgl

class Scheduler(object):
    def __init__(self, dbpath):
        super().__init__()
        self.__logger = logging.getLogger('telegram')
        self.__logger.addHandler(SysLogHandler())
        self.__peers = None
        self.__dialogs = None
        self.__last = datetime.datetime.now()
        self.__db = WNDB(path=dbpath)

    def setPeers(self, peers):
        self.__peers = peers

    def setDialogs(self, dialogs):
        self.__dialogs = dialogs

    def tick(self):
        if not self.__isSchedulerInitialized():
            return

        now = datetime.datetime.now()
        totalseconds = (now - self.__last).total_seconds()
        if totalseconds >= 1:
            self.__last = now
            self.schedule(now=now)

    def schedule(self, now):
        # obtain database session
        session = self.__db.getSession()
        # iterate through subscriptions
        for user, subscription, subscription_url in session.query(User, Subscription, Url).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id).all():
            # determine which subscriptions have to be queried again
            if self.__isSubscriptionDue(now, subscription):
                # query relevant subscription pages
                crawl = WHCrawl(subscription_url.location)
                self.__processOffers(crawl, session, user, subscription)
                # update last_query to now
                subscription.last_query = now
                session.commit()

    def __isSchedulerInitialized(self):
        return self.__peers is not None and self.__dialogs is not None

    def __createChatGroups(self):
        pass

    def __processOffers(self, crawl, session, user, subscription):
        # iterate thorugh offers
        for offer in crawl.getOffers():
            offer_url_id = self.__createUrlIfNotExists(session, offer.getUrl())
            # determine whether offer.getUrl() has already been sent
            if self.__hasOfferNotBeenSent(session, offer_url_id):
                # if no, send offer
                if False:
                    self.__sendTelegramMsg(user.first_name, user.last_name, offer.getUrl())
                else:
                    self.__sendTelegramGrpMsg(user.first_name, user.last_name, offer.getUrl())
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

    def __sendTelegramMsg(self, first_name, last_name, msg):
        peer_name = first_name + " " + last_name
        if peer_name in self.__peers:
            self.__peers[peer_name].send_msg(msg, preview=True)
        else:
            self.__logger.error("Peer " + peer_name + " cannot be found. Please add it to your contact list!")

    def __sendTelegramGrpMsg(self, first_name, last_name, msg, grp_prefix='Offers'):
        dialog_name = grp_prefix + '_' + first_name + '_' + last_name
        if dialog_name in self.__dialogs:
            self.__dialogs[dialog_name].send_msg(msg, preview=True)
        else:
            self.__logger.error("Dialog " + dialog_name + " cannot be found. Please create it!")

    def __hasOfferNotBeenSent(self, session, offer_url_id):
        return session.query(SentOffer, Subscription).filter(Subscription.user_id == SentOffer.user_id).filter(SentOffer.url_id == offer_url_id).count() == 0

    def __isSubscriptionDue(self, now, subscription):
        return subscription.last_query is None or (now - subscription.last_query).total_seconds() >= subscription.query_period


def cb_contact_list(s, cl):
    peers = {}
    for p in cl:
        username = p.first_name + " " + p.last_name
        peers[username] = p
    scheduler.setPeers(peers)


def cb_dialog_list(success, dialog_list):
    dialogs = {}
    for dialog in dialog_list:
        if dialog['peer'].type == tgl.PEER_CHAT:
            dialogs[dialog['peer'].name] = dialog['peer']
    scheduler.setDialogs(dialogs)


def cb_user_update(peer, what_changed):
    pass


def cb_chat_update(peer, what_changed):
    pass


def cb_on_diff_end():
    pass


def cb_binlog_end():
    pass

def cb_on_our_id(our_id):
    pass


def main():
    tgl.get_contact_list(cb_contact_list)
    tgl.get_dialog_list(cb_dialog_list)
    tgl.set_on_user_update(cb_user_update)
    tgl.set_on_get_difference_end(cb_on_diff_end)
    tgl.set_on_chat_update(cb_chat_update)
    tgl.set_on_loop(scheduler.tick)
    tgl.set_on_binlog_replay_end(cb_binlog_end)
    tgl.set_on_our_id(cb_on_our_id)


scheduler = Scheduler(dbpath=expanduser('~/wn.sqlite'))
main()
