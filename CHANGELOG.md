# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-12

### Added

- End-to-end ETL pipeline for Fast and Safe (`main.py`, `src/etl/*`).
- OLAP DDL in `sqlscripts.yml` for dimensions and fact tables.
- Conformed dimensions: `dim_fecha`, `dim_tiempo`, `dim_ubicacion`, `dim_mensajero`, `dim_estado`, `dim_tipo_novedad`.
- Fact tables: `hecho_servicios` (phase durations + packages) and `hecho_novedades`.
- Null-safe unknown members and business time slots (`franja_horaria`).
- Course-style exploratory notebooks under `src/notebooks/`.
- `config.example.yml`, MIT license, version badge support and English README.
- Formatted Spanish delivery report under `docs/`.

### Notes

- All OLTP rows are loaded, including `es_prueba` / toy records.
- Warehouse target database: `olap_proyecto_mensajeria`.
