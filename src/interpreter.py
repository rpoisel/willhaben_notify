from wn_db import User, Subscription, Url


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

commands = {}
commands['list'] = CommandList()
commands['help'] = CommandHelp()