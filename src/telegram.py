import logging
from logging import StreamHandler

from twx.botapi import TelegramBot


class Telegram(object):
    def __init__(self, interpreter):
        super().__init__()
        self.__interpreter = interpreter
        self.__logger = logging.getLogger('telegram')
        logHandler = StreamHandler()
        logHandler.setLevel(logging.DEBUG)
        self.__logger.addHandler(logHandler)

        # TODO read token from file
        self.__bot = TelegramBot('your token here')
        self.__logger.warning("Bot details: " + str(self.__bot.get_me().wait()))

    def send_msg(self, telegram_id, text):
        self.__bot.send_message(telegram_id, text).wait()

    def getUpdates(self):
        self.__interpreter.interpret(msg.src, msg.text.split(' '))
