'''
Created on Aug 18, 2015

@author: rpoisel
'''

from os.path import expanduser

from wn_db import WNDB
from scheduler import Scheduler
from interpreter import Interpreter
from telegram import Telegram, setupTelegram

def main():
    wndb = WNDB(path=expanduser('~/wn.sqlite'))
    scheduler = Scheduler(dbsession=wndb.getSession())
    interpreter = Interpreter(scheduler, wndb.getSession())
    telegram = Telegram(interpreter)
    scheduler.setTelegram(telegram)
    setupTelegram(telegram, scheduler)

main()