import logging
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
from app.database import db
from app.models.mapas import SiteSettings
from app.utils.decorators import async_task


def send_mail(app, receiver_email, subject, message_text, attachments=None):
    try:
        logger = logging.getLogger(__name__)

        mail_settings = get_mail_settings()

        if mail_settings.get('smtp_server') and mail_settings.get('smtp_port'):
            message = MIMEMultipart("alternative")
            message.set_charset('utf8')

            message["Subject"] = subject
            message["From"] = mail_settings.get('sender_email')
            message["To"] = ','.join(receiver_email)

            # Turn these into plain/html MIMEText objects
            #part_text = MIMEText(text, "plain")
            part_html = MIMEText(message_text.encode('utf-8'), 'html', 'UTF-8')

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            #message.attach(part_text)
            message.attach(part_html)

            if attachments is not None:
                for f in attachments:
                    part = MIMEBase('application', "octet-stream")
                    with open(f.get('filepath'), 'rb') as file:
                        part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    'attachment; filename={}'.format(f.get('filename')))
                    message.attach(part)

            if mail_settings:
                send_async_message(app, mail_settings, receiver_email, message)

    except Exception as e:
        logger.exception("message")


@async_task
def send_async_message(app, mail_settings, receiver_email, message):
    with app.app_context():
        with smtplib.SMTP(mail_settings.get('smtp_server'), mail_settings.get('smtp_port')) as server:
            if mail_settings.get('smtp_username'):
                server.login(mail_settings.get('smtp_username'), mail_settings.get('smtp_password'))

            for to_email in receiver_email:
                server.sendmail(
                    mail_settings.get('smtp_username'), to_email, message.as_string().encode('utf-8')
                )


def get_mail_settings():
    site_settings = {}
    st = db.session.query(SiteSettings).all()

    if 'SMTP_SERVER' in current_app.config.keys():
        site_settings['smtp_server'] = current_app.config['SMTP_SERVER']
    if 'SMTP_PORT' in current_app.config.keys():
        site_settings['smtp_port'] = current_app.config['SMTP_PORT']
    if 'USE_SSL_EMAIL' in current_app.config.keys():
        site_settings['use_ssl_email'] = current_app.config['USE_SSL_EMAIL']
    if 'SMTP_USERNAME' in current_app.config.keys():
        site_settings['smtp_username'] = current_app.config['SMTP_USERNAME']
    if 'SMTP_PASSWORD' in current_app.config.keys():
        site_settings['smtp_password'] = current_app.config['SMTP_PASSWORD']
    if 'SENDER_EMAIL' in current_app.config.keys():
        site_settings['sender_email'] = current_app.config['SENDER_EMAIL']

    for r in st:
        if r.code.lower() in ['smtp_server', 'smtp_port', 'use_ssl_email', 'smtp_username', 'smtp_password']:
            if r.setting_value:
                if r.code.lower() == 'use_ssl_email':
                    if r.code.lower() == 'true':
                        site_settings[r.code] = True
                    elif r.code.lower() == 'false':
                        site_settings[r.code] = False
                else:
                    site_settings[r.code] = r.setting_value

    return site_settings