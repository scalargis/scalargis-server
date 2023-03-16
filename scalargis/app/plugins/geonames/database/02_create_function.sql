CREATE OR REPLACE FUNCTION geonames.search_geonames(_filter text, _group text DEFAULT NULL::text, _admin_level1 text DEFAULT NULL::text, _admin_level2 text DEFAULT NULL::text, _admin_level3 text DEFAULT NULL::text, _maxrows integer DEFAULT 18, _min_similarity real DEFAULT 0)
 RETURNS TABLE(id integer, geom_wkt text, name text, source text, type text, "group" text, admin_level1 text, admin_level2 text, admin_level3 text, admin_level4 text, admin_code text, similarity real, search_func text)
 LANGUAGE plpgsql
 ROWS 10
AS $function$
declare
	f text;
	fts text;
	mysql text;
	f_is_integer boolean;
	x integer;
begin
	f = lower(unaccent(_filter));
	fts = replace(f,' ','&');
	fts = rtrim(fts,'&');
	fts = ltrim(fts,'&');

	Begin
	    x = $1::Integer;
	    f_is_integer = TRUE;
	EXCEPTION WHEN others THEN
	    f_is_integer = FALSE;
	End;

	mysql = 'with t as (
			Select * from geonames.geographical_names Where 1=1 ';

	if (_group Is Not Null) Then
		mysql = mysql || ' and group like ''' || _group::text ||'''';
	end if;
	if (_admin_level1 Is Not Null) Then
		mysql = mysql || ' and admin_level1 like ''' || _admin_level1::text ||'''';
	end if;
	if (_admin_level2 Is Not Null) Then
		mysql = mysql || ' and admin_level2 like ''' || _admin_level2::text ||'''';
	end if;
	if (_admin_level3 Is Not Null) Then
		mysql = mysql || ' and admin_level3 like ''' || _admin_level3::text ||'''';
	end if;


	mysql = mysql || '), q as
		(
			(
			SELECT geom, name, source, type, "group", admin_level1, admin_level2, admin_level3, admin_level4, admin_code,
			similarity(name, '''||f||''') as similarity, ''similarity'' as search_func
			FROM t
			)
		';
	If (not f_is_integer) Then
		mysql = mysql || '
			Union All
				(
				SELECT geom, name, source, type, "group", admin_level1, admin_level2, admin_level3, admin_level4, admin_code,
				 (ts_rank(fs_str, to_tsquery(''pt'','''||fts||''')) + 0.8)::real AS similarity, ''full_ts'' as search_func
				from t
				where fs_str @@ to_tsquery(''pt'','''||fts||''')
				)';
	else
		mysql = mysql || '
			Union All
				(
				SELECT geom, name, source, type, "group", admin_level1, admin_level2, admin_level3, admin_level4, admin_code,
				 (ts_rank(fs_str, to_tsquery(''pt'','''||fts||''')) + 0.8)::real AS similarity, ''full_ts'' as search_func
				from t
				where admin_code @@ to_tsquery('''||fts||':*'')
				)
			';
	end if;

	mysql = mysql || ')
		SELECT row_number() OVER ()::integer AS id, St_Astext(geom), name, source,
		type, "group", admin_level1, admin_level2, admin_level3, admin_level4, admin_code,
		sum(similarity),max(search_func) from q
		group by St_Astext(geom), name, source, type, "group", admin_level1, admin_level2, admin_level3, admin_level4, admin_code
		having sum(similarity) > ' || _min_similarity::text;

	mysql = mysql || ' order by  sum(similarity) desc, name';



	if (_maxrows>0) Then mysql = mysql || ' Limit ' || _maxrows::text; end if;

	--raise notice 'sql= %',mysql;

	return query execute mysql;

end;
$function$
;

-- Permissions

ALTER FUNCTION geonames.search_geonames(text, text, text, text, text, int4, float4) OWNER TO postgres;
GRANT ALL ON FUNCTION geonames.search_geonames(text, text, text, text, text, int4, float4) TO public;
GRANT ALL ON FUNCTION geonames.search_geonames(text, text, text, text, text, int4, float4) TO postgres;