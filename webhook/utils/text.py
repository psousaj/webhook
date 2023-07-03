from enum import Enum
from datetime import datetime as dt

class TransferTicketReasons(Enum):
    ASK_FOR_ATTENDANT = "Atendente solicitado no canal de documentos"
    EXCEPT_RETRIES = "3 tentativas de resposta não compreendidas automaticamente"
    MORE_THAN_FIVE_PENDENCIES = "Número de pendencias({REPLACE}) maior que 5, te encaminhei para um atendente.\nAguarde que logo entraremos em contato"

    @classmethod
    def get_text_with_replace(cls, atrib='MORE_THAN_FIVE_PENDENCIES', param=None):
        return (getattr(cls, atrib).value).replace('{REPLACE}', param)

class Answers(Enum):
    UNEXPECTED_MESSAGE = "Esse canal é apenas para o envio de documentos.\nDeseja falar com um atendente? (Sim / Não)"
    ASK_FOR_ATTENDANT = "Estou solicitando um atendente para você. Aguarde um pouco por gentileza."
    DONT_NEED_ATTENDANT = "Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!"
    RETRY_ASK_FOR_ATTENDANT = "Este canal é para documentos, se precisar de um atendente informe por gentileza\n(Sim / Não)"
    PENDENCIES_SEND_CONFIRMED = "Vou enviar os arquivos agora mesmo!"
    MESSAGE_CONFIRMED = "Obrigado por confirmar!"
    NEGATIVE_RESPONSE = "Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!"
    NOT_TEXT_MESSAGE_RECEIVED = "Obrigado! Ainda preciso que me responda SIM, OK, ou RECEBI para finalizar o atendimento"
    ASK_ASSISTANCE = "Tudo bem! Em instantes um de nossos atendentes entrará em contato!"
    MORE_THAN_FIVE_PENDENCIES = "Número de pendencias({REPLACE}) maior que 5, te encaminhei para um atendente.\nAguarde que logo entraremos em contato"
    BASE_ERROR_MESSAGE = "\nDesculpe, não entendi. Por favor, responda SIM, OK ou "
    HAS_DEBITS_ERROR_COMPLETION = "NÃO caso não queira os boletos agora."
    NO_DEBIT_ERROR_COMPLETION = "RECEBI."
    ATTENDANT_ERROR_COMPLETION = '\nSe precisar falar com um de nossos atendentes digite "atendente"'

    @classmethod
    def get_text_with_replace(cls, atrib='MORE_THAN_FIVE_PENDENCIES', param=None):
        return (getattr(cls, atrib).value).replace('{REPLACE}', param)


class BaseText(Enum):
    saudacao = f"""Olá, espero que esteja bem.
Gostaria de informar que seu Documento de Arrecadação Simplificado(DAS) 
período ({dt.today().strftime('%B/%Y').capitalize()}) está disponível, irei envia-lo em seguida.
Lembrando que é importante que o pagamento seja realizado
dentro do prazo estipulado para evitar juros e multa
"""

    suggest = "Qualquer dúvida ou sugestão entre em contato através do WhatsApp: https://wa.me/5588988412833."

    disclaimer = f"""
{suggest}

Por favor, preciso que confirme o recebimento desta mensagem. 
Responda SIM, OK, ou RECEBI por gentileza.
"""


    def get_pendencies_text(pendencies):
        pendencies_message = f"""
Identificamos que existem documentos de arrecadação simplificado (DAS)
pendentes no nome de sua empresa.

({pendencies})

Deseja receber os boletos agora, para realizar o pagamento?
"""

        return pendencies_message