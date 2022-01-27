SET search_path = portal, pg_catalog;

-- Function: portal.change_trigger()
-- DROP FUNCTION portal.change_trigger();
CREATE OR REPLACE FUNCTION portal.change_trigger()
  RETURNS trigger AS
$BODY$
        BEGIN
                IF      TG_OP = 'INSERT'
                THEN
                        INSERT INTO portal.log_history (tabname, schemaname, operation, new_val)
                                VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP, row_to_json(NEW));
                        RETURN NEW;

                ELSIF   TG_OP = 'UPDATE'
                THEN
                        INSERT INTO portal.log_history (tabname, schemaname, operation, new_val, old_val)
                                VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP,
                                       row_to_json(NEW), row_to_json(OLD));
                        RETURN NEW;
                ELSIF   TG_OP = 'DELETE'
                THEN
                        INSERT INTO portal.log_history (tabname, schemaname, operation, old_val)
                                VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP, row_to_json(OLD));
                        RETURN OLD;
                END IF;
        END;
$BODY$
  LANGUAGE plpgsql VOLATILE SECURITY DEFINER
  COST 100;

CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON configuracao_mapa FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON mapa FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON planta FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON tipo_planta FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON sub_planta FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON planta_layouts FOR EACH ROW EXECUTE PROCEDURE change_trigger();
CREATE TRIGGER t BEFORE INSERT OR DELETE OR UPDATE ON "user" FOR EACH ROW EXECUTE PROCEDURE change_trigger();