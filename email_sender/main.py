import pika
import json
import smtplib
from email.mime.text import MIMEText
from config import RABBITMQ_URL, EMAIL_PASSWORD, EMAIL_ADDRESS

connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
channel = connection.channel()
channel.queue_declare(queue='email_notifications')


def send_email(email, journal_name, post_content, datetime_):
    msg = MIMEText(f"Новый пост в журнале '{journal_name}' от {datetime_}:\n\n{post_content}")
    msg['Subject'] = f"Новый пост в журнале '{journal_name}'"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def callback(ch, method, properties, body):
    message = json.loads(body)
    emails = message['emails']
    journal_name = message['journal_name']
    post_content = message['post_content']
    datetime_ = message['datetime']

    for email in emails:
        send_email(email, journal_name, post_content, datetime_)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"Messages for journal {journal_name} was sended!")


channel.basic_consume(queue='email_notifications', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
