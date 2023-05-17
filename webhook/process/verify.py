# from webhook.request import get_digisac_api as digisac_api


# def receiver_handler(data):
#     id_messager = data['data']['id']
#     event = data['event']

#     if 'type' in data['data'] and data['data']['type'] != 'ticket':
#         if event == 'message.updated':
#             handle_message_updated(data, event, id_messager)
#         elif event == 'message.created':
#             handle_message_created(data, event)
#         else:
#             pass


# def handle_message_updated(data, message_id):
#     ticket_id = data['data']['ticketId']
#     protocol = digisac_api(f'/tickets/{ticket_id}')
#     message_data = search_message.search(message_id)
#     if message_data:
#         status = data['data']['data']['ack']
#         confirm_mensager.confirm(message_data, status)


# def handle_message_created(data, event):
#     if not data['data']['isFromMe'] and 'ticketId' in data['data']:
#         cnpj, id_mess, confirm_file, name_company = search_message_confirmation.search(
#             data)
#         if id_mess == 'question-confim':
#             handle_message_confirm(data, cnpj, id_mess,
#                                    confirm_file, name_company)
#         elif id_mess and cnpj:
#             handle_message_text(data, cnpj, id_mess,
#                                 confirm_file, name_company)
#         elif confirm_file and cnpj:
#             response_messeger.send_finish(cnpj)
#             close_ticket.close(cnpj)
#         else:
#             handle_other_cases(data, cnpj, name_company)
#     else:
#         handle_other_cases(data, cnpj, name_company)


# def handle_message_confirm(data, cnpj, id_mess, confirm_file, name_company):
#     if 'text' in data['data']:
#         text = str(data['data']['text']).lower()
#         if text == 'sim':
#             response_messeger.send_finish(cnpj)
#             update_control_messager.update_question(
#                 data['data']['ticketId'], 'question-confirm', '4')
#         else:
#             handle_attempt(cnpj, 'question-confirm', name_company)
#     else:
#         handle_attempt(cnpj, 'question-confirm', name_company)


# def handle_message_text(data, cnpj, id_mess, confirm_file, name_company):
#     text = str(data['data']['text']).lower()
#     if text in ('sim', 'quero'):
#         folder, name = download_json_and_das_company.download(cnpj)
#         if folder:
#             send_files_competences.send(cnpj, name, folder, id_mess)
#             response_messeger.send_finish(cnpj)
#             update_control_messager.update_question(
#                 data['data']['ticketId'], 'question', '4')
#             close_ticket.close(cnpj)
#     elif text in ('nao', 'não'):
#         response_messeger.send_finish(cnpj)
#         update_control_messager.update_question(
#             data['data']['ticketId'], 'question', '4')
#         close_ticket.close(cnpj)
#     else:
#         handle_attempt(data, cnpj, 'question', name_company)


# def handle_other_cases(data, cnpj, name_company):
#     response_messeger.send(data['data']['contactId'])
#     close_ticket.close(cnpj)
#     text_messeger = f"O cliente {name_company} solicita um atendimento"
#     send_message_group.send(text_messeger)


# def handle_attempt(data, cnpj, question, name_company):
#     attempt = verify_attempt.check_question(cnpj, question)
#     if attempt < 3:
#         response_messeger.send_negation_confirm(cnpj)
#         update_attempt.update_question(cnpj, question)
#     else:
#         response_messeger.send_tranfer(cnpj)
#         text_messeger = f"O cliente {name_company} solicita um atendimento - protocolo {protocol}"
#         send_message_group.send(text_messeger)
#         update_control_messager.update_question(
#             data['data']['ticketId'], question, '4')
