import tgl
import requests
from lxml import html
from time import sleep
import datetime
import sqlite3


class Scheduler(object):
    def __init__(self):
        super().__init__()
        self.__peers = None
        self.__last = datetime.datetime.now()
        self.__conn = sqlite3.connect('../db/wn.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
        self.__conn.row_factory = sqlite3.Row
        self.__cursor = self.__conn.cursor()
        
    def setPeers(self, peers):
        self.__peers = peers
    
    def tick(self):
        now = datetime.datetime.now()
        totalseconds = (now - self.__last).total_seconds()
        if totalseconds >= 1:
            self.__last = now
            self.schedule()
    
    def schedule(self):
        #if self.__peers is not None:
        #    self.__peers["Rainer Poisel"].send_msg("Once a second called ...")
        self.__cursor.execute('SELECT \
            subscriptions.user_id, users.first_name, users.last_name, subscriptions.url, subscriptions.last_query, subscriptions.query_period \
            FROM subscriptions \
            INNER JOIN users on users.id = subscriptions.user_id')
        while True:
            subscription = self.__cursor.fetchone()
            if subscription is None:
                break
            if subscription['last_query'] is None:
                self.__cursor.execute(
                    "UPDATE subscriptions SET last_query = ? WHERE user_id = ?",
                    (datetime.datetime.now(), subscription['user_id']))
                self.__conn.commit()


def on_user_map_populated(peers):
    scheduler.setPeers(peers)


def cb_main_entry(s, cl):
    peers = {}
    for p in cl:
        username = p.first_name + " " + p.last_name
        peers[username] = p
    on_user_map_populated(peers)


def cb_user_update(peer, what_changed):
    pass


def cb_chat_update(peer, what_changed):
    pass


def cb_on_diff_end():
    pass


def cb_binlog_end():
    pass


def main():
    tgl.get_contact_list(cb_main_entry)
    tgl.set_on_user_update(cb_user_update)
    tgl.set_on_get_difference_end(cb_on_diff_end)
    tgl.set_on_chat_update(cb_chat_update)
    tgl.set_on_loop(scheduler.tick)
    tgl.set_on_binlog_replay_end(cb_binlog_end)


scheduler = Scheduler()
main()
