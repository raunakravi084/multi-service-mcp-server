#!/usr/bin/env python3
"""
PostgreSQL MCP Server for Claude Desktop
Provides database operations via Model Context Protocol
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import src.postgres_db as db

def load_config():
    """Load database configuration"""
    try:
        # Try multiple possible paths
        possible_paths = [
            Path(__file__).parent.parent / 'config.json',  # Standard location
            Path.cwd() / 'config.json',  # Current working directory
            Path.home() / 'mcplatestv1' / 'config.json',  # Alternative location
        ]
        
        for config_path in possible_paths:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        
        # If no config file found, return empty dict
        return {'database': {}}
    except Exception as e:
        # Return error info for debugging
        return {'database': {}, 'error': str(e)}

config = load_config()
db_url = config.get('database', {}).get('url', '')

server = Server("postgresql-mcp-server")

@server.list_tools()
async def list_tools():
    """List all available database tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SELECT query and return results. Use for reading data from tables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional query parameters for parameterized queries",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_write",
            description="Execute INSERT, UPDATE, or DELETE queries. Use for modifying data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL INSERT, UPDATE, or DELETE query"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional query parameters",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="run_custom_sql",
            description="Execute any SQL query (SELECT, INSERT, UPDATE, DELETE, etc.). Automatically handles query type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Any SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional query parameters",
                        "items": {"type": "string"}
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database with their schemas",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="describe_table",
            description="Get detailed schema information for a specific table including columns, types, and constraints",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="get_table_count",
            description="Get the total number of rows in a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool execution"""
    try:
        # Reload config on each call to ensure we have the latest
        current_config = load_config()
        current_db_url = current_config.get('database', {}).get('url', '')
        
        if not current_db_url:
            # Try to provide helpful error message
            config_path = Path(__file__).parent.parent / 'config.json'
            error_msg = {
                "success": False,
                "error": "Database URL not configured",
                "details": "Please add 'database.url' to config.json",
                "config_location": str(config_path),
                "config_exists": config_path.exists(),
                "config_keys": list(current_config.keys())
            }
            if 'error' in current_config:
                error_msg["config_error"] = current_config['error']
            return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]
        
        result = None
        
        if name == "execute_query":
            query = arguments.get("query")
            params = arguments.get("params")
            result = db.execute_query(current_db_url, query, params)
        
        elif name == "execute_write":
            query = arguments.get("query")
            params = arguments.get("params")
            result = db.execute_write(current_db_url, query, params)
        
        elif name == "run_custom_sql":
            sql = arguments.get("sql")
            params = arguments.get("params")
            result = db.run_custom_sql(current_db_url, sql, params)
        
        elif name == "list_tables":
            result = db.list_tables(current_db_url)
        
        elif name == "describe_table":
            table_name = arguments.get("table_name")
            result = db.describe_table(current_db_url, table_name)
        
        elif name == "get_table_count":
            table_name = arguments.get("table_name")
            result = db.get_table_count(current_db_url, table_name)
        
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as error:
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": str(error)}, indent=2)
        )]

async def main():
    """Main entry point for MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

