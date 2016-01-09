from os.path import expanduser
from time import sleep
from threading import Thread

from wn_db import WNDB
from interpreter import Interpreter
from telegram import Telegram
from scheduler import Scheduler


def main():
    wndb = WNDB(path=expanduser('~/wn.sqlite'))
    interpreter = Interpreter(wndb)
    telegram = Telegram(interpreter)
    scheduler = Scheduler(wndb, telegram)

    thread = Thread(target=scheduler.run)

    thread.start()

    while True:
        try:
            sleep(.1)
        except (KeyboardInterrupt, SystemExit):
            break

    telegram.shutdown()
    scheduler.shutdown()
    thread.join()

if __name__ == "__main__":
    main()
