# -*- coding: utf8 -*-
import email
import imaplib
import copy
import requests
import quopri
import time
import smtplib
import configparser
import re
import datetime
from email.header import Header, decode_header, make_header
from email.mime.text import MIMEText

#Получение значений параметров из файла config.ini
def get_param(part, param):
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    rez = config.get(part, param)
    return rez

#Отправка ответа на полученное письмо
def send_mail_to_sender(addr):
    host = get_param('email', 'host')
    port = get_param('email', 'port')
    from_ = get_param('email', 'from')
    subject = get_param('email', 'subject')
    passw = get_param('email', 'pass')
    msg = get_param('email', 'msg')
    message = MIMEText(msg, 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    message['From'] = from_
    message['To'] = addr
    server = smtplib.SMTP(host, port)
    server.login(from_, passw)
    server.sendmail(from_, addr, message.as_string())
    server.close()

#Отправка полученного письма в чат телеграмма
def send_mail_to_tg(text):
    api_token = get_param('tg', 'api_token')
    url = get_param('tg', 'url')
    chat_id = get_param('tg', 'chat_id')
    requests.post(f'{url}{api_token}/sendMessage?chat_id={chat_id}&text={text}')

#изменение кодировки заголовка письма в utf-8 из base64
def dec_hed(message):
    bytes, mail_subject = decode_header(message)[0]
    return bytes.decode(mail_subject)

#конвертируем фио от кого пришло письмо
#def dec_from_mail(message):

#Замена в теле письма <div> и </div>
def repl_div(mail_body):
    s = mail_body.replace('<div>', '')
    rez_mail_body = s.replace('</div>', '\n')
    return rez_mail_body

#Пишем данные в лог файл
def log_file(text):
    date_time_now = datetime.datetime.now()
    with open('log.txt', 'a') as file:
        file.write(str(date_time_now) + '  ' + text+ '\n')
        file.write('*****************************************************************\n')

#Создание сообщения для отправки в телеграм и ответное письмо отправителю
def add_mail_text(mail_from_name, mail_from, mail_subject, mail_body):
    rez_mail_subject = dec_hed(mail_subject)
    text ='От: '+mail_from+'\n'+'Тема: '+rez_mail_subject+'\n'+'Содержание: '+mail_body
    send_mail_to_tg(text)
    send_mail_to_sender(mail_from)
    log_file(text)

def data_from_body(data):
    if '<div>' in data:
        rez = repl_div(data)

    if re.search(r'=..=..', data):
        rez1 = quopri.decodestring(data)
        rez = rez1.decode('windows-1251')

    return rez

#Получение данных из email: от кого, тема и содержание письма
def exp_data_from_email(mail_data):
    s = {}
    if len(mail_data) > 0:
        for i in range(len(mail_data)):
            s = mail_data[i]
            body = data_from_body(s['body'])
            add_mail_text(s['mail_from'][0], s['mail_from'][1], s['mail_subject'], body)
            s = {}

#Получение непрочитанных писем из почтового ящика
def read(username, password, host ,sender_of_interest=None):

    imap = imaplib.IMAP4(host)
    imap.login(username, password)
    imap.select('INBOX')

    #if sender_of_interest:
     #   status, response = imap.uid('search', None, 'UNSEEN', 'FROM {0}'.format(sender_of_interest))
   # else:
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
        data_list.append(data_dict)
        print('ddata_list ======', data_list)
        exp_data_from_email(data_list)

#Проверка почтового ящика каждые 60 секунд
def start():
    i = 1
    while i !=0:
        from_ = get_param('email', 'from')
        passw = get_param('email', 'pass')
        host = get_param('email', 'host')
        read(from_, passw, host)
        time.sleep(60)


if __name__ == '__main__':
    start()




