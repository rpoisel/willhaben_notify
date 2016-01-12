from wn_db import User, Subscription, Url
from crawl import WHCrawlFactory


class Interpreter(object):
    def __init__(self):
        super().__init__()

    def interpret(self, dbSession, telegram, peer, tokens):
        if len(tokens) < 1:
            telegram.send_msg(peer.id, 'No command given.')
            return
        if tokens[0] in commands:
            commands[tokens[0]].execute(dbSession, telegram, peer, tokens[1:])
            return
        telegram.send_msg(peer.id, 'Command not found.')

    def shutdown(self):
        pass


class Command(object):
    def execute(self, dbSession, telegram, peer, arguments):
        telegram.send_msg(peer.id, 'Command not implemented')

    def help(self):
        return 'No help available'

    def __queryUserDbType(self, dbSession, peer, known):
        return dbSession.query(User).filter(User.telegram_id == peer.id).filter(User.known == known)

    def _knownUserExists(self, dbSession, peer):
        return self.__queryUserDbType(dbSession, peer, True).count() > 0

    def _unknownUserExists(self, dbSession, peer):
        return self.__queryUserDbType(dbSession, peer, False).count() > 0

    def _isUserAuthorized(self, dbSession, peer):
        if self._knownUserExists(dbSession, peer):
            return True
        if not self._unknownUserExists(dbSession, peer):
            self._addUnknownUser(dbSession, peer)
        return False

    def _queryUser(self, dbSession, peer):
        return self.__queryUserDbType(dbSession, peer, True).first()

    def _addUnknownUser(self, dbSession, peer):
        newUser = User(telegram_id=peer.id, first_name=peer.first_name, last_name=peer.last_name, known=False)
        dbSession.add(newUser)
        dbSession.commit()

    def __queryUrlDbType(self, dbSession, url_location):
        return dbSession.query(Url).filter(Url.location == url_location)

    def __urlAlreadyExists(self, dbSession, url_location):
        return self.__queryUrlDbType(dbSession, url_location).count() > 0

    def _makeSureUrlExists(self, dbSession, url_location):
        if not self.__urlAlreadyExists(dbSession, url_location):
            url = Url(location=url_location)
            dbSession.add(url)
            dbSession.flush()
            return url.id
        return self.__queryUrlDbType(dbSession, url_location).one().id


class CommandList(Command):
    def execute(self, dbSession, telegram, peer, arguments):
        if not self._isUserAuthorized(dbSession, peer):
            telegram.send_msg(peer.id, 'Not authorized.')
            return

        subscriptions = ''
        for user, subscription, url in dbSession.query(User, Subscription, Url).filter(User.telegram_id == peer.id).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id):
            subscriptions += url.location + ' every ' + str(subscription.query_period) + ' seconds\n'
        if len(subscriptions) > 0:
            telegram.send_msg(peer.id, subscriptions)
        else:
            telegram.send_msg(peer.id, 'No subscriptions.')

    def help(self):
        return '/list ... list subscriptions this peer is subscribed to'


class CommandHelp(Command):
    def execute(self, dbSession, telegram, peer, arguments):
        helpInfo = ''
        for command in commands.values():
            helpInfo += command.help() + '\n'
        telegram.send_msg(peer.id, helpInfo)

    def help(self):
        return '/help ... information about available commands'


class CommandSubscriptionBase(Command):

    def _subscriptionExists(self, dbSession, telegram, peer, urlLocation):
        return self.__querySubscriptionDbType(dbSession, telegram, peer, urlLocation).count() > 0

    def __querySubscriptionDbType(self, dbSession, telegram, peer, urlLocation):
        return dbSession.query(User, Subscription, Url).filter(User.telegram_id == peer.id).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id).filter(Url.location == urlLocation)

    def _removeSubscription(self, dbSession, telegram, peer, urlLocation):
        subscriptions = self.__querySubscriptionDbType(dbSession, telegram, peer, urlLocation).one()
        dbSession.delete(subscriptions.Subscription)
        dbSession.delete(subscriptions.Url)
        dbSession.commit()

class CommandSubscribe(CommandSubscriptionBase):
    def execute(self, dbSession, telegram, peer, arguments):
        if not len(arguments) == 2:
            telegram.send_msg(peer.id, 'Wrong number of arguments.')
            return

        if not self._isUserAuthorized(dbSession, peer):
            telegram.send_msg(peer.id, 'Not authorized.')
            return

        if self._subscriptionExists(dbSession, telegram, peer, arguments[0]):
            telegram.send_msg(peer.id, 'You are already subscribed to this URL.')
            return

        try:
            if not WHCrawlFactory.crawlerExists(arguments[0]):
                raise Exception("Could not find a suitable crawler for the site provided!")
            if not WHCrawlFactory.isCrawlingPeriodValid(arguments[0], int(arguments[1])):
                raise Exception("Given crawling period is not valid.")

            # add URL
            urlId = self._makeSureUrlExists(dbSession, arguments[0])

            # add Subscription of user to URL
            subscription = Subscription(user_id=self._queryUser(dbSession, peer).id, url_id=urlId, query_period=int(arguments[1]))
            dbSession.add(subscription)
            dbSession.commit()
            telegram.send_msg(peer.id, 'URL added successfully.')
        except Exception as exc:
            telegram.send_msg(peer.id, "Could not add URL: {0}".format(exc))
            dbSession.rollback()

    def help(self):
        return '/subscribe <URL> <QueryPeriod> .. subscribe to given URL and retrieve new items every QueryPeriod seconds'


class CommandUnsubscribe(CommandSubscriptionBase):
    def execute(self, dbSession, telegram, peer, arguments):
        if not len(arguments) == 1:
            telegram.send_msg(peer.id, 'Wrong number of arguments.')
            return

        if not self._isUserAuthorized(dbSession, peer):
            telegram.send_msg(peer.id, 'Not authorized.')
            return

        if not self._subscriptionExists(dbSession, telegram, peer, arguments[0]):
            telegram.send_msg(peer.id, 'You are not subscribed to this URL')
            return

        # remove subscription
        try:
            self._removeSubscription(dbSession, telegram, peer, arguments[0])
        except Exception as exc:
            telegram.send_msg(peer.id, "Could not unsubscribe from URL: " + str(exc))
            return
        # check whether URL can be removed as well (optional)
        telegram.send_msg(peer.id, 'Subscription removed successfully.')

    def help(self):
        return '/unsubscribe <URL> ... unsubscribe from given URL'

commands = {}
commands['/list'] = CommandList()
commands['/help'] = CommandHelp()
commands['/subscribe'] = CommandSubscribe()
commands['/unsubscribe'] = CommandUnsubscribe()
