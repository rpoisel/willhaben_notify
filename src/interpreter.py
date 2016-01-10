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


class CommandList(Command):
    def execute(self, dbSession, telegram, peer, arguments):
        subscriptions = ''
        for user, subscription, url in dbSession.query(User, Subscription, Url).filter(User.telegram_id == peer.id).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id):
            subscriptions += url.location + ' every ' + str(subscription.query_period) + ' seconds\n'
        telegram.send_msg(peer.id, subscriptions)

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

    def __queryUserDbType(self, dbSession, peer):
        return dbSession.query(User).filter(User.telegram_id == peer.id)

    def _userExists(self, dbSession, telegram, peer):
        if self.__queryUserDbType(dbSession, peer).count() > 0:
            return True
        telegram.send_msg(peer.id, 'Sorry, you need to be a registered user to perform this operation')
        return False

    def _queryUser(self, dbSession, peer):
        return self.__queryUserDbType(dbSession, peer).first()

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

        if not self._userExists(dbSession, telegram, peer):
            return

        if self._subscriptionExists(dbSession, telegram, peer, arguments[0]):
            telegram.send_msg(peer.id, 'You are already subscribed to this URL.')
            return

        try:
            if not WHCrawlFactory.crawlerExists(arguments[0]):
                telegram.send_msg(peer.id, "Could not find a suitable crawler for the site provided!")
                return

            # add URL
            url = Url(location=arguments[0])
            dbSession.add(url)
            dbSession.flush()

            # add Subscription of user to URL
            subscription = Subscription(user_id=self._queryUser(dbSession, peer).id, url_id=url.id, query_period=int(arguments[1]))
            dbSession.add(subscription)
            dbSession.commit()
            telegram.send_msg(peer.id, 'URL added successfully.')
        except Exception as exc:
            telegram.send_msg(peer.id, "Could not add URL: {0}".format(exc))

    def help(self):
        return '/subscribe <URL> <QueryPeriod> .. subscribe to given URL and retrieve new items every QueryPeriod seconds'


class CommandUnsubscribe(CommandSubscriptionBase):
    def execute(self, dbSession, telegram, peer, arguments):
        if not len(arguments) == 1:
            telegram.send_msg(peer.id, 'Wrong number of arguments.')
            return

        if not self._userExists(dbSession, telegram, peer):
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
