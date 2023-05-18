from webhook.request import get_chat_protocol as digisac_api


def manage(data):
    event = data['event']
    event_type = data['data']['type']
    ticketId = {data["data"]["ticketId"]}
    # Protocolo para encaminhar no grupo
    protocol = digisac_api(url=f'/tickets/{ticketId}')

    if 'type' in data['data'] and event_type != 'ticket':
        if event == 'message.updated':
            message_id = data['data']['id']
            handle_message_updated(data, message_id)
        elif event == 'message.created':
            handle_message_created(data)
    else:
        pass


def handle_message_created(data):
    if not data['data']['isFromMe'] and 'ticketId' in data['data']:
        cnpj, id_mess, confirm_file, name_company = search_message_confirmation.search(
            data)
        if id_mess == 'question-confim':
            handle_message_confirm(data, cnpj, id_mess,
                                   confirm_file, name_company)
        elif id_mess and cnpj:
            handle_message_text(data, cnpj, id_mess,
                                confirm_file, name_company)
        elif confirm_file and cnpj:
            response_messeger.send_finish(cnpj)
            close_ticket.close(cnpj)
        else:
            handle_other_cases(data, cnpj, name_company)
    else:
        handle_other_cases(data, cnpj, name_company)


def handle_message_updated(data, message_id):
    messe_data = search_message.search(message_id)
    if messe_data:
        status = data['data']['data']['ack']
        confirm_mensager.confirm(messe_data, status)


def handle_message_confirm(data, cnpj, id_mess, confirm_file, name_company):
    if 'text' in data['data']:
        text = str(data['data']['text']).lower()
        if text == 'sim':
            response_messeger.send_finish(cnpj)
            update_control_messager.update_question(
                data['data']['ticketId'], 'question-confirm', '4')
        else:
            handle_attempt(cnpj, 'question-confirm', name_company)
    else:
        handle_attempt(cnpj, 'question-confirm', name_company)


def handle_message_text(data, cnpj, id_mess, confirm_file, name_company):
    text = str(data['data']['text']).lower()
    if text in ('sim', 'quero'):
        folder, name = download_json_and_das_company.download(cnpj)
        if folder:
            send_files_competences.send(cnpj, name, folder, id_mess)
            response_messeger.send_finish(cnpj)
            update_control_messager.update_question(
                data['data']['ticketId'], 'question', '4')
            close_ticket.close(cnpj)
    elif text in ('nao', 'não'):
        response_messeger.send_finish(cnpj)
        update_control_messager.update_question(
            data['data']['ticketId'], 'question', '4')
        close_ticket.close(cnpj)
    else:
        handle_attempt(data, cnpj, 'question', name_company)


def handle_attempt(data, cnpj, question, name_company):
    attempt = verify_attempt.check_question(cnpj, question)
    if attempt < 3:
        response_messeger.send_negation_confirm(cnpj)
        update_attempt.update_question(cnpj, question)
    else:
        response_messeger.send_tranfer(cnpj)
        text_messeger = f"O cliente {name_company} solicita um atendimento - protocolo {protocol}"
        send_message_group.send(text_messeger)
        update_control_messager.update_question(
            data['data']['ticketId'], question, '4')


def handle_other_cases(data, cnpj, name_company):
    response_messeger.send(data['data']['contactId'])
    close_ticket.close(cnpj)
    text_messeger = f"O cliente {name_company} solicita um atendimento"
    send_message_group.send(text_messeger)
