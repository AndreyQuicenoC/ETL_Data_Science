from datetime import date, datetime, timedelta

import holidays
import numpy as np
import pandas as pd
from pandas import DataFrame

# Operational state ids in mensajeria_estado
ESTADO_INICIADO = 1
ESTADO_ASIGNADO = 2
ESTADO_NOVEDAD = 3
ESTADO_RECOGIDO = 4
ESTADO_ENTREGADO = 5
ESTADO_CERRADO = 6

NA_TEXT = "NO APLICA"


def _fill_text_nulls(df: DataFrame, columns=None) -> DataFrame:
    """Replace null/blank values so downstream merges and loads do not fail."""
    cols = columns if columns is not None else df.select_dtypes(include=["object", "string"]).columns
    for col in cols:
        if col not in df.columns:
            continue
        df[col] = df[col].replace({"": NA_TEXT, " ": NA_TEXT, None: NA_TEXT})
        df[col] = df[col].fillna(NA_TEXT)
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col].isin(["", "nan", "None", "NaT"]), col] = NA_TEXT
    return df


def _franja_horaria(hora: int) -> str:
    """Business time slots (exact minutes are not required)."""
    if pd.isna(hora):
        return NA_TEXT
    h = int(hora)
    if 0 <= h <= 5:
        return "Madrugada (00-05)"
    if 6 <= h <= 11:
        return "Manana (06-11)"
    if 12 <= h <= 17:
        return "Tarde (12-17)"
    return "Noche (18-23)"


def _periodo_dia(hora: int) -> str:
    if pd.isna(hora):
        return NA_TEXT
    h = int(hora)
    if 5 <= h < 12:
        return "AM"
    if 12 <= h < 19:
        return "PM"
    return "Nocturno"


def transform_fecha(start: str = "2023-01-01", end: str = "2025-12-31") -> DataFrame:
    dim_fecha = pd.DataFrame({"date": pd.date_range(start=start, end=end, freq="D")})
    dim_fecha["year"] = dim_fecha["date"].dt.year
    dim_fecha["month"] = dim_fecha["date"].dt.month
    dim_fecha["day"] = dim_fecha["date"].dt.day
    dim_fecha["weekday"] = dim_fecha["date"].dt.weekday
    dim_fecha["quarter"] = dim_fecha["date"].dt.quarter
    dim_fecha["day_of_year"] = dim_fecha["date"].dt.day_of_year
    dim_fecha["day_of_month"] = dim_fecha["date"].dt.days_in_month
    dim_fecha["month_str"] = dim_fecha["date"].dt.month_name()
    dim_fecha["day_str"] = dim_fecha["date"].dt.day_name()
    dim_fecha["date_str"] = dim_fecha["date"].dt.strftime("%d/%m/%Y")
    co_holidays = holidays.CO(language="es")
    dim_fecha["is_Holiday"] = dim_fecha["date"].apply(lambda x: x in co_holidays)
    dim_fecha["holiday"] = dim_fecha["date"].apply(lambda x: co_holidays.get(x))
    dim_fecha["holiday"] = dim_fecha["holiday"].fillna(NA_TEXT)
    dim_fecha["weekend"] = dim_fecha["weekday"].apply(lambda x: x > 4)
    dim_fecha["saved"] = date.today()
    return dim_fecha


def transform_tiempo() -> DataFrame:
    dim_tiempo = pd.DataFrame({"hora": list(range(24))})
    dim_tiempo["franja_horaria"] = dim_tiempo["hora"].apply(_franja_horaria)
    dim_tiempo["periodo_dia"] = dim_tiempo["hora"].apply(_periodo_dia)
    dim_tiempo["saved"] = date.today()
    return dim_tiempo


def transform_ubicacion(args) -> DataFrame:
    sede, cliente, ciudad = args
    dim = sede.merge(cliente, on="cliente_id", how="left")
    dim = dim.merge(ciudad, on="ciudad_id", how="left")
    dim.rename(
        columns={
            "sede_id": "id_sede",
            "cliente_id": "id_cliente",
            "ciudad_id": "id_ciudad",
            "departamento_id": "id_departamento",
        },
        inplace=True,
    )
    dim = _fill_text_nulls(dim)
    for col in ["id_sede", "id_cliente", "id_ciudad", "id_departamento"]:
        dim[col] = dim[col].fillna(-1).astype("Int64")

    # Unknown member for services/novedades without sede
    unknown = pd.DataFrame(
        [{
            "id_sede": -1,
            "sede_nombre": NA_TEXT,
            "sede_direccion": NA_TEXT,
            "sede_telefono": NA_TEXT,
            "id_cliente": -1,
            "nombre_cliente": NA_TEXT,
            "nit_cliente": NA_TEXT,
            "sector_cliente": NA_TEXT,
            "tipo_cliente": NA_TEXT,
            "id_ciudad": -1,
            "ciudad": NA_TEXT,
            "id_departamento": -1,
            "departamento": NA_TEXT,
        }]
    )
    dim = pd.concat([unknown, dim], ignore_index=True)
    dim["saved"] = date.today()
    dim.reset_index(drop=True, inplace=True)
    return dim


def transform_mensajero(args) -> DataFrame:
    mensajero, vehiculo = args
    if not vehiculo.empty:
        vehiculo = vehiculo.sort_values(["id_mensajero", "n"], ascending=[True, False])
        vehiculo = vehiculo.drop_duplicates(subset=["id_mensajero"], keep="first")
        mensajero = mensajero.merge(
            vehiculo[["id_mensajero", "tipo_vehiculo"]],
            on="id_mensajero",
            how="left",
        )
    else:
        mensajero["tipo_vehiculo"] = NA_TEXT

    mensajero["nombre"] = mensajero["nombre"].replace({"": np.nan, " ": np.nan})
    mensajero["nombre"] = mensajero["nombre"].fillna(mensajero["username"])
    mensajero = _fill_text_nulls(mensajero)
    mensajero["activo"] = mensajero["activo"].fillna(False)
    mensajero["id_ciudad_operacion"] = mensajero["id_ciudad_operacion"].fillna(-1).astype("Int64")
    mensajero.drop(columns=["user_id"], inplace=True, errors="ignore")

    unknown = pd.DataFrame(
        [{
            "id_mensajero": -1,
            "username": NA_TEXT,
            "nombre": NA_TEXT,
            "telefono": NA_TEXT,
            "activo": False,
            "id_ciudad_operacion": -1,
            "ciudad_operacion": NA_TEXT,
            "tipo_vehiculo": NA_TEXT,
        }]
    )
    dim = pd.concat([unknown, mensajero], ignore_index=True)
    dim["saved"] = date.today()
    dim.reset_index(drop=True, inplace=True)
    return dim


def transform_estado(dim_estado: DataFrame) -> DataFrame:
    dim_estado = dim_estado.rename(columns={"id": "id_estado"})
    dim_estado = _fill_text_nulls(dim_estado)
    unknown = pd.DataFrame(
        [{"id_estado": -1, "nombre": NA_TEXT, "descripcion": NA_TEXT}]
    )
    dim = pd.concat([unknown, dim_estado], ignore_index=True)
    dim["saved"] = date.today()
    dim.reset_index(drop=True, inplace=True)
    return dim


def transform_tipo_novedad(dim_tipo: DataFrame) -> DataFrame:
    dim_tipo = dim_tipo.rename(columns={"id": "id_tipo_novedad"})
    dim_tipo = _fill_text_nulls(dim_tipo)
    unknown = pd.DataFrame([{"id_tipo_novedad": -1, "nombre": NA_TEXT}])
    dim = pd.concat([unknown, dim_tipo], ignore_index=True)
    dim["saved"] = date.today()
    dim.reset_index(drop=True, inplace=True)
    return dim


def _combine_fecha_hora(fecha, hora):
    """Build timestamp; return NaT when date or time is missing."""
    if pd.isna(fecha) or pd.isna(hora):
        return pd.NaT
    try:
        f = pd.to_datetime(fecha).to_pydatetime()
        if isinstance(hora, timedelta):
            return pd.Timestamp(datetime.combine(f.date(), datetime.min.time()) + hora)
        if hasattr(hora, "hour"):
            return pd.Timestamp(datetime.combine(f.date(), hora))
        # string / numeric fallback
        h = pd.to_datetime(str(hora)).time()
        return pd.Timestamp(datetime.combine(f.date(), h))
    except Exception:
        return pd.NaT


def _minutes_between(start, end):
    if pd.isna(start) or pd.isna(end):
        return np.nan
    minutes = (end - start).total_seconds() / 60.0
    # Out-of-order operational timestamps become null instead of negative durations
    return minutes if minutes >= 0 else np.nan


def _first_timestamp(group: DataFrame, estado_id: int):
    subset = group[group["id_estado"] == estado_id].sort_values("ts")
    if subset.empty:
        return pd.NaT
    return subset.iloc[0]["ts"]


def _last_estado_id(group: DataFrame):
    subset = group.sort_values("ts")
    if subset.empty:
        return -1
    return int(subset.iloc[-1]["id_estado"])


def transform_hecho_servicios(args) -> DataFrame:
    (servicios, estados, documentos, dim_fecha, dim_tiempo,
     dim_ubicacion, dim_mensajero, dim_estado) = args

    # Include ALL rows (including es_prueba / toy data)
    servicios = servicios.copy()
    estados = estados.copy()
    documentos = documentos.copy()

    servicios["id_mensajero"] = servicios["id_mensajero"].fillna(-1).astype("Int64")
    servicios["id_sede"] = servicios["id_sede"].fillna(-1).astype("Int64")
    servicios["es_prueba"] = servicios["es_prueba"].fillna(False)

    servicios = servicios.merge(documentos, on="id_servicio", how="left")
    servicios["cantidad_paquetes"] = servicios["cantidad_paquetes"].fillna(0).astype(int)
    servicios["cantidad_servicios"] = 1

    estados["ts"] = [
        _combine_fecha_hora(f, h) for f, h in zip(estados["fecha"], estados["hora"])
    ]
    estados = estados[~estados["ts"].isna()].copy()
    estados = estados.sort_values(["id_servicio", "ts"])

    last_estado = (
        estados.groupby("id_servicio", as_index=False)
        .tail(1)[["id_servicio", "id_estado"]]
        .rename(columns={"id_estado": "id_estado_actual"})
    )
    first_by_state = (
        estados.groupby(["id_servicio", "id_estado"], as_index=False)["ts"]
        .first()
        .pivot(index="id_servicio", columns="id_estado", values="ts")
        .reset_index()
    )
    rename_states = {
        ESTADO_INICIADO: "ts_iniciado",
        ESTADO_ASIGNADO: "ts_asignado",
        ESTADO_RECOGIDO: "ts_recogido",
        ESTADO_ENTREGADO: "ts_entregado",
        ESTADO_CERRADO: "ts_cerrado",
    }
    first_by_state = first_by_state.rename(columns=rename_states)
    for col in rename_states.values():
        if col not in first_by_state.columns:
            first_by_state[col] = pd.NaT

    fases = first_by_state.merge(last_estado, on="id_servicio", how="left")
    fases["tiempo_fase_asignacion"] = [
        _minutes_between(a, b)
        for a, b in zip(fases["ts_iniciado"], fases["ts_asignado"])
    ]
    fases["tiempo_fase_recogida"] = [
        _minutes_between(a, b)
        for a, b in zip(fases["ts_asignado"], fases["ts_recogido"])
    ]
    fases["tiempo_fase_entrega"] = [
        _minutes_between(a, b)
        for a, b in zip(fases["ts_recogido"], fases["ts_entregado"])
    ]
    fases["tiempo_fase_cierre"] = [
        _minutes_between(a, b)
        for a, b in zip(fases["ts_entregado"], fases["ts_cerrado"])
    ]
    start_total = fases["ts_iniciado"].fillna(fases["ts_asignado"])
    end_total = fases["ts_cerrado"].fillna(fases["ts_entregado"])
    fases["tiempo_total_minutos"] = [
        _minutes_between(a, b) for a, b in zip(start_total, end_total)
    ]
    hecho = servicios.merge(fases, on="id_servicio", how="left")

    # Fallback: if no state history, use solicitud datetime for total only
    hecho["ts_solicitud"] = [
        _combine_fecha_hora(f, h)
        for f, h in zip(hecho["fecha_solicitud"], hecho["hora_solicitud"])
    ]
    mask_total = hecho["tiempo_total_minutos"].isna() & hecho["ts_solicitud"].notna() & hecho["ts_cerrado"].notna()
    hecho.loc[mask_total, "tiempo_total_minutos"] = [
        _minutes_between(s, e)
        for s, e in zip(hecho.loc[mask_total, "ts_solicitud"], hecho.loc[mask_total, "ts_cerrado"])
    ]

    hecho["id_estado_actual"] = hecho["id_estado_actual"].fillna(-1).astype(int)
    hecho["hora"] = hecho["hora_solicitud"].apply(
        lambda x: x.hour if hasattr(x, "hour") and not pd.isna(x) else np.nan
    )
    hecho["hora"] = hecho["hora"].fillna(-1).astype(int)

    dim_fecha = dim_fecha.copy()
    dim_fecha["date_only"] = pd.to_datetime(dim_fecha["date"]).dt.date
    hecho["fecha_solicitud"] = pd.to_datetime(hecho["fecha_solicitud"], errors="coerce").dt.date

    hecho = hecho.merge(
        dim_fecha[["date_only", "key_dim_fecha"]],
        left_on="fecha_solicitud",
        right_on="date_only",
        how="left",
    )
    hecho = hecho.merge(dim_tiempo[["hora", "key_dim_tiempo"]], on="hora", how="left")
    hecho = hecho.merge(
        dim_ubicacion[["id_sede", "key_dim_ubicacion"]],
        on="id_sede",
        how="left",
    )
    hecho = hecho.merge(
        dim_mensajero[["id_mensajero", "key_dim_mensajero"]],
        on="id_mensajero",
        how="left",
    )
    hecho = hecho.merge(
        dim_estado[["id_estado", "key_dim_estado"]],
        left_on="id_estado_actual",
        right_on="id_estado",
        how="left",
    )

    # Resolve missing dimension keys using unknown members (-1)
    unknown_ubic = dim_ubicacion.loc[dim_ubicacion["id_sede"] == -1, "key_dim_ubicacion"]
    unknown_mens = dim_mensajero.loc[dim_mensajero["id_mensajero"] == -1, "key_dim_mensajero"]
    unknown_est = dim_estado.loc[dim_estado["id_estado"] == -1, "key_dim_estado"]
    unknown_time = None
    if (dim_tiempo["hora"] == 0).any() and hecho["key_dim_tiempo"].isna().any():
        # keep NaN only if hour invalid; map invalid hour to unknown via hora 0? better leave and drop only if fecha missing
        pass

    if not unknown_ubic.empty:
        hecho["key_dim_ubicacion"] = hecho["key_dim_ubicacion"].fillna(unknown_ubic.iloc[0])
    if not unknown_mens.empty:
        hecho["key_dim_mensajero"] = hecho["key_dim_mensajero"].fillna(unknown_mens.iloc[0])
    if not unknown_est.empty:
        hecho["key_dim_estado"] = hecho["key_dim_estado"].fillna(unknown_est.iloc[0])

    # Drop rows without fecha (cannot analyze by calendar)
    before = len(hecho)
    hecho = hecho[hecho["key_dim_fecha"].notna() & hecho["key_dim_tiempo"].notna()].copy()
    dropped = before - len(hecho)
    if dropped:
        print(f"[*] hecho_servicios: dropped {dropped} rows without fecha/tiempo keys")

    hecho["saved"] = date.today()
    cols = [
        "id_servicio",
        "key_dim_fecha",
        "key_dim_tiempo",
        "key_dim_ubicacion",
        "key_dim_mensajero",
        "key_dim_estado",
        "cantidad_servicios",
        "cantidad_paquetes",
        "tiempo_total_minutos",
        "tiempo_fase_asignacion",
        "tiempo_fase_recogida",
        "tiempo_fase_entrega",
        "tiempo_fase_cierre",
        "es_prueba",
        "saved",
    ]
    out = hecho[cols].reset_index(drop=True)
    for c in [
        "id_servicio", "key_dim_fecha", "key_dim_tiempo", "key_dim_ubicacion",
        "key_dim_mensajero", "key_dim_estado", "cantidad_servicios", "cantidad_paquetes",
    ]:
        out[c] = out[c].astype("Int64").astype(int)
    return out


def transform_hecho_novedades(args) -> DataFrame:
    (novedades, dim_fecha, dim_tiempo, dim_ubicacion,
     dim_mensajero, dim_tipo_novedad, dim_estado) = args

    # Include ALL novedades (including es_prueba / toy data)
    df = novedades.copy()
    df["id_mensajero"] = df["id_mensajero"].fillna(-1).astype("Int64")
    df["id_sede"] = df["id_sede"].fillna(-1).astype("Int64")
    df["id_tipo_novedad"] = df["id_tipo_novedad"].fillna(-1).astype("Int64")
    df["es_prueba"] = df["es_prueba"].fillna(False)
    df["cantidad_novedades"] = 1

    df["fecha_novedad"] = pd.to_datetime(df["fecha_novedad"], errors="coerce", utc=True)
    # normalize to naive local-like timestamp for date/hour extraction
    df["fecha_novedad"] = df["fecha_novedad"].dt.tz_convert(None)
    df["date_only"] = df["fecha_novedad"].dt.date
    df["hora"] = df["fecha_novedad"].dt.hour

    dim_fecha = dim_fecha.copy()
    dim_fecha["date_only"] = pd.to_datetime(dim_fecha["date"]).dt.date

    df = df.merge(
        dim_fecha[["date_only", "key_dim_fecha"]],
        on="date_only",
        how="left",
    )
    df = df.merge(dim_tiempo[["hora", "key_dim_tiempo"]], on="hora", how="left")
    df = df.merge(
        dim_ubicacion[["id_sede", "key_dim_ubicacion"]],
        on="id_sede",
        how="left",
    )
    df = df.merge(
        dim_mensajero[["id_mensajero", "key_dim_mensajero"]],
        on="id_mensajero",
        how="left",
    )
    df = df.merge(
        dim_tipo_novedad[["id_tipo_novedad", "key_dim_tipo_novedad"]],
        on="id_tipo_novedad",
        how="left",
    )

    # Optional estado link: novedades often relate to estado "Con novedad"
    estado_nov = dim_estado.loc[dim_estado["id_estado"] == ESTADO_NOVEDAD, "key_dim_estado"]
    unknown_est = dim_estado.loc[dim_estado["id_estado"] == -1, "key_dim_estado"]
    if not estado_nov.empty:
        df["key_dim_estado"] = estado_nov.iloc[0]
    elif not unknown_est.empty:
        df["key_dim_estado"] = unknown_est.iloc[0]
    else:
        df["key_dim_estado"] = np.nan

    unknown_ubic = dim_ubicacion.loc[dim_ubicacion["id_sede"] == -1, "key_dim_ubicacion"]
    unknown_mens = dim_mensajero.loc[dim_mensajero["id_mensajero"] == -1, "key_dim_mensajero"]
    unknown_tipo = dim_tipo_novedad.loc[dim_tipo_novedad["id_tipo_novedad"] == -1, "key_dim_tipo_novedad"]

    if not unknown_ubic.empty:
        df["key_dim_ubicacion"] = df["key_dim_ubicacion"].fillna(unknown_ubic.iloc[0])
    if not unknown_mens.empty:
        df["key_dim_mensajero"] = df["key_dim_mensajero"].fillna(unknown_mens.iloc[0])
    if not unknown_tipo.empty:
        df["key_dim_tipo_novedad"] = df["key_dim_tipo_novedad"].fillna(unknown_tipo.iloc[0])

    before = len(df)
    df = df[df["key_dim_fecha"].notna() & df["key_dim_tiempo"].notna()].copy()
    dropped = before - len(df)
    if dropped:
        print(f"[*] hecho_novedades: dropped {dropped} rows without fecha/tiempo keys")

    df["saved"] = date.today()
    cols = [
        "id_novedad",
        "key_dim_fecha",
        "key_dim_tiempo",
        "key_dim_ubicacion",
        "key_dim_mensajero",
        "key_dim_tipo_novedad",
        "key_dim_estado",
        "cantidad_novedades",
        "es_prueba",
        "saved",
    ]
    out = df[cols].reset_index(drop=True)
    for c in [
        "id_novedad", "key_dim_fecha", "key_dim_tiempo", "key_dim_ubicacion",
        "key_dim_mensajero", "key_dim_tipo_novedad", "key_dim_estado", "cantidad_novedades",
    ]:
        out[c] = out[c].astype("Int64").astype(int)
    return out
