from os.path import expanduser

from wn_db import WNDB
from scheduler import Scheduler
from interpreter import Interpreter

import tgl

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
    global id
    id = our_id

def cb_on_msg_receive(msg):
    if id is None or msg.src.id == id:
        return

    if not scheduler.isInitialized():
        msg.src.send_msg("Sorry, scheduler not initialized yet. ")
        return

    interpreter.interpret(msg.src, msg.text.split(' '))


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

id = None
wndb = WNDB(path=expanduser('~/wn.sqlite'))
scheduler = Scheduler(dbsession=wndb.getSession())
interpreter = Interpreter(scheduler, wndb.getSession())
main()
