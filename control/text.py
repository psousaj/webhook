from messages_api.event import get_current_period
import locale

# locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

saudacao = f"""Olá, espero que esteja bem.
Gostaria de informar que seu Documento de Arrecadação Simplificado(DAS) 
período ({get_current_period(file_name=True)}) está disponível, irei envia-lo em seguida.
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

# "Abril/2020, Março/2021, Janeiro/2022, Agosto/2022"
