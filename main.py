import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect
import yaml
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from etl import extract, transform, load, utils_etl

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)


with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)
    config_co = config['OLTP']
    config_etl = config['ETL_PRO']

# Construct the database URL
url_co = (f"{config_co['drivername']}://{config_co['user']}:{config_co['password']}@{config_co['host']}:"
          f"{config_co['port']}/{config_co['dbname']}")
url_etl = (f"{config_etl['drivername']}://{config_etl['user']}:{config_etl['password']}@{config_etl['host']}:"
           f"{config_etl['port']}/{config_etl['dbname']}")
# Create the SQLAlchemy Engine
co_sa = create_engine(url_co)
etl_conn = create_engine(url_etl)

if config.get('ADMIN'):
    utils_etl.ensure_olap_database(config['ADMIN'], config_etl)

inspector = inspect(etl_conn)
tnames = inspector.get_table_names()

if not tnames:
    conn = psycopg2.connect(dbname=config_etl['dbname'], user=config_etl['user'], password=config_etl['password'],
                            host=config_etl['host'], port=config_etl['port'])
    cur = conn.cursor()
    with open('sqlscripts.yml', 'r') as f:
        sql = yaml.safe_load(f)
        for key, val in sql.items():
            cur.execute(val)
            conn.commit()
    cur.close()
    conn.close()

if config.get('FORCE_RELOAD', False) or utils_etl.new_data(etl_conn):

    if config['LOAD_DIMENSIONS']:
        load.truncate_warehouse(etl_conn)

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

    # hecho servicios
    hecho_servicios = extract.extract_hecho_servicios(etl_conn, co_sa)
    hecho_servicios = transform.transform_hecho_servicios(hecho_servicios)
    load.load_hecho_servicios(hecho_servicios, etl_conn, True)
    print('Done servicios fact')

    # hecho novedades
    hecho_novedades = extract.extract_hecho_novedades(etl_conn, co_sa)
    hecho_novedades = transform.transform_hecho_novedades(hecho_novedades)
    load.load_hecho_novedades(hecho_novedades, etl_conn, True)
    print('Done novedades fact')

    print('success all facts loaded')
else:
    print('done not new data')

#%%
