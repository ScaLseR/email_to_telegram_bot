# -*- coding: utf8 -*-
import email
import imaplib
import copy
import requests
import quopri
import time
import smtplib
import configparser
from email.header import Header, decode_header, make_header
from email.mime.text import MIMEText

#Отправка ответа на входящее письмо
def send_mail_to_sender(addr):
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    host = config.get('email', 'host')
    port = config.get('email', 'port')
    from_ = config.get('email', 'from')
    subject = config.get('email', 'subject')
    passw = config.get('email', 'pass')
    msg = config.get('email', 'msg')
    message = MIMEText(msg, 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    message['From'] = from_
    message['To'] = addr
    server = smtplib.SMTP(host, port)
    server.login(from_, passw)
    server.sendmail(from_, addr, message.as_string())
    server.close()

#Отправка входящего письма в чат телеграмма
def send_mail_to_tg(text):
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    api_token = config.get('tg', 'api_token')
    url = config.get('tg', 'url')
    chat_id = config.get('tg', 'chat_id')
    print(config.get('tg', 'api_token'), config.get('tg', 'url'), config.get('tg', 'chat_id'))
    requests.post(f'{url}{api_token}/sendMessage?chat_id={chat_id}&text={text}')

#изменение кодировки заголовка письма в utf-8 из base64
def dec_hed(message):
    bytes, mail_subject = decode_header(message)[0]
    return bytes.decode(mail_subject)

#замена в теле письма <div> и </div>
def repl_div(mail_body):
    s = mail_body.replace('<div>', '')
    rez_mail_body = s.replace('</div>', '\n')
    return rez_mail_body

def add_mail_text(mail_from, mail_subject):
    #если письмо пришло с mail.dumask
    #if '@dumask.ru' in mail_from:
    #    rez_mail_subject = dec_hed(mail_subject)
    #    rez_mail_body = quopri.decodestring(mail_body)
    #    text ='От: '+mail_from+'\n'+'Тема: '+rez_mail_subject+'\n'+'Содержание: '+ rez_mail_body.decode('windows-1251')
    #если письмо пришло с mail.yandex
    #if '@yandex.ru' in mail_from:
    #    rez_mail_body = repl_div(mail_body)
     #   rez_mail_subject = dec_hed(mail_subject)
     #   text ='От: '+mail_from+'\n'+'Тема: '+rez_mail_subject+'\n'+'Содержание: '+ rez_mail_body

    #if '@mail.ru' in mail_from:
    #rez_mail_body = repl_div(mail_body)
    rez_mail_subject = dec_hed(mail_subject)
    text ='От: '+mail_from+'\n'+'Тема: '+rez_mail_subject+'\n'+'Содержание: '

    send_mail_to_tg(text)
    send_mail_to_sender(mail_from)

#Получение данных от кого, тема и содержание письма
def exp_data_from_email(mail_data):
    s = {}
    if len(mail_data) > 0:
        for i in range(len(mail_data)):
            s = mail_data[i]
            print('s[mail_from][1] ===', s['mail_from'][1])
            print('s[mail_subject] ===', s['mail_subject'])
            #print('s[body]===', s['body'])
            #add_mail_text(s['mail_from'][1], s['mail_subject'], s['body'])
            add_mail_text(s['mail_from'][1], s['mail_subject'])
            s = {}

#Получение непрочитанных писем из почтового ящика
def read(username, password, host ,sender_of_interest=None):

    imap = imaplib.IMAP4(host)
    imap.login(username, password)
    imap.select('INBOX')

    if sender_of_interest:
        status, response = imap.uid('search', None, 'UNSEEN', 'FROM {0}'.format(sender_of_interest))
    else:
        status, response = imap.uid('search', None, 'UNSEEN')
    if status == 'OK':
        unread_msg_nums = response[0].split()
    else:
        unread_msg_nums = []
    data_list = []
    for e_id in unread_msg_nums:
        data_dict = {}
        e_id = e_id.decode('utf-8')
        _, response = imap.uid('fetch', e_id, '(RFC822)')
        html = response[0][1].decode('utf-8')
        email_message = email.message_from_string(html)
        data_dict['mail_to'] = email_message['To']
        data_dict['mail_subject'] = email_message['Subject']
        data_dict['mail_from'] = email.utils.parseaddr(email_message['From'])
        data_dict['body'] = email_message.get_payload()
        print('data_dict=====', data_dict)
        data_list.append(data_dict)
        exp_data_from_email(data_list)

#Проверка почтового ящика каждые 60 секунд
def start():
    i = 1
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    while i !=0:
        read(config.get('email', 'from'), config.get('email', 'pass'),config.get('email', 'host'))
        time.sleep(60)

if __name__ == '__main__':
    start()

