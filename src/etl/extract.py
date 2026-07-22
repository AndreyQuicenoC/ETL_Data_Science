import pandas as pd
from sqlalchemy.engine import Engine


def extract(tables: list, conection: Engine):
    """
    :param conection: the connection to the database
    :param tables: the tables to extract
    :return: a list of tables in df format
    """
    a = []
    for i in tables:
        aux = pd.read_sql_table(i, conection)
        a.append(aux)
    return a


def extract_ubicacion(conection: Engine):
    """Extract sede / cliente / ciudad / departamento for dim_ubicacion."""
    sede = pd.read_sql_query(
        """
        SELECT s.sede_id, s.nombre AS sede_nombre, s.direccion AS sede_direccion,
               s.telefono AS sede_telefono, s.cliente_id, s.ciudad_id
        FROM sede s
        """,
        conection,
    )
    cliente = pd.read_sql_query(
        """
        SELECT c.cliente_id, c.nombre AS nombre_cliente, c.nit_cliente,
               c.sector AS sector_cliente, tc.nombre AS tipo_cliente
        FROM cliente c
        LEFT JOIN tipo_cliente tc ON tc.tipo_cliente_id = c.tipo_cliente_id
        """,
        conection,
    )
    ciudad = pd.read_sql_query(
        """
        SELECT ci.ciudad_id, ci.nombre AS ciudad, ci.departamento_id,
               d.nombre AS departamento
        FROM ciudad ci
        LEFT JOIN departamento d ON d.departamento_id = ci.departamento_id
        """,
        conection,
    )
    return [sede, cliente, ciudad]


def extract_mensajero(conection: Engine):
    """Extract messengers with user profile, city and most-used vehicle."""
    mensajero = pd.read_sql_query(
        """
        SELECT m.id AS id_mensajero,
               m.user_id,
               m.activo,
               m.telefono,
               m.ciudad_operacion_id AS id_ciudad_operacion,
               u.username,
               TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS nombre,
               c.nombre AS ciudad_operacion
        FROM clientes_mensajeroaquitoy m
        LEFT JOIN auth_user u ON u.id = m.user_id
        LEFT JOIN ciudad c ON c.ciudad_id = m.ciudad_operacion_id
        """,
        conection,
    )
    vehiculo = pd.read_sql_query(
        """
        SELECT s.mensajero_id AS id_mensajero, tv.nombre AS tipo_vehiculo, COUNT(*) AS n
        FROM mensajeria_servicio s
        JOIN mensajeria_tipovehiculo tv ON tv.id = s.tipo_vehiculo_id
        WHERE s.mensajero_id IS NOT NULL
        GROUP BY s.mensajero_id, tv.nombre
        """,
        conection,
    )
    # Vehicle counts are used later to pick each messenger's most common vehicle type.
    return [mensajero, vehiculo]


def extract_estado(conection: Engine):
    return pd.read_sql_table("mensajeria_estado", conection)


def extract_tipo_novedad(conection: Engine):
    return pd.read_sql_table("mensajeria_tiponovedad", conection)


def extract_servicios_oltp(conection: Engine):
    """Extract services, state history, documents and usuario-sede mapping."""
    servicios = pd.read_sql_query(
        """
        SELECT s.id AS id_servicio,
               s.fecha_solicitud,
               s.hora_solicitud,
               s.mensajero_id AS id_mensajero,
               s.cliente_id AS id_cliente,
               s.usuario_id,
               s.es_prueba,
               s.activo,
               u.sede_id AS id_sede
        FROM mensajeria_servicio s
        LEFT JOIN clientes_usuarioaquitoy u ON u.id = s.usuario_id
        """,
        conection,
    )
    # State history rows are used to measure how long each service phase took.
    estados = pd.read_sql_query(
        """
        SELECT es.servicio_id AS id_servicio,
               es.estado_id AS id_estado,
               es.fecha,
               es.hora,
               es.es_prueba AS es_prueba_estado,
               e.nombre AS nombre_estado
        FROM mensajeria_estadosservicio es
        JOIN mensajeria_estado e ON e.id = es.estado_id
        """,
        conection,
    )
    documentos = pd.read_sql_query(
        """
        SELECT servicio_id AS id_servicio, COUNT(*) AS cantidad_paquetes
        FROM mensajeria_documentoasociado
        GROUP BY servicio_id
        """,
        conection,
    )
    return [servicios, estados, documentos]


def extract_novedades_oltp(conection: Engine):
    """Extract service incidents with service context for location/messenger."""
    novedades = pd.read_sql_query(
        """
        SELECT n.id AS id_novedad,
               n.fecha_novedad,
               n.tipo_novedad_id AS id_tipo_novedad,
               n.servicio_id AS id_servicio,
               n.mensajero_id AS id_mensajero,
               n.es_prueba,
               n.descripcion,
               s.cliente_id AS id_cliente,
               s.usuario_id,
               u.sede_id AS id_sede
        FROM mensajeria_novedadesservicio n
        LEFT JOIN mensajeria_servicio s ON s.id = n.servicio_id
        LEFT JOIN clientes_usuarioaquitoy u ON u.id = s.usuario_id
        """,
        conection,
    )
    return novedades


def extract_hecho_servicios(etl_conn: Engine, oltp_conn: Engine):
    """Extract OLTP service sources plus already-loaded dimensions from OLAP."""
    servicios, estados, documentos = extract_servicios_oltp(oltp_conn)
    # Dimensions are read from OLAP to map business ids to warehouse surrogate keys.
    dim_fecha = pd.read_sql_table("dim_fecha", etl_conn)
    dim_tiempo = pd.read_sql_table("dim_tiempo", etl_conn)
    dim_ubicacion = pd.read_sql_table("dim_ubicacion", etl_conn)
    dim_mensajero = pd.read_sql_table("dim_mensajero", etl_conn)
    dim_estado = pd.read_sql_table("dim_estado", etl_conn)
    return [servicios, estados, documentos, dim_fecha, dim_tiempo,
            dim_ubicacion, dim_mensajero, dim_estado]


def extract_hecho_novedades(etl_conn: Engine, oltp_conn: Engine):
    """Extract OLTP incidents plus already-loaded dimensions from OLAP."""
    novedades = extract_novedades_oltp(oltp_conn)
    # Dimensions are read from OLAP to map business ids to warehouse surrogate keys.
    dim_fecha = pd.read_sql_table("dim_fecha", etl_conn)
    dim_tiempo = pd.read_sql_table("dim_tiempo", etl_conn)
    dim_ubicacion = pd.read_sql_table("dim_ubicacion", etl_conn)
    dim_mensajero = pd.read_sql_table("dim_mensajero", etl_conn)
    dim_tipo_novedad = pd.read_sql_table("dim_tipo_novedad", etl_conn)
    dim_estado = pd.read_sql_table("dim_estado", etl_conn)
    return [novedades, dim_fecha, dim_tiempo, dim_ubicacion,
            dim_mensajero, dim_tipo_novedad, dim_estado]
