from os.path import expanduser

from wn_db import WNDB
from scheduler import Scheduler
from interpreter import Interpreter

import tgl

def cb_contact_list(s, cl):
    peers = {}
    for peer in cl:
        username = peer.first_name + " " + peer.last_name
        peers[username] = peer
    telegram.setPeers(peers)


def cb_dialog_list(success, dialog_list):
    dialogs = {}
    for dialog in dialog_list:
        if dialog['peer'].type == tgl.PEER_CHAT:
            dialogs[dialog['peer'].name] = dialog['peer']
    telegram.setDialogs(dialogs)


def cb_user_update(peer, what_changed):
    pass


def cb_chat_update(peer, what_changed):
    pass


def cb_on_diff_end():
    pass


def cb_binlog_end():
    pass

def cb_on_our_id(our_id):
    telegram.setId(our_id)

def cb_on_msg_receive(msg):
    if not telegram.isInitialized():
        msg.src.send_msg("Sorry, bot not initialized yet. ")
        return

    if msg.src.id == telegram.getId():
        return

    interpreter.interpret(msg.src, msg.text.split(' '))


class Telegram(object):
    def __init__(self):
        super().__init__()
        self.__id = None
        self.__peer = None
        self.__peers = None
        self.__dialogs = None

    def isInitialized(self):
        return self.__id is not None and self.__peers is not None and self.__dialogs is not None

    def setId(self, our_id):
        self.__id = our_id

    def getId(self):
        return self.__id

    def setPeers(self, peers):
        self.__peers = peers
        for key, peer in self.__peers.items():
            if peer.id == self.__id:
                self.__peer = peer
                return

    def setDialogs(self, dialogs):
        self.__dialogs = dialogs

    def send_msg(self, first_name, last_name, msg):
        peer_name = first_name + " " + last_name
        if peer_name in self.__peers:
            self.__peers[peer_name].send_msg(msg, preview=True)
        else:
            self.__logger.error("Peer " + peer_name + " cannot be found. Please add it to your contact list!")

    def send_self_msg(self, msg):
        self.__peer.send_msg(msg, preview=True)

    def send_grpmsg(self, first_name, last_name, msg, grp_prefix='Offers'):
        dialog_name = grp_prefix + '_' + first_name + '_' + last_name
        if dialog_name in self.__dialogs:
            self.__dialogs[dialog_name].send_msg(msg, preview=True)
        else:
            self.__logger.error("Dialog " + dialog_name + " cannot be found. Please create it!")


def main():
    tgl.get_contact_list(cb_contact_list)
    tgl.get_dialog_list(cb_dialog_list)
    tgl.set_on_user_update(cb_user_update)
    tgl.set_on_get_difference_end(cb_on_diff_end)
    tgl.set_on_chat_update(cb_chat_update)
    tgl.set_on_loop(scheduler.tick)
    tgl.set_on_binlog_replay_end(cb_binlog_end)
    tgl.set_on_our_id(cb_on_our_id)
    tgl.set_on_msg_receive(cb_on_msg_receive)

telegram = Telegram()
wndb = WNDB(path=expanduser('~/wn.sqlite'))
scheduler = Scheduler(telegram, dbsession=wndb.getSession())
interpreter = Interpreter(scheduler, wndb.getSession())
main()
