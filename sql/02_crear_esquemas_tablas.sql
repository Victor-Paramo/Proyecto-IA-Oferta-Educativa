-- ============================================================
-- PROYECTO IA - OFERTA EDUCATIVA
-- 02. CREACION DE ESQUEMAS Y TABLAS
-- PostgreSQL 16 | Modelo relacional preliminar
-- Ejecutar conectado a la base oferta_educativa.
-- No ejecutarlo de nuevo si ya se crearon las tablas.
-- ============================================================

BEGIN;

CREATE SCHEMA catalogo;
CREATE SCHEMA origen;

-- ============================================================
-- ESQUEMA CATALOGO: entidades normalizadas
-- ============================================================

CREATE TABLE catalogo.estado (
    id_estado INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE catalogo.institucion (
    id_institucion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE catalogo.plantel (
    id_plantel BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_institucion BIGINT NOT NULL
        REFERENCES catalogo.institucion(id_institucion),
    id_estado INTEGER NOT NULL
        REFERENCES catalogo.estado(id_estado),
    nombre TEXT
);

CREATE TABLE catalogo.nivel_academico (
    id_nivel INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE catalogo.programa_academico (
    id_programa BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_nivel INTEGER NOT NULL
        REFERENCES catalogo.nivel_academico(id_nivel),
    nombre TEXT NOT NULL,
    CONSTRAINT uq_programa_nivel UNIQUE (nombre, id_nivel)
);

CREATE TABLE catalogo.modalidad (
    id_modalidad INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Sin UNIQUE (plantel, programa, modalidad) por el momento:
-- aun se debe resolver la identidad de cada oferta.
CREATE TABLE catalogo.oferta_educativa (
    id_oferta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_plantel BIGINT NOT NULL
        REFERENCES catalogo.plantel(id_plantel),
    id_programa BIGINT NOT NULL
        REFERENCES catalogo.programa_academico(id_programa),
    id_modalidad INTEGER NOT NULL
        REFERENCES catalogo.modalidad(id_modalidad)
);

CREATE TABLE catalogo.autorizacion (
    id_autorizacion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_oferta BIGINT NOT NULL
        REFERENCES catalogo.oferta_educativa(id_oferta),
    tipo VARCHAR(50),
    referencia TEXT,
    fecha_otorgamiento DATE,
    texto_original TEXT NOT NULL,
    CONSTRAINT uq_autorizacion_id_oferta
        UNIQUE (id_autorizacion, id_oferta)
);

-- ============================================================
-- ESQUEMA ORIGEN: procedencia y trazabilidad documental
-- ============================================================

CREATE TABLE origen.documento_fuente (
    id_documento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_archivo TEXT NOT NULL UNIQUE
);

CREATE TABLE origen.registro_origen (
    id_registro BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_documento BIGINT NOT NULL
        REFERENCES origen.documento_fuente(id_documento),
    pagina INTEGER,
    datos_json JSONB NOT NULL,
    CONSTRAINT ck_pagina_positiva
        CHECK (pagina IS NULL OR pagina > 0)
);

-- Un registro de origen puede no tener vinculo mientras se revisa.
-- Si existe, solo puede vincularse a una oferta y opcionalmente
-- a una autorizacion que pertenezca a esa misma oferta.
CREATE TABLE origen.vinculo_registro (
    id_registro BIGINT PRIMARY KEY
        REFERENCES origen.registro_origen(id_registro),
    id_oferta BIGINT NOT NULL
        REFERENCES catalogo.oferta_educativa(id_oferta),
    id_autorizacion BIGINT,
    estado_revision VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    CONSTRAINT ck_estado_revision
        CHECK (estado_revision IN ('PENDIENTE', 'VALIDADO', 'REVISAR')),
    CONSTRAINT fk_autorizacion_oferta
        FOREIGN KEY (id_autorizacion, id_oferta)
        REFERENCES catalogo.autorizacion(id_autorizacion, id_oferta)
);

COMMIT;
