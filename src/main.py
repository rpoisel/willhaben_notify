from os.path import expanduser

from wn_db import WNDB
from scheduler import Scheduler
from interpreter import Interpreter
from telegram import Telegram


def main():
    wndb = WNDB(path=expanduser('~/wn.sqlite'))
    interpreter = Interpreter(wndb.getSession())
    telegram = Telegram(interpreter)
    scheduler = Scheduler(telegram, dbsession=wndb.getSession())

    try:
        scheduler.schedule();
    except (KeyboardInterrupt, SystemExit):
        pass

    # TODO signal scheduler to shut down and wait
    # close database connection/session

if __name__ == "__main__":
    main()
