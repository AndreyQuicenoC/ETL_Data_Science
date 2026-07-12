from sqlalchemy import Engine, text


def new_data(conne: Engine) -> bool:
    queryo = text('select saved from hecho_servicios order by saved desc limit 1;')
    queryt = text(''' select date from dim_fecha where key_dim_fecha =
    (select key_dim_fecha from hecho_servicios order by key_hecho_servicios desc limit 1) ;''')
    with conne.connect() as con:
        try:
            rs1 = con.execute(queryo)
            rs2 = con.execute(queryt)
            lastupdate = rs1.fetchone()
            lastdate = rs2.fetchone()
            if lastupdate is None or lastdate is None:
                return True
            date_val = lastdate[0]
            if hasattr(date_val, 'date'):
                date_val = date_val.date()
            if date_val > lastupdate[0]:
                return True
            print(f'''No hay datos nuevos desde la ultima fecha de carga {lastupdate}''')
            return False
        except Exception as e:
            print('[*]', e)
            return True


def ensure_olap_database(admin_cfg: dict, etl_cfg: dict) -> None:
    from sqlalchemy import create_engine

    dbname = etl_cfg['dbname']
    owner = etl_cfg['user']
    url = (f"{admin_cfg['drivername']}://{admin_cfg['user']}:{admin_cfg['password']}"
           f"@{admin_cfg['host']}:{admin_cfg['port']}/{admin_cfg['dbname']}")
    admin = create_engine(url, isolation_level='AUTOCOMMIT')
    with admin.connect() as conn:
        exists = conn.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :n'), {'n': dbname}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{dbname}" OWNER "{owner}"'))
        conn.execute(text(f'GRANT ALL PRIVILEGES ON DATABASE "{dbname}" TO "{owner}"'))

    olap_admin = create_engine(
        f"{admin_cfg['drivername']}://{admin_cfg['user']}:{admin_cfg['password']}"
        f"@{admin_cfg['host']}:{admin_cfg['port']}/{dbname}",
        isolation_level='AUTOCOMMIT',
    )
    with olap_admin.connect() as conn:
        conn.execute(text(f'GRANT ALL ON SCHEMA public TO "{owner}"'))
        try:
            conn.execute(text(f'ALTER SCHEMA public OWNER TO "{owner}"'))
        except Exception as e:
            print('[*]', e)


def push_dimensions(co_sa, etl_conn):
    from etl import extract, transform, load

    dim_ubicacion = extract.extract_ubicacion(co_sa)
    dim_mensajero = extract.extract_mensajero(co_sa)
    dim_estado = extract.extract_estado(co_sa)
    dim_tipo_novedad = extract.extract_tipo_novedad(co_sa)

    # transform
    dim_ubicacion = transform.transform_ubicacion(dim_ubicacion)
    dim_mensajero = transform.transform_mensajero(dim_mensajero)
    dim_estado = transform.transform_estado(dim_estado)
    dim_tipo_novedad = transform.transform_tipo_novedad(dim_tipo_novedad)
    dim_fecha = transform.transform_fecha()
    dim_tiempo = transform.transform_tiempo()

    load.load(dim_fecha, etl_conn, 'dim_fecha', True)
    load.load(dim_tiempo, etl_conn, 'dim_tiempo', True)
    load.load(dim_ubicacion, etl_conn, 'dim_ubicacion', True)
    load.load(dim_mensajero, etl_conn, 'dim_mensajero', True)
    load.load(dim_estado, etl_conn, 'dim_estado', True)
    load.load(dim_tipo_novedad, etl_conn, 'dim_tipo_novedad', True)
