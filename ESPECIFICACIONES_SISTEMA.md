# Especificaciones del Sistema - AppEtiquetas

## 1. Objetivo del sistema

AppEtiquetas es una aplicacion web construida con Django para crear, editar, visualizar y duplicar etiquetas ZPL, con previsualizacion en imagen PNG mediante el servicio Labelary.

El objetivo principal es centralizar la gestion de plantillas de etiquetas y permitir que el contenido dinamico (variables) se resuelva por idioma, con fallback a espanol cuando no exista traduccion.

## 2. Alcance funcional

El sistema permite:

- Crear etiquetas nuevas con configuracion de impresora, insumo y rotacion.
- Editar etiquetas existentes (nombre y ZPL).
- Duplicar etiquetas existentes con nuevo nombre.
- Renderizar etiquetas a PNG para vista previa.
- Resolver variables embebidas en ZPL desde base de datos.
- Resolver variables con logica multi-idioma.
- Detectar variables faltantes en base de datos y notificar al usuario.
- Informar cuando una variable usa fallback a idioma ES.

## 3. Arquitectura tecnica

### 3.1 Stack

- Backend: Django 4.2.6
- Base de datos: PostgreSQL
- Cliente HTTP: httpx
- Frontend: HTML + Bootstrap + htmx + JavaScript
- Contenedores: Docker + Docker Compose
- Testing: pytest + pytest-django (pipeline CI)

### 3.2 Estructura de alto nivel

- Proyecto Django: labelary
- App principal: etiquetas
- Templates: templates/etiquetas
- Estaticos: static
- Orquestacion: docker-compose.yaml
- CI: .github/workflows/main.yml

## 4. Modelo de datos

### 4.1 Entidades

- Impresora
  - dpi (Integer)
  - descripcion (Char)

- Insumo
  - nombre (Char)
  - tamanio (Char, ej. 4x6)

- Rotacion
  - descripcion (Char)
  - angulo (Integer)

- Etiqueta
  - tipo_etiqueta (choices: Rotulo Interno, Etiqueta Externa)
  - nombre (Char)
  - contenido_zpl (Text)
  - fecha_creacion (DateTime)
  - impresora (FK)
  - insumo (FK)
  - rotacion (FK)
  - Restriccion unica: tipo_etiqueta + nombre

- Idioma
  - codigo (PK, Char)
  - nombre (Char unico)

- Variable
  - codigo (Char)
  - default (Char)
  - descripcion (Char opcional)
  - idioma (FK a Idioma.codigo)
  - Restriccion unica: codigo + idioma

- TraduccionVariable
  - variable (FK)
  - idioma (FK)
  - descripcion (Char)
  - Restriccion unica: variable + idioma

### 4.2 Reglas de integridad relevantes

- No pueden existir dos etiquetas con el mismo nombre dentro del mismo tipo.
- Una variable se identifica por codigo+idioma.
- Durante la renderizacion, si no existe una variable en el idioma solicitado, se intenta usar ES.

## 5. Operacion funcional

### 5.1 Flujo principal de usuario

1. El usuario abre la pantalla principal del sistema.
2. Puede trabajar en dos modos:
   - Edicion manual de ZPL.
   - Gestion de etiquetas existentes.
3. Selecciona impresora, insumo, rotacion e idioma.
4. El sistema procesa el ZPL y reemplaza variables.
5. Se envia el ZPL resultante a Labelary para convertir a PNG.
6. Se muestra la vista previa y mensajes de advertencia/error.

### 5.2 Flujo de procesamiento de variables

El backend analiza el ZPL y soporta varios patrones de reemplazo:

- Variables simples: [@Variable@]
- Variables con idioma directo: [@Variable;EN@]
- Variables con formato especial FI: [@Variable;;FI ITA@]
- Variables anidadas con selector de idioma: [@Variable[@IDIOMAVARIABLE@]@]
- Variable de idioma literal: [@IDIOMAVARIABLE=EN@]
- Variables con formato de fecha: [@Fecha;FFdd/MM/yyyy@]

Prioridades observadas en la logica:

- El patron FIIDIOMAVARIABLE usa preferentemente el idioma seleccionado en template.
- Si falta traduccion en idioma solicitado, intenta fallback a ES.
- Si una variable no existe en ningun idioma, se reporta como faltante.

### 5.3 Renderizado de etiqueta

El renderizado construye la URL de Labelary segun:

- dpi de impresora -> segmento dpmm
- tamanio de insumo -> segmento labels/{tamanio}
- angulo de rotacion -> header X-Rotation

Se aplican hasta 3 reintentos ante error y timeout de 10 segundos por intento.

## 6. Endpoints del sistema

Rutas base:

- /admin/
- /etiquetas/

Rutas funcionales de la app:

- GET /etiquetas/
  - Pantalla principal.

- POST /etiquetas/png/
  - Renderiza vista previa desde ZPL directo o etiqueta por ID.

- GET /etiquetas/renderizar/{etiqueta_id}/
  - Renderiza una etiqueta persistida.

- GET /etiquetas/get_zpl/{etiqueta_id}/
  - Devuelve ZPL y configuracion asociada (JSON).

- POST /etiquetas/actualizar_zpl/
  - Actualiza contenido ZPL y opcionalmente nombre.

- POST /etiquetas/crear_etiqueta/
  - Crea nueva etiqueta.

- POST /etiquetas/visualizar_etiqueta/
  - Vista previa temporal sin persistir etiqueta.

- POST /etiquetas/actualizar_nombre_etiqueta/
  - Renombra etiqueta existente.

- POST /etiquetas/duplicar_etiqueta/
  - Duplica etiqueta con nuevo nombre.

## 7. Interfaz de usuario

La interfaz principal usa Bootstrap con dos tabs:

- Edicion Manual
- Etiquetas Existentes

Capacidades en UI:

- Selector de tipo, impresora, tamano, rotacion, idioma.
- Edicion de codigo ZPL.
- Guardado y duplicacion de etiquetas.
- Vista previa dinamica via htmx.
- Modo claro/oscuro.
- Mensajes de advertencia por fallback de idioma.
- Mensajes de error por variables inexistentes.

## 8. Configuracion y despliegue

### 8.1 Variables de entorno requeridas

La configuracion de base de datos depende de:

- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_HOST
- POSTGRES_PORT

### 8.2 Ejecucion con Docker Compose

Servicios:

- labelary_app: app Django en puerto 8000
- db_labelary: PostgreSQL

Notas:

- El compose usa archivo docker-compose.yaml.
- En .dockerignore figura docker-compose.yml (nombre distinto), lo que sugiere una inconsistencia menor de nomenclatura.

### 8.3 CI/CD

GitHub Actions ejecuta pruebas en pushes a main y ramas test/*, y en pull requests:

- Python 3.11
- instalacion de dependencias
- ejecucion de pytest -v

## 9. Calidad, pruebas y observabilidad

### 9.1 Estado de pruebas

- Existe configuracion pytest (pytest.ini).
- Existe pipeline de ejecucion de tests.
- Archivo de pruebas de la app actualmente vacio (tests.py sin casos definidos).

### 9.2 Logging y diagnostico

- Hay trazas print extensivas en procesamiento de variables/idioma/fecha.
- Varias capturas de excepcion retornan error amigable en template JSON/HTML.

## 10. Riesgos y hallazgos del analisis

1. El proyecto declara Django 4.2.6 en requirements, pero settings.py tiene cabecera generada por Django 5.2.1. Puede confundir mantenimiento.
2. En Labelary.renderizar_etiqueta se compara tipo_etiqueta con "interno"/"externo", pero en el modelo los valores son "Rotulo Interno" y "Etiqueta Externa". Hoy no rompe porque ambos caminos llaman al mismo render, pero es inconsistente.
3. El archivo tests.py de la app no cubre funcionalidad critica de variables, idioma ni renderizado.
4. Hay muchos prints de depuracion en rutas de produccion, con potencial ruido en logs.
5. Existe archivo correcicon.txt con lineamientos de proceso, pero no integrado a documentacion formal.

## 11. Objetivo operativo recomendado

Para operar de forma estable en entorno real, este sistema debe enfocarse en:

- Garantizar consistencia de variables multi-idioma por plantilla.
- Asegurar calidad de datos (variables definidas y traducciones completas).
- Mantener disponibilidad del servicio Labelary.
- Incrementar cobertura de pruebas sobre parsing de patrones ZPL y reglas de fallback.

## 12. Propuesta de mejoras inmediatas

1. Crear tests unitarios de Patrones y formatear_fecha.
2. Crear tests de integracion para endpoints crear/actualizar/visualizar/renderizar.
3. Unificar nombres y convenciones (docker-compose.yaml vs docker-compose.yml).
4. Reducir prints y migrar a logging estructurado por nivel.
5. Documentar ejemplos de patrones ZPL soportados para usuarios funcionales.

---

Documento generado a partir del analisis del repositorio completo en la rama main.