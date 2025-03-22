#!/usr/bin/env python3
"""
Script to create catalog, namespace, and table for battery data in Iceberg
"""
import argparse
import logging
import sys
import traceback
from datetime import datetime
import random
import os

import pyarrow as pa
import pandas as pd
from pyiceberg.catalog import load_catalog
from pyiceberg.partitioning import PartitionSpec, PartitionField  # Add PartitionField import
from pyiceberg.schema import Schema
from pyiceberg.schema import NestedField
from pyiceberg.types import (TimestampType, StringType, DoubleType, IntegerType)
from pyiceberg.io import pyarrow as py_io
from pyiceberg.transforms import (
    MonthTransform,
    IdentityTransform,
    DayTransform,
    HourTransform
)

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("battery-schema")

# Default settings
DEFAULT_CATALOG_URL = "http://iceberg-catalog:8181"
DEFAULT_WAREHOUSE = "warehouse"
DEFAULT_NAMESPACE = "iot_battery"
DEFAULT_TABLE_NAME = "battery_v2"

def create_catalog_connection(catalog_url, warehouse):
    """Create a connection to the Iceberg catalog"""
    logger.info(f"Attempting to connect to catalog at {catalog_url} with warehouse {warehouse}")
    
    try:
        # Configure S3 environment variables
        os.environ['AWS_S3_ENDPOINT'] = 'http://minio:9000'
        os.environ['AWS_S3_PATH_STYLE_ACCESS'] = 'true'
        
        logger.debug(f"Loading catalog with identifier='demo', uri='{catalog_url}', warehouse='{warehouse}'")
        logger.debug(f"S3 endpoint set to: {os.environ.get('AWS_S3_ENDPOINT')}")
        
        # Add specific properties for S3 access
        props = {
            "uri": catalog_url,
            "warehouse": warehouse,
            "s3.endpoint": "http://minio:9000",
            "s3.path-style-access": "true",
            "s3.access-key-id": "minio-root-user",
            "s3.secret-access-key": "minio-root-password"
        }
        
        catalog = load_catalog("demo", **props)
        logger.info(f"Successfully connected to catalog")
        
        # List existing namespaces as a connection test
        namespaces = catalog.list_namespaces()
        logger.info(f"Available namespaces: {namespaces}")
        
        return catalog
    except Exception as e:
        logger.error(f"Failed to connect to catalog: {e}")
        logger.debug(f"Connection error details:", exc_info=True)
        raise

def create_namespace(catalog, namespace):
    """Create a namespace if it doesn't exist"""
    logger.info(f"Checking if namespace '{namespace}' exists")
    try:
        # Check if namespace exists
        all_namespaces = catalog.list_namespaces()
        logger.debug(f"All existing namespaces: {all_namespaces}")
        
        namespace_parts = namespace.split('.')
        logger.debug(f"Namespace parts: {namespace_parts}")
        
        # Check if namespace already exists (simplified for PyIceberg 0.9.0)
        try:
            # In PyIceberg 0.9.0, namespaces returned as tuples of strings
            namespace_tuple = tuple(namespace_parts)
            namespace_exists = namespace_tuple in all_namespaces
            
            if namespace_exists:
                logger.info(f"Namespace '{namespace}' already exists")
                return True
                
            # Try an alternative check by listing tables
            try:
                tables = catalog.list_tables(namespace)
                logger.debug(f"Tables in namespace {namespace}: {tables}")
                logger.info(f"Namespace '{namespace}' already exists")
                return True
            except Exception as e:
                logger.debug(f"Error listing tables in namespace, it probably doesn't exist: {e}")
        except Exception as e:
            logger.debug(f"Error checking namespace: {e}")
                
        # Create the namespace
        logger.info(f"Creating namespace: '{namespace}'")
        catalog.create_namespace(namespace)
        logger.info(f"Successfully created namespace: '{namespace}'")
        
        # Verify creation
        all_namespaces_after = catalog.list_namespaces()
        logger.debug(f"Updated namespaces list: {all_namespaces_after}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating namespace '{namespace}': {e}")
        logger.debug("Namespace creation error details:", exc_info=True)
        return False

def define_battery_schema():
    """Define the schema for battery telemetry data"""
    logger.info("Defining battery telemetry schema")
    
    schema = Schema(
        NestedField(1, "event_time", TimestampType(), required=True),
        NestedField(2, "battery_serial", StringType(), required=True),
        NestedField(3, "latitude", DoubleType(), required=False),
        NestedField(4, "longitude", DoubleType(), required=False),
        NestedField(5, "state_of_charge", DoubleType(), required=False),
        NestedField(6, "state_of_health", DoubleType(), required=False),
        NestedField(7, "charge_cycles", IntegerType(), required=False),
        NestedField(8, "battery_voltage", DoubleType(), required=False),
        NestedField(9, "battery_current", DoubleType(), required=False),
        NestedField(10, "bms_temperature", DoubleType(), required=False)
    )
    
    logger.debug(f"Schema definition complete: {schema}")
    return schema

def create_table(catalog, namespace, table_name):
    """Create a table with the battery schema"""
    logger.info(f"Creating or validating table '{namespace}.{table_name}'")
    
    try:
        # Check if table exists
        table_identifier = f"{namespace}.{table_name}"
        logger.debug(f"Checking if table '{table_identifier}' exists")
        
        try:
            existing_table = catalog.load_table(table_identifier)
            logger.info(f"Table '{table_identifier}' already exists")
            logger.debug(f"Existing table schema: {existing_table.schema()}")
            return existing_table
        except Exception as e:
            logger.debug(f"Table '{table_identifier}' doesn't exist, will create it: {e}")
            # Table doesn't exist, we'll create it
            pass
            
        # Define the schema
        logger.info("Defining table schema")
        schema = define_battery_schema()
        
        # Create a non-partitioned table for simplicity and better compatibility
        logger.info(f"Creating unpartitioned table: '{table_identifier}'")
        
        # Create an empty partition spec (no partitioning)
        partition_spec = PartitionSpec()
        
        # Add table properties for optimization
        table_properties = {
            "write.format.default": "parquet",
            "write.parquet.compression-codec": "snappy",
            "format-version": "2"
        }
        
        table = catalog.create_table(
            identifier=table_identifier,
            schema=schema,
            partition_spec=partition_spec,
            properties=table_properties
        )
        
        logger.info(f"Successfully created unpartitioned table: '{table_identifier}'")
        logger.info(f"Table location: {table.metadata.location}")
        
        return table
        
    except Exception as e:
        logger.error(f"Error creating table '{namespace}.{table_name}': {e}")
        logger.debug("Table creation error details:", exc_info=True)
        raise

def generate_battery_records(num_records=10):
    """Generate sample battery telemetry records"""
    logger.info(f"Generating {num_records} sample battery records")
    
    records = []
    for i in range(num_records):
        battery_id = random.randint(1, 10)
        battery_serial = f"battery-{battery_id:02d}"
        
        record = {
            "event_time": datetime.utcnow(),
            "battery_serial": battery_serial,
            "latitude": round(random.uniform(-90.0, 90.0), 6),
            "longitude": round(random.uniform(-180.0, 180.0), 6),
            "state_of_charge": round(random.uniform(0.0, 100.0), 2),
            "state_of_health": round(random.uniform(60.0, 100.0), 2),
            "charge_cycles": random.randint(0, 1000),
            "battery_voltage": round(random.uniform(3000.0, 4500.0), 2),
            "battery_current": round(random.uniform(-200.0, 200.0), 2),
            "bms_temperature": round(random.uniform(20.0, 45.0), 2)
        }
        records.append(record)
        logger.debug(f"Generated record {i+1}/{num_records}: {battery_serial}")
    
    return records

def get_arrow_schema_from_table(iceberg_table):
    """Create a PyArrow schema that matches the Iceberg table schema"""
    import pyarrow as pa
    
    # Map Iceberg types to PyArrow types
    type_mappings = {
        'TimestampType': pa.timestamp('us'),
        'StringType': pa.string(),
        'DoubleType': pa.float64(),
        'IntegerType': pa.int32(),  # Use int32 to match file schema
    }
    
    # Extract field information from Iceberg schema
    fields = []
    for field in iceberg_table.schema().fields:
        pa_type = type_mappings.get(field.field_type.__class__.__name__, pa.string())
        nullable = not field.required
        fields.append(pa.field(field.name, pa_type, nullable=nullable))
    
    return pa.schema(fields)

def insert_sample_data(table, num_records=10):
    """Insert sample data into the table"""
    # Get table name in a safe way
    table_name_tuple = table.name()
    if isinstance(table_name_tuple, tuple):
        namespace = table_name_tuple[0] if len(table_name_tuple) > 0 else "default"
        tablename = table_name_tuple[-1] if len(table_name_tuple) > 0 else "unknown"
        full_table_name = ".".join(table_name_tuple)
    else:
        full_table_name = str(table_name_tuple)
        tablename = full_table_name.split(".")[-1] if "." in full_table_name else full_table_name
        namespace = full_table_name.split(".")[0] if "." in full_table_name else "default"
    
    logger.info(f"Inserting {num_records} records into table '{full_table_name}'")
    
    try:
        # Generate battery records
        records = generate_battery_records(num_records)
        
        # Get PyArrow schema that matches the Iceberg table
        arrow_schema = get_arrow_schema_from_table(table)
        logger.debug(f"Generated Arrow schema: {arrow_schema}")
        
        # Convert data to match schema
        data_dict = {field.name: [] for field in arrow_schema}
        for record in records:
            for field_name, value in record.items():
                # Cast integers to int32 if needed
                if field_name == 'charge_cycles':
                    value = int(value)  # Ensure it's an int
                data_dict[field_name].append(value)
        
        # Create PyArrow arrays with correct types
        arrays = []
        for field in arrow_schema:
            values = data_dict[field.name]
            
            if field.type == pa.int32():
                arr = pa.array(values, type=pa.int32())
            elif field.type == pa.timestamp('us'):
                arr = pa.array(values, type=pa.timestamp('us'))
            else:
                arr = pa.array(values)
                
            arrays.append(arr)
            
        # Create table with the correct schema
        pa_table = pa.Table.from_arrays(arrays, schema=arrow_schema)
        logger.info(f"Created PyArrow table with {len(pa_table)} rows using compatible schema")
        
        # Save data to backup file (JSON only, no Parquet)
        output_file = f"/var/log/schema/battery_data_{tablename}.json"
        logger.info(f"Saving data to {output_file} (as backup)")
        df = pa_table.to_pandas()
        df.to_json(output_file, orient='records', lines=True, date_format='iso')
        
        # Try to insert data using transaction API
        insertion_success = False
        
        # Important: Pass the PyArrow table directly, not the Pandas DataFrame
        try:
            logger.info("Attempting to insert data using transaction API")
            with table.transaction() as tx:
                # Pass the PyArrow table directly - not the pandas DataFrame
                tx.append(pa_table)
            logger.info(f"SUCCESS! Inserted {len(pa_table)} records using transaction API")
            insertion_success = True
        except Exception as e1:
            logger.warning(f"Transaction API failed: {e1}")
            logger.debug("Error details:", exc_info=True)
        
        # If data insertion failed, provide instructions for manual import
        if not insertion_success:
            logger.info("-" * 80)
            logger.info("DATA FILES CREATED FOR MANUAL IMPORT")
            logger.info("-" * 80)
            logger.info(f"Table: {full_table_name}")
            logger.info(f"Data file: {output_file}")
            logger.info("")
            logger.info("To import this data using:")
            logger.info("")
            logger.info("1. Spark SQL:")
            logger.info(f"   spark.read.json('{output_file}')")
            logger.info(f"   .writeTo('{namespace}.{tablename}')")
            logger.info("   .append()")
            logger.info("")
            logger.info("2. DuckDB with iceberg extension:")
            logger.info(f"   COPY (SELECT * FROM read_json_auto('{output_file}'))")
            logger.info(f"   TO iceberg('{table.metadata.location}')")
            logger.info("-" * 80)
        
        return True
            
    except Exception as e:
        logger.error(f"Error in insert_sample_data: {e}")
        logger.debug("Error details:", exc_info=True)
        logger.info("Setup completed with the table structure, but without sample data")
        return False

def main():
    """Main function to set up battery data catalog, namespace, and table"""
    logger.info("Starting battery schema setup")
    
    parser = argparse.ArgumentParser(description="Create Iceberg catalog, namespace, and table for battery data")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG_URL, help=f"Iceberg REST catalog URL (default: {DEFAULT_CATALOG_URL})")
    parser.add_argument("--warehouse", default=DEFAULT_WAREHOUSE, help=f"Warehouse name (default: {DEFAULT_WAREHOUSE})")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE, help=f"Namespace name (default: {DEFAULT_NAMESPACE})")
    parser.add_argument("--table", default=DEFAULT_TABLE_NAME, help=f"Table name (default: {DEFAULT_TABLE_NAME})")
    
    args = parser.parse_args()
    logger.info(f"Command line arguments: catalog={args.catalog}, warehouse={args.warehouse}, "
                f"namespace={args.namespace}, table={args.table}")
    
    try:
        # Connect to catalog
        logger.info("Step 1: Connecting to Iceberg catalog")
        catalog = create_catalog_connection(args.catalog, args.warehouse)
        
        # Create namespace
        logger.info("Step 2: Creating or validating namespace")
        if create_namespace(catalog, args.namespace):
            # Create table
            logger.info("Step 3: Creating or validating table")
            table = create_table(catalog, args.namespace, args.table)
            
            # Insert sample data as a separate step
            logger.info("Step 4: Inserting sample data into table")
            insert_sample_data(table)
            
            logger.info(f"Schema setup complete for table: '{args.namespace}.{args.table}'")
            
            # Print table information - handle tuple returned by table.name()
            table_name_tuple = table.name()
            if isinstance(table_name_tuple, tuple):
                full_name = ".".join(table_name_tuple)
            else:
                full_name = str(table_name_tuple)
                
            logger.info(f"Table name: {full_name}")
            logger.info(f"Table schema: {table.schema()}")
            logger.info(f"Table partition spec: {table.spec()}")
            logger.info(f"Table location: {table.metadata.location}")
            logger.info(f"Table properties: {table.properties}")
    
    except Exception as e:
        logger.error(f"Error setting up schema: {e}")
        logger.debug("Error details:", exc_info=True)
        traceback.print_exc()
        return 1
        
    logger.info("Battery schema setup and data insertion completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
