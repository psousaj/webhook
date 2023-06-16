import logging
from datetime import datetime as dt


__all__=["get_contact_number", "get_current_period", "Logger"]

class Logger:

    def __init__(self, name) -> None:
        # Configuração do logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Criando um handler para o log no terminal
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        # Criando um handler para o log em arquivo de texto
        # self.file_handler = logging.FileHandler('webhook_log.txt')
        # self.file_handler.setLevel(logging.DEBUG)

        # Definindo o formato das mensagens de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s -%(levelname)s- %(message)s', datefmt='%d/%m/%Y|%H:%M:%S')
        self.console_handler.setFormatter(formatter)
        # self.file_handler.setFormatter(formatter)

        # Adicionando os handlers ao logger
        self.logger.addHandler(self.console_handler)
        # self.logger.addHandler(self.file_handler)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

def get_contact_number(contact_id: str, only_number=False):
    from webhook.utils.get_objects import get_contact
    contact = get_contact(contact_id=contact_id)

    if contact:
        if not only_number:
            return f"{contact.country_code}{contact.ddd}{contact.contact_number}"
        else:
            return f"{contact.contact_number}"

    return None

def get_current_period(file_name=False) -> str:
    if file_name:
        return dt.today().strftime('%B/%Y').capitalize()

    return dt.today().strftime('%m/%y')

