from webhook.request import any_request as digisac_api
import json


def teste_de_coisas(url: str):
    print(digisac_api(url))


def handle_message_updated(data, message_id):
    protocol = digisac_api('/messages')
    print(protocol)
    # messe_data = search_message.search(message_id)
    # if messe_data:
    # status = data['data']['data']['ack']
    # confirm_mensager.confirm(messe_data, status)


# with open('messages/tax/1.json', 'r') as f:
#     data = json.load(f)
# handle_message_updated(data, data['data']['id'])
teste_de_coisas('/contacts/79db7607-6088-44c1-a010-ed4ef39d4f37')
