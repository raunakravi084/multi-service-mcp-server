#!/usr/bin/env python3
"""
PostgreSQL Database Functions
Function-based operations for Neon PostgreSQL database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from urllib.parse import urlparse

def parse_db_url(db_url):
    """Parse PostgreSQL connection URL"""
    # Handle full connection string with query params
    if '?' in db_url:
        base_url, query_string = db_url.split('?', 1)
        parsed = urlparse(base_url)
        # Extract sslmode and channel_binding from query string
        query_params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
    else:
        parsed = urlparse(db_url)
        query_params = {}
    
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/').split('?')[0],
        'user': parsed.username,
        'password': parsed.password
    }
    
    # Add SSL parameters if present
    if 'sslmode' in query_params:
        conn_params['sslmode'] = query_params['sslmode']
    else:
        conn_params['sslmode'] = 'require'
    
    return conn_params

def get_connection(db_url):
    """Get PostgreSQL database connection"""
    try:
        conn_params = parse_db_url(db_url)
        conn = psycopg2.connect(**conn_params)
        return conn
    except Exception as e:
        raise Exception(f"Connection error: {str(e)}")

def execute_query(db_url, query, params=None):
    """Execute a SELECT query and return results"""
    conn = None
    try:
        conn = get_connection(db_url)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        
        conn.close()
        return {
            "success": True,
            "rows": result,
            "count": len(result)
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}

def execute_write(db_url, query, params=None):
    """Execute INSERT, UPDATE, DELETE queries"""
    conn = None
    try:
        conn = get_connection(db_url)
        
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            rows_affected = cursor.rowcount
            conn.commit()
        
        conn.close()
        return {
            "success": True,
            "rows_affected": rows_affected,
            "message": f"Query executed successfully. {rows_affected} row(s) affected."
        }
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return {"success": False, "error": str(e)}

def list_tables(db_url):
    """List all tables in the database"""
    conn = None
    try:
        conn = get_connection(db_url)
        
        query = """
            SELECT table_name, table_schema
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            tables = [dict(row) for row in rows]
        
        conn.close()
        return {
            "success": True,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}

def describe_table(db_url, table_name):
    """Get table schema information"""
    conn = None
    try:
        conn = get_connection(db_url)
        
        query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (table_name,))
            columns = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        if not columns:
            return {"success": False, "error": f"Table '{table_name}' not found"}
        
        return {
            "success": True,
            "table_name": table_name,
            "columns": columns
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}

def get_table_count(db_url, table_name):
    """Get row count for a table"""
    conn = None
    try:
        conn = get_connection(db_url)
        
        query = f'SELECT COUNT(*) as count FROM "{table_name}"'
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
        
        conn.close()
        return {
            "success": True,
            "table_name": table_name,
            "count": result['count']
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}

def run_custom_sql(db_url, sql, params=None):
    """Execute custom SQL query (handles both SELECT and write operations)"""
    sql_upper = sql.strip().upper()
    
    # Check if it's a SELECT query
    if sql_upper.startswith('SELECT') or sql_upper.startswith('WITH'):
        return execute_query(db_url, sql, params)
    else:
        # INSERT, UPDATE, DELETE, etc.
        return execute_write(db_url, sql, params)

