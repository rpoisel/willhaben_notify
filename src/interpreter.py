

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
        peer.send_msg('Command not understood.')


class Command(object):
    def execute(self, scheduler, dbsession, peer, arguments):
        peer.send_msg('Command not implemented')


class CommandList(Command):
    def execute(self, scheduler, dbsession, peer, arguments):
        peer.send_msg('Listing subscriptions ...')

commands = {}
commands['list'] = CommandList()