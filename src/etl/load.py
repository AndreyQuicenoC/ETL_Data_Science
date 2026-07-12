from pandas import DataFrame
from sqlalchemy.engine import Engine
from sqlalchemy import text


def load_hecho_servicios(hecho_servicios: DataFrame, etl_conn: Engine, replace: bool = False):
    load(hecho_servicios, etl_conn, 'hecho_servicios', replace)


def load_hecho_novedades(hecho_novedades: DataFrame, etl_conn: Engine, replace: bool = False):
    load(hecho_novedades, etl_conn, 'hecho_novedades', replace)


def truncate_warehouse(etl_conn: Engine):
    order = [
        'hecho_novedades',
        'hecho_servicios',
        'dim_tipo_novedad',
        'dim_estado',
        'dim_mensajero',
        'dim_ubicacion',
        'dim_tiempo',
        'dim_fecha',
    ]
    with etl_conn.begin() as conn:
        for tname in order:
            conn.execute(text(f'Delete from {tname}'))


def load(table: DataFrame, etl_conn: Engine, tname, replace: bool = False):
    """
    :param table: table to load into the database
    :param etl_conn: sqlalchemy engine to connect to the database
    :param tname: table name to load into the database
    :param replace: when true it deletes existing table data(rows)
    :return: void it just load the table to the database
    """
    if replace:
        with etl_conn.begin() as conn:
            conn.execute(text(f'Delete from {tname}'))
        table.to_sql(f'{tname}', etl_conn, if_exists='append', index=False)
    else:
        table.to_sql(f'{tname}', etl_conn, if_exists='append', index=False)
