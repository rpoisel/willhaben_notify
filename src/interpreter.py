from wn_db import User, Subscription, Url
from crawl import WHCrawlFactory


class Interpreter(object):
    def __init__(self, scheduler, dbsession):
        super().__init__()
        self.__scheduler = scheduler
        self.__dbsession = dbsession

    def interpret(self, peer, tokens):
        if len(tokens) < 1:
            peer.send_msg('No command given.')
            return
        if tokens[0] in commands:
            commands[tokens[0]].execute(self.__scheduler, self.__dbsession, peer, tokens[1:])
            return
        peer.send_msg('Command not found.')


class Command(object):
    def execute(self, scheduler, dbsession, peer, arguments):
        peer.send_msg('Command not implemented')

    def help(self):
        return 'No help available'


class CommandList(Command):
    def execute(self, scheduler, dbsession, peer, arguments):
        subscriptions = ''
        for user, subscription, url in dbsession.query(User, Subscription, Url).filter(User.first_name == peer.first_name).filter(User.last_name == peer.last_name).filter(User.id == Subscription.user_id).filter(Subscription.url_id == Url.id):
            subscriptions += url.location + ' every ' + str(subscription.query_period) + ' seconds\n'
        peer.send_msg(subscriptions)

    def help(self):
        return 'list ... list subscriptions this peer is subscribed to'


class CommandHelp(Command):
    def execute(self, scheduler, dbsession, peer, arguments):
        helpInfo = ''
        for command in commands.values():
            helpInfo += command.help() + '\n'
        peer.send_msg(helpInfo)

    def help(self):
        return 'help ... information about available commands'


class CommandSubscriptionBase(Command):

    def __queryUserDbType(self, dbsession, peer):
        return dbsession.query(User).filter(User.first_name == peer.first_name).filter(User.last_name == peer.last_name);

    def _userExists(self, dbsession, peer):
        if self.__queryUserDbType(dbsession, peer).count() > 0:
            return True
        peer.send_msg('Sorry, you need to be a registered user to perform this operation')
        return False

    def _queryUser(self, dbsession, peer):
        return self.__queryUserDbType(dbsession, peer).first()

    def _subscriptionExists(self, dbsession, peer, urlLocation):
        return self.__querySubscriptionDbType(dbsession, peer, urlLocation).count() > 0

    def __querySubscriptionDbType(self, dbsession, peer, urlLocation):
        return dbsession.query(User, Subscription, Url).filter(User.first_name == peer.first_name).filter(User.last_name == peer.last_name).filter(User.id == Subscription.user_id).filter(Url.location == urlLocation)

    def _removeSubscription(self, dbsession, peer, urlLocation):
        self.__querySubscriptionDbType(dbsession, peer, urlLocation).delete()
        dbsession.commit()

class CommandSubscribe(CommandSubscriptionBase):
    def execute(self, scheduler, dbsession, peer, arguments):
        if not len(arguments) == 2:
            peer.send_msg('Wrong number of arguments.')
            return

        if not self._userExists(dbsession, peer):
            return

        if self._subscriptionExists(dbsession, peer, arguments[0]):
            peer.send_msg('You are already subscribed to this URL.')
            return

        try:
            if not WHCrawlFactory.crawlerExists(arguments[0]):
                peer.send_msg("Could not find a suitable crawler for the site provided!")
                return

            # add URL
            url = Url(location=arguments[0])
            dbsession.add(url)
            dbsession.flush()

            # add Subscription of user to URL
            subscription = Subscription(user_id=self._queryUser(dbsession, peer).id, url_id=url.id, query_period=int(arguments[1]))
            dbsession.add(subscription)
            dbsession.commit()
            peer.send_msg('URL added successfully.')
        except Exception as exc:
            peer.send_msg("Could not add URL: {0}".format(exc))

    def help(self):
        return 'subscribe <URL> <QueryPeriod>'


class CommandUnsubscribe(CommandSubscriptionBase):
    def execute(self, scheduler, dbsession, peer, arguments):
        if not len(arguments) == 1:
            peer.send_msg('Wrong number of arguments.')
            return

        if not self._userExists(dbsession, peer):
            return

        if not self._subscriptionExists(dbsession, peer, arguments[0]):
            peer.send_msg('You are not subscribed to this URL')
            return

        # remove subscription
        try:
            self._removeSubscription(dbsession , peer, arguments[0])
        except:
            peer.send_msg("Could not unsubscribe from URL.")
        # check whether URL can be removed as well (optional)
        peer.send_msg('Subscription removed successfully.')

    def help(self):
        return 'unsubscribe <URL>'

commands = {}
commands['list'] = CommandList()
commands['help'] = CommandHelp()
commands['subscribe'] = CommandSubscribe()
commands['unsubscribe'] = CommandUnsubscribe()
