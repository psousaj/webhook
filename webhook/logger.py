import logging


class Logger:

    def __init__(self, name) -> None:
        # Configuração do logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Criando um handler para o log no terminal
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        # Criando um handler para o log em arquivo de texto
        self.file_handler = logging.FileHandler('webhook_log.txt')
        self.file_handler.setLevel(logging.DEBUG)

        # Definindo o formato das mensagens de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s -%(levelname)s- %(message)s', datefmt='%d/%m/%Y|%H:%M:%S')
        self.console_handler.setFormatter(formatter)
        self.file_handler.setFormatter(formatter)

        # Adicionando os handlers ao logger
        # self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, *kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, *kwargs)
