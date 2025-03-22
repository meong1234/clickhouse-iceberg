-- +goose Up
CREATE DATABASE IF NOT EXISTS iceberg_catalog
ENGINE = DataLakeCatalog('http://iceberg-catalog:8181', 'minio-root-user', 'minio-root-password')
SETTINGS 
    catalog_type = 'rest', 
    warehouse = 'warehouse', 
    storage_endpoint = 'http://minio:9000/warehouse';