import logging
from logging import StreamHandler

from twx.botapi import TelegramBot


class Telegram(object):
    def __init__(self, config, interpreter):
        super().__init__()
        self.__interpreter = interpreter
        self.__logger = logging.getLogger('telegram')
        logHandler = StreamHandler()
        logHandler.setLevel(logging.DEBUG)
        self.__logger.addHandler(logHandler)

        self.__bot = TelegramBot(config['Telegram']['token'])
        self.__logger.warning("Bot details: " + str(self.__bot.get_me().wait()))

        self.__updateOffset = None

    def send_msg(self, telegram_id, text):
        self.__bot.send_message(telegram_id, text).wait()

    def getUpdates(self, dbSession):
        updates = None
        if self.__updateOffset is not None:
            updates = self.__bot.get_updates(offset=self.__updateOffset + 1).wait()
        else:
            updates = self.__bot.get_updates().wait()

        for update in updates:
            if hasattr(update, 'message'):
                self.__logger.warning(str(update.message.sender) + ": " + update.message.text)
                self.__interpreter.interpret(dbSession, self, update.message.sender, update.message.text.split(' '))
            if hasattr(update, 'update_id'):
                self.__updateOffset = update.update_id

    def shutdown(self):
        pass
