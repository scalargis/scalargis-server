import logging
import os
import smtplib
import socket
import ssl
from email import charset, encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

from flask import current_app, has_app_context

from app.database import db
from app.models.portal import SiteSettings
from app.utils.decorators import async_task


logger = logging.getLogger(__name__)

STARTTLS_MODES = ('never', 'auto', 'required')
DEFAULT_STARTTLS = 'never'
DEFAULT_TIMEOUT = 15

_CONFIG_KEYS = {
    'smtp_server': 'SCALARGIS_SMTP_SERVER',
    'smtp_port': 'SCALARGIS_SMTP_PORT',
    'use_ssl_email': 'SCALARGIS_USE_SSL_EMAIL',
    'smtp_username': 'SCALARGIS_SMTP_USERNAME',
    'smtp_password': 'SCALARGIS_SMTP_PASSWORD',
    'sender_username': 'SCALARGIS_SENDER_USERNAME',
    'sender_email': 'SCALARGIS_SENDER_EMAIL',
}

_DB_KEYS = ('smtp_server', 'smtp_port', 'use_ssl_email', 'smtp_username', 'smtp_password')


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ('true', '1', 'yes', 'on'):
        return True
    if text in ('false', '0', 'no', 'off'):
        return False
    return None


def get_mail_settings():
    """Return SMTP settings from the Flask config, overridden by site_settings rows."""
    site_settings = {}
    config = current_app.config

    for key, config_key in _CONFIG_KEYS.items():
        if config_key in config:
            site_settings[key] = config[config_key]

    for r in db.session.query(SiteSettings).all():
        code = (r.code or '').lower()
        if code not in _DB_KEYS or not r.setting_value:
            continue
        if code == 'use_ssl_email':
            parsed = _parse_bool(r.setting_value)
            if parsed is not None:
                site_settings[code] = parsed
        else:
            site_settings[code] = r.setting_value

    return site_settings


def _resolve_starttls(settings):
    config = current_app.config
    if 'SCALARGIS_SMTP_STARTTLS' in config:
        mode = str(config['SCALARGIS_SMTP_STARTTLS'] or '').strip().lower()
        return mode if mode in STARTTLS_MODES else None
    if _parse_bool(settings.get('use_ssl_email')):
        return 'required'
    return DEFAULT_STARTTLS


def _resolve_timeout():
    try:
        timeout = float(current_app.config.get('SCALARGIS_SMTP_TIMEOUT', DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT
    return timeout if timeout > 0 else DEFAULT_TIMEOUT


def _resolve_port(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _looks_like_email(value):
    if not value or not isinstance(value, str):
        return False
    local, _, domain = value.strip().rpartition('@')
    return bool(local) and '.' in domain and not domain.endswith('.')


def _resolve_sender(settings):
    display, address = parseaddr(settings.get('sender_email') or '')
    sender_username = (settings.get('sender_username') or '').strip()

    if not _looks_like_email(address) and _looks_like_email(sender_username):
        address = sender_username
    if not display and sender_username and '@' not in sender_username:
        display = sender_username

    if not _looks_like_email(address):
        return None, None
    return display or None, address


def get_connection_settings():
    """Return the resolved SMTP connection settings, or None when mail is not configured."""
    settings = get_mail_settings()

    server = settings.get('smtp_server')
    port = _resolve_port(settings.get('smtp_port'))
    if not server or not port:
        return None

    starttls = _resolve_starttls(settings)
    display, address = _resolve_sender(settings)

    return {
        'smtp_server': server,
        'smtp_port': port,
        'smtp_username': settings.get('smtp_username') or None,
        'smtp_password': settings.get('smtp_password') or '',
        'starttls': starttls,
        'tls_verify': _parse_bool(current_app.config.get('SCALARGIS_SMTP_TLS_VERIFY', True)) is not False,
        'timeout': _resolve_timeout(),
        'sender_display': display,
        'sender_email': address,
    }


def _text_part(body, subtype):
    cs = charset.Charset('utf-8')
    cs.body_encoding = charset.QP
    return MIMEText(body, subtype, cs)


def _attach_inline_image(container, image):
    filepath = image.get('filepath')
    cid = image.get('cid')
    filename = image.get('filename') or (os.path.basename(filepath) if filepath else cid)
    mimetype = image.get('mimetype') or 'image/png'
    subtype = mimetype.split('/', 1)[1] if '/' in mimetype else 'png'

    if not filepath or not os.path.isfile(filepath):
        logger.warning('Send mail: inline image missing on disk: cid=%s path=%s', cid, filepath)
        return

    with open(filepath, 'rb') as fh:
        part = MIMEImage(fh.read(), _subtype=subtype)
    part.add_header('Content-ID', '<{}>'.format(cid))
    part.add_header('Content-Disposition', 'inline', filename=filename)
    container.attach(part)


def _attach_file(container, attachment):
    filepath = attachment.get('filepath')
    filename = attachment.get('filename') or os.path.basename(filepath)

    part = MIMEBase('application', 'octet-stream')
    with open(filepath, 'rb') as fh:
        part.set_payload(fh.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    container.attach(part)


def build_message(*, subject, html_body, text_body=None, recipients, sender_email,
                  sender_display=None, inline_images=None, attachments=None):
    """Build the MIME tree: alternative text/html, wrapped in related when inline images exist."""
    alternative = MIMEMultipart('alternative')
    if text_body:
        alternative.attach(_text_part(text_body, 'plain'))
    if html_body or not text_body:
        alternative.attach(_text_part(html_body or '', 'html'))

    images = list(inline_images or [])
    if images:
        outer = MIMEMultipart('related')
        outer.attach(alternative)
        for image in images:
            _attach_inline_image(outer, image)
    else:
        outer = alternative

    outer['Subject'] = subject
    outer['From'] = formataddr((sender_display, sender_email)) if sender_display else sender_email
    outer['To'] = ', '.join(recipients)

    for attachment in attachments or []:
        _attach_file(outer, attachment)

    return outer


def _tls_context(verify):
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def deliver(message, recipients, conn):
    """Open one SMTP session and send the message. Return True when at least one recipient is accepted."""
    host = conn['smtp_server']
    port = conn['smtp_port']
    mode = conn['starttls']
    username = conn['smtp_username']

    try:
        with smtplib.SMTP(host, port, timeout=conn['timeout']) as smtp:
            smtp.ehlo()
            tls_active = False

            if mode in ('auto', 'required'):
                if smtp.has_extn('starttls'):
                    try:
                        smtp.starttls(context=_tls_context(conn['tls_verify']))
                        smtp.ehlo()
                    except Exception as e:
                        logger.error('Send mail: STARTTLS failed host=%s:%s mode=%s, send aborted: %s',
                                     host, port, mode, e)
                        return False
                    tls_active = True
                elif mode == 'required':
                    logger.error('Send mail: STARTTLS required but not offered by host=%s:%s, send aborted',
                                 host, port)
                    return False
                else:
                    logger.info('Send mail: no STARTTLS offered by host=%s:%s, sending plaintext', host, port)

            if username:
                if not tls_active:
                    logger.warning('Send mail: SMTP login as %r without TLS to host=%s:%s', username, host, port)
                smtp.login(username, conn['smtp_password'])

            refused = smtp.send_message(message, from_addr=conn['sender_email'], to_addrs=recipients)

            for rcpt, (code, reason) in (refused or {}).items():
                logger.error('Send mail: recipient refused to=%s code=%s reason=%r', rcpt, code, reason)
            delivered = [r for r in recipients if r not in (refused or {})]
            logger.info('Send mail: delivered host=%s:%s tls=%s subject=%r to=%s',
                        host, port, tls_active, message.get('Subject'), ', '.join(delivered))
            return True

    except smtplib.SMTPRecipientsRefused as e:
        for rcpt, (code, reason) in (e.recipients or {}).items():
            logger.error('Send mail: recipient refused to=%s code=%s reason=%r', rcpt, code, reason)
    except smtplib.SMTPSenderRefused as e:
        logger.error('Send mail: sender refused code=%s sender=%r: %r', e.smtp_code, e.sender, e.smtp_error)
    except smtplib.SMTPResponseException as e:
        logger.error('Send mail: server refused host=%s:%s code=%s: %r', host, port, e.smtp_code, e.smtp_error)
    except socket.timeout:
        logger.error('Send mail: timeout host=%s:%s', host, port)
    except (smtplib.SMTPException, OSError) as e:
        logger.error('Send mail: SMTP failure host=%s:%s: %s', host, port, e)
    except Exception:
        logger.exception('Send mail: unexpected failure host=%s:%s', host, port)
    return False


@async_task
def _deliver_async(app, message, recipients, conn):
    with app.app_context():
        deliver(message, recipients, conn)


def _dispatch(app, *, subject, html_body, text_body, recipients, inline_images, attachments):
    if isinstance(recipients, str):
        recipients = [recipients]
    recipient_list = [r.strip() for r in (recipients or []) if r and r.strip()]
    if not recipient_list:
        logger.warning('Send mail: no recipients, subject=%r', subject)
        return False

    try:
        conn = get_connection_settings()
    except Exception as e:
        logger.error('Send mail: could not load settings: %s', e)
        return False

    if conn is None:
        logger.info('Send mail: SMTP not configured, skipped subject=%r', subject)
        return False
    if conn['starttls'] is None:
        logger.error('Send mail: invalid SCALARGIS_SMTP_STARTTLS %r, expected one of %s',
                     current_app.config.get('SCALARGIS_SMTP_STARTTLS'), ', '.join(STARTTLS_MODES))
        return False
    if not conn['sender_email']:
        logger.error('Send mail: no valid sender address, skipped subject=%r', subject)
        return False

    try:
        message = build_message(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=recipient_list,
            sender_email=conn['sender_email'],
            sender_display=conn['sender_display'],
            inline_images=inline_images,
            attachments=attachments,
        )
    except Exception as e:
        logger.error('Send mail: message build failed: %s', e)
        return False

    try:
        _deliver_async(app, message, recipient_list, conn)
    except Exception as e:
        logger.error('Send mail: async hand-off failed: %s', e)
        return False
    return True


def send_email(*, subject, html_body, text_body=None, recipients, inline_images=None, attachments=None):
    """Build and dispatch a mail in a worker thread. Return True on hand-off. Never raise."""
    try:
        app = current_app._get_current_object()
        return _dispatch(app, subject=subject, html_body=html_body, text_body=text_body,
                         recipients=recipients, inline_images=inline_images, attachments=attachments)
    except Exception as e:
        logger.error('Send mail: %s', e)
        return False


def send_mail(app, receiver_email, subject, message_html, message_text=None, attachments=None):
    """Legacy entry point. Wrap send_email with the given app."""
    try:
        if has_app_context():
            return _dispatch(app, subject=subject, html_body=message_html, text_body=message_text,
                             recipients=receiver_email, inline_images=None, attachments=attachments)
        with app.app_context():
            return _dispatch(app, subject=subject, html_body=message_html, text_body=message_text,
                             recipients=receiver_email, inline_images=None, attachments=attachments)
    except Exception as e:
        logger.error('Send mail: %s', e)
        return False
