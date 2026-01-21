-- V1: Products + Materials (PostgreSQL)

DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS materials CASCADE;

CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  price NUMERIC(10,2) NOT NULL,
  materials_input TEXT
);

CREATE TABLE materials (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,          -- FILAMENT | HARDWARE | PACKAGING | OTHER
  color TEXT NOT NULL,             -- allow 'N/A'
  quantity_on_hand NUMERIC(12,2) NOT NULL DEFAULT 0,
  unit TEXT NOT NULL DEFAULT 'pcs',

  -- Filament-only fields (nullable for non-filament)
  brand TEXT,
  type TEXT,
  finish TEXT
);

CREATE INDEX IF NOT EXISTS idx_material_lookup
ON materials(category, name, color, brand, type, finish);