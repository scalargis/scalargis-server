ALTER TABLE portal.mapa ADD COLUMN send_email_notifications_admin boolean;
ALTER TABLE portal.mapa ADD COLUMN email_notifications_admin character varying;

ALTER TABLE portal.contacto_mensagem ADD COLUMN mensagem_uuid character varying;