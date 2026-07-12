# ETL_Ciencia_De_Datos

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](./VERSION)
[![Python](https://img.shields.io/badge/python-3.11%2B-yellow.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-12%2B-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![ETL](https://img.shields.io/badge/pipeline-ETL-orange.svg)](./main.py)
[![Status](https://img.shields.io/badge/status-stable-success.svg)](./CHANGELOG.md)

Python ETL pipeline and dimensional data warehouse for the **Fast and Safe** messaging company (course project).

Operational data lives in PostgreSQL (`proyecto_mensajeria`). The ETL builds conformed dimensions and two fact tables in `olap_proyecto_mensajeria`, following the same project style used in the class reference (`CS_etl_py`).

## Authors

- Adolfo Andrey Quiceno Cabrera
- Iván David Ausecha Salamanca

## What this project does

1. **Extract** services, state history, incidents, clients/sites and messengers from the OLTP database.
2. **Transform** calendar/time slots, unified location hierarchy, null-safe unknown members, and phase durations (assignment → pickup → delivery → close).
3. **Load** dimensions and facts into the OLAP warehouse for analytics / Power BI.

Toy / test rows (`es_prueba = true`) are **included** on purpose so the warehouse reflects the full operational database.

## Architecture

```text
PostgreSQL OLTP (proyecto_mensajeria)
        │
        ▼
   Extract (pandas + SQLAlchemy)
        │
        ▼
   Transform (dimensions + facts)
        │
        ▼
PostgreSQL OLAP (olap_proyecto_mensajeria)
        │
        ▼
   Notebooks / Power BI
```

## Warehouse model

### Dimensions

| Table | Description |
|-------|-------------|
| `dim_fecha` | Calendar attributes, Colombia holidays, weekend flag |
| `dim_tiempo` | 24 hours with business time slots (`franja_horaria`) |
| `dim_ubicacion` | Cliente → Sede → Ciudad → Departamento |
| `dim_mensajero` | Messenger profile and most-used vehicle type |
| `dim_estado` | Service lifecycle states |
| `dim_tipo_novedad` | Incident types |

### Facts

| Table | Grain | Key measures |
|-------|-------|--------------|
| `hecho_servicios` | One row per service | `cantidad_servicios`, `cantidad_paquetes`, phase times (minutes) |
| `hecho_novedades` | One row per incident | `cantidad_novedades` |

Phase times are derived from `mensajeria_estadosservicio` timestamps. Out-of-order durations are stored as `NULL` instead of negative values.

## Project structure

```text
ETL_Ciencia_De_Datos/
├── config.example.yml      # Template only (safe to commit)
├── config.yml              # Local credentials (gitignored, never pushed)
├── sqlscripts.yml
├── main.py
├── requirements.txt
├── VERSION / CHANGELOG.md / LICENSE
├── docs/
└── src/
    ├── etl/
    │   ├── extract.py
    │   ├── transform.py
    │   ├── load.py
    │   └── utils_etl.py
    └── notebooks/          # One notebook per dimension/fact
```

## Requirements

- Python 3.11+
- PostgreSQL with:
  - OLTP database `proyecto_mensajeria`
  - OLAP database `olap_proyecto_mensajeria` (created automatically if admin credentials are set)

## Setup

### 1. Clone

```bash
git clone https://github.com/AndreyQuicenoC/ETL_Ciencia_De_Datos.git
cd ETL_Ciencia_De_Datos
```

### 2. Virtual environment

```bash
python -m venv my_env

# Windows PowerShell
.\my_env\Scripts\Activate.ps1

# Linux / macOS
source my_env/bin/activate

pip install -r requirements.txt
```

### 3. Configuration

```bash
cp config.example.yml config.yml
```

Edit `config.yml`:

```yaml
OLTP:
  drivername: postgresql
  dbname: proyecto_mensajeria
  user: user_example
  password: YOUR_PASSWORD
  host: localhost
  port: 5432

ETL_PRO:
  drivername: postgresql
  dbname: olap_proyecto_mensajeria
  user: user_example
  password: YOUR_PASSWORD
  host: localhost
  port: 5432

ADMIN:
  drivername: postgresql
  dbname: postgres
  user: postgres
  password: YOUR_ADMIN_PASSWORD
  host: localhost
  port: 5432

LOAD_DIMENSIONS: True
FORCE_RELOAD: False
```

Only `config.example.yml` is versioned. Copy it to `config.yml` locally and fill in your real credentials; `config.yml` is ignored by git.

`ADMIN` is only used to create the OLAP database and grant privileges when it does not exist yet.

### 4. Run the ETL

```bash
python main.py
```

Expected result (full reload):

- dimensions loaded
- `hecho_servicios` ≈ 28 430 rows
- `hecho_novedades` ≈ 5 208 rows
- `success all facts loaded`

Set `FORCE_RELOAD: True` in `config.yml` if you need to rebuild after a successful run.

### 5. Notebooks

```bash
jupyter notebook src/notebooks
```

Each notebook follows the class style: connect with `../../config.yml` → extract → transform → load.
## Optional Docker (local PostgreSQL + pgAdmin)

If you are not using an already running PostgreSQL instance:

```bash
docker compose up -d
```

Default compose credentials are for a blank lab environment. For this course project the recommended path is the existing local databases configured in `config.yml`.

## Power BI

Connect with:

- Server: `localhost`
- Port: `5432`
- Database: `olap_proyecto_mensajeria`
- User / password: values from `config.yml`

Import dimensions and both fact tables to build dashboards for demand, messenger productivity, SLA phase times and incident frequency.

## Documentation

Spanish assignment report and diagrams remain under [`docs/`](./docs/Informe%20de%20entrega%20Ciencia%20de%20datos.md).

## License

MIT — see [LICENSE](./LICENSE).
