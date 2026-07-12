# Ciencia de datos

Sistema para analizar datos de una empresa de mensajería.

**Autores:** Adolfo Andrey Quiceno Cabrera · Iván David Ausecha Salamanca

---

## Introducción

La empresa de mensajería “Fast and Safe” busca desarrollar una solución de analítica de datos que apoye la toma de decisiones en sus operaciones. Actualmente, la organización cuenta con un sistema de información operacional que gestiona clientes y servicios, y opera en múltiples ciudades de Colombia. Sin embargo, esta información no se encuentra estructurada para análisis estratégico.

En este contexto, el presente trabajo aborda el diseño conceptual de una solución de bodega de datos, orientada a organizar y transformar los datos operacionales en información útil. A través de la identificación de procesos de negocio, la construcción de la matriz de bus y el diseño de Data Marts, se establece una base sólida que permitirá analizar el comportamiento de la demanda, el desempeño operativo y la calidad del servicio.

---

## Objetivos

### General

La empresa “Fast and Safe” quiere hacer un sistema de bodegas de datos que le permita analizar la información que generan los clientes y mensajeros.

### Específicos

Responder a los interrogantes:

1. ¿En qué meses del año los clientes solicitan más servicios de mensajería?
2. ¿Cuáles son los días donde más solicitudes hay?
3. ¿A qué hora los mensajeros están más ocupados?
4. Número de servicios solicitados por cliente y por mes.
5. Mensajeros más eficientes (los que más servicios prestan).
6. ¿Cuáles son las sedes que más servicios solicitan por cada cliente?
7. ¿Cuál es el tiempo promedio de entrega desde que se solicita el servicio hasta que se cierra el caso?
8. Mostrar los tiempos de espera por cada fase del servicio: Iniciado, Con mensajero asignado, recogido en origen, Entregado en Destino, Cerrado. ¿En qué fase del servicio hay más demoras?
9. ¿Cuáles son las novedades que más se presentan durante la prestación del servicio?

---

## Metodología

Para abordar el problema de la empresa se plantea usar estrategias de Ciencias de Datos para diseñar, construir y ejecutar una solución que resuelva el problema de la empresa.

En las etapas de diseño se usarán herramientas como la Matriz de bus, el diseño de data marts, reconocimiento de dimensiones, etc. Bajo la lógica del modelo dimensional se desarrolla el análisis para posteriormente poder crear las bodegas de datos correspondientes en próximas entregas.

### Modelo relacional

A partir del análisis del modelo relacional, se identificaron las principales dimensiones que permiten contextualizar los hechos del negocio dentro del modelo dimensional.

### Matriz de Bus

| Proceso de negocio   | Fecha | Tiempo | Cliente | Mensajero | Ubicación | Estado | Tipo de novedad |
|----------------------|:-----:|:------:|:-------:|:---------:|:---------:|:------:|:---------------:|
| Gestión de servicios | X     | X      | X       | X         | X         | X      |                 |
| Gestión de novedades | X     | X      | X       | X         | X         | X      | X               |

---

## Descripción de los procesos

### Gestión de servicios

Este proceso corresponde al ciclo de vida completo de un servicio de mensajería. Inicia cuando un cliente solicita un servicio a través de la plataforma, registrando información como origen, destino, fecha, hora y prioridad. Este pasa por diferentes fases o estados (iniciado, asignado, recogido, entregado y cerrado), cuya información se almacena en el historial de estados. Este proceso permite analizar el volumen de servicios, tiempos de atención, desempeño de los mensajeros y comportamiento de la demanda.

### Gestión de novedades

Se enfoca en el registro de incidencias que pueden ocurrir durante la ejecución de un servicio. Las novedades son registradas por los mensajeros o el sistema y pueden corresponder a situaciones como retrasos, problemas mecánicos, errores en la dirección o demoras del cliente, con el objetivo de detectar oportunidades de mejora en la operación.

---

## Descripción de las dimensiones

| Dimensión | Descripción |
|-----------|-------------|
| **Fecha** | Permite analizar servicios y novedades a nivel de calendario (día, mes, año, festivos y trimestres). Es vital para identificar tendencias de demanda estacional y comparativas anuales. |
| **Tiempo (Reloj)** | Representa las 24 horas del día y sus franjas horarias. Es la dimensión clave para responder “¿A qué hora los mensajeros están más ocupados?” y definir rangos de “Horas Pico”. |
| **Ubicación (Cliente / Sede / Ciudad)** | Dimensión unificada. Contiene la jerarquía completa: desde la empresa (Cliente), pasando por el punto físico (Sede), hasta la ubicación geográfica (Ciudad y Departamento). Responde quién pide y desde dónde, eliminando la redundancia. |
| **Repartidor (Mensajero)** | Corresponde a los mensajeros que ejecutan los servicios. Incluye atributos como nombre, tipo de vehículo y datos de contacto. Es esencial para evaluar la eficiencia y carga de trabajo individual. |
| **Estado** | Representa las fases del ciclo de vida del servicio (Iniciado, Asignado, Recogido, Entregado, Cerrado). Permite calcular los tiempos de espera entre fases y detectar cuellos de botella operativos. |
| **Tipo de Novedad** | Clasifica de forma estandarizada las incidencias (Dirección errada, cliente ausente, etc.). Facilita el análisis de los problemas más frecuentes para la toma de decisiones preventivas. |

---

## Diseño de data marts

### Data Mart de servicios

El Data Mart de Servicios tiene como objetivo analizar el comportamiento operativo y la eficiencia logística de la empresa “Fast and Safe”. Está diseñado para evaluar la fluctuación de la demanda, la productividad de la flota de mensajeros y el cumplimiento de los niveles de servicio (SLA) mediante el monitoreo de los tiempos de atención en cada fase crítica del ciclo de vida del envío.

El grano de este Data Mart es un registro por cada servicio individual. Esta granularidad permite realizar análisis multidimensionales y detallados por Ubicación (integrando Cliente, Sede y Ciudad), Fecha (calendario), Tiempo (rango horario), Mensajero y Estado del servicio.

| Nombre del atributo | Descripción |
|---------------------|-------------|
| `cantidad_servicios` | Métrica base que indica el conteo de servicios realizados (valor constante de 1 por registro). |
| `cantidad_paquetes` | Sumatoria de documentos o bultos asociados a cada servicio, permitiendo analizar la carga física gestionada. |
| `tiempo_total_minutos` | Tiempo total transcurrido, medido en minutos, desde la creación de la solicitud por parte del cliente hasta el cierre definitivo en el sistema. |
| `tiempo_fase_asignacion` | Minutos transcurridos desde que se registra la solicitud hasta que un mensajero es vinculado al servicio. |
| `tiempo_fase_recogida` | Minutos transcurridos desde la asignación del mensajero hasta que el paquete es marcado como “Recogido en Origen”. |
| `tiempo_fase_entrega` | Minutos transcurridos desde la recogida hasta que el servicio cambia al estado “Entregado en Destino”. |
| `tiempo_fase_cierre` | Minutos transcurridos desde la entrega física hasta que el caso se formaliza como “Cerrado” en la plataforma, permitiendo detectar demoras administrativas. |

#### Preguntas que responde el Data Mart de Servicios

| Pregunta | Cómo se responde |
|----------|------------------|
| Meses con más servicios | Dimensión Fecha (atributo Mes) + métrica `cantidad_servicios`. |
| Días con más solicitudes | Dimensión Fecha (atributo Día de la semana) + métrica `cantidad_servicios`. |
| Horas pico de mensajeros | Dimensión Tiempo (Hora o Rango Horario) + métrica `cantidad_servicios`. |
| Servicios por cliente y mes | Dimensión Ubicación (Cliente) × Fecha (Mes) + `cantidad_servicios`. |
| Mensajeros más eficientes | Dimensión Mensajero + `cantidad_servicios` (filtrando finalizados). |
| Sedes con más servicios por cliente | Dimensión Ubicación (jerarquía Cliente > Sede) + `cantidad_servicios`. |
| Tiempo promedio de entrega | Promedio de `tiempo_total_minutos`. |
| Demoras por fase | Métricas `tiempo_fase_asignacion`, `tiempo_fase_recogida`, `tiempo_fase_entrega` y `tiempo_fase_cierre`. |

---

### Data Mart de novedades

El Data Mart de Novedades permite analizar las incidencias que ocurren durante la ejecución de los servicios de mensajería. Su propósito es identificar patrones de fallas, evaluar la calidad del servicio y detectar las principales causas de retrasos o problemas operativos.

El grano de este Data Mart es un registro por cada novedad reportada. Este nivel de detalle permite analizar la frecuencia de las incidencias mediante su categorización por tipo, cliente y mensajero.

| Nombre del atributo | Descripción |
|---------------------|-------------|
| `cantidad_novedades` | Indica el conteo de novedades registradas (valor constante de 1 por registro). |

#### Preguntas que responde el Data Mart de Novedades

| Pregunta | Cómo se responde |
|----------|------------------|
| ¿Cuáles son las novedades que más se presentan? | Dimensión Tipo de Novedad + suma de `cantidad_novedades`, ordenado de mayor a menor. |

---

## Resultados

### Abordaje de preguntas

El modelo dimensional propuesto permite responder los interrogantes planteados por la empresa de la siguiente manera:

| Pregunta | Cómo se responde |
|----------|------------------|
| 1. Meses con más servicios | Se agrupa por el atributo `Nombre_Mes` / `month_str` de `Dim_Fecha` y se suma `cantidad_servicios`. |
| 2. Días con más solicitudes | Se utiliza el atributo `Dia_Semana` / `day_str` de `Dim_Fecha` para identificar patrones de demanda diaria. |
| 3. Horas pico | Se analiza mediante `Dim_Tiempo`, utilizando el atributo Hora o `franja_horaria`. |
| 4. Servicios por cliente | Se agrupa por `Nombre_Cliente` en la dimensión unificada `Dim_Ubicacion`. |
| 5. Mensajeros eficientes | Se cruza `Dim_Mensajero` con las métricas de tiempo y cantidad de servicios en `Fact_Servicios`. |
| 6. Sedes con más servicios | Se utiliza el atributo `Sede_Nombre` de `Dim_Ubicacion`. |
| 7. Tiempo promedio entrega | Se calcula el promedio de la métrica `tiempo_total_minutos` en `Fact_Servicios`. |
| 8. Tiempos por fase | Se analizan las métricas directas: asignación, recogida, entrega y cierre. |
| 9. Novedades frecuentes | Se agrupa por `Nombre_Novedad` de `Dim_Tipo_Novedad` y se suma `cantidad_novedades`. |

### Metodología de cálculo de tiempos

Cabe resaltar que el cálculo de los tiempos por fase del servicio se realiza mediante la transformación de los datos de la tabla operativa `mensajeria_estadosservicio`, la cual almacena el historial de estados con sus respectivas marcas de tiempo (timestamps). Este enfoque de ingeniería de datos permite reconstruir el flujo cronológico de cada operación para calcular con precisión las métricas de tiempo de asignación, recogida, entrega y cierre. Al integrar estos cálculos directamente en el Data Mart de Servicios, se facilita un análisis inmediato de la eficiencia operativa sin necesidad de procesar el historial de estados en cada consulta.

### Análisis de la solución

Como resultado de esta entrega, se consolidó el diseño conceptual de la solución analítica para la empresa “Fast and Safe”. En este proceso, se identificaron los procesos clave del negocio: la gestión de servicios y la gestión de novedades. Se definieron dimensiones transversales y conformadas (fecha, ubicación unificada, tiempo, mensajero, tipo de novedad y estado), lo que garantiza la integridad de los datos en toda la organización.

A través de la matriz de bus, se alinearon estos procesos permitiendo la coexistencia de dos Data Marts especializados:

- **Data Mart de Servicios:** orientado a la medición de productividad y tiempos de respuesta.
- **Data Mart de Novedades:** orientado al control de calidad y detección de incidencias recurrentes.

---

## Conclusiones

En el paso a paso seguido en el análisis de los datos para diseñar la bodega de datos diagramando la matriz de bus y los data marts, se logró:

- Definir una estructura analítica coherente a partir del entendimiento del negocio.
- Diseñar la matriz de bus que permitió organizar los procesos y garantizar consistencia entre los Data Marts.
- Cubrir, con el diseño de los Data Marts, los requerimientos de análisis planteados por la empresa.
- Plantear el modelo dimensional para facilitar la construcción de la bodega de datos.

---

## Anexos

### Apéndice A — Diagramas de base de datos y arquitectura de Data Marts

Enlace al recurso en Draw.io:  
https://drive.google.com/file/d/1NmFMSb7_tkDVOJw_tn1OhEV7U0P220Gq/view?usp=sharing

Diagramas locales exportados en este directorio:

- `Mensajería-CienciaDeDatos.drawio.html` (modelo operacional)
- `Mensajería-CienciaDeDatos.drawio (1).html` (Data Mart Servicios)
- `Mensajería-CienciaDeDatos.drawio (2).html` (Data Mart Novedades)
