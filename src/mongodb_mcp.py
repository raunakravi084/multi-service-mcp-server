#!/usr/bin/env python3
"""
MongoDB MCP Server for Claude Desktop
Provides MongoDB operations via Model Context Protocol
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import src.mongodb_db as mongo

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
        return {'mongodb': {}}
    except Exception as e:
        # Return error info for debugging
        return {'mongodb': {}, 'error': str(e)}

config = load_config()
mongo_uri = config.get('mongodb', {}).get('uri', '')

server = Server("mongodb-mcp-server")

@server.list_tools()
async def list_tools():
    """List all available MongoDB tools"""
    return [
        Tool(
            name="list_databases",
            description="List all databases in MongoDB",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_collections",
            description="List all collections in a specific database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "Name of the database"
                    }
                },
                "required": ["database_name"]
            }
        ),
        Tool(
            name="find_documents",
            description="Find documents in a collection. Supports query, limit, skip, and sort options.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "query": {
                        "type": "string",
                        "description": "MongoDB query filter (JSON string, e.g., '{\"name\": \"John\"}')"
                    },
                    "limit": {"type": "integer", "description": "Maximum number of documents to return (default: 100)"},
                    "skip": {"type": "integer", "description": "Number of documents to skip (default: 0)"},
                    "sort": {
                        "type": "string",
                        "description": "Sort criteria (JSON string, e.g., '{\"name\": 1}' for ascending)"
                    }
                },
                "required": ["database_name", "collection_name"]
            }
        ),
        Tool(
            name="insert_document",
            description="Insert a single document into a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "document": {
                        "type": "string",
                        "description": "Document to insert (JSON string, e.g., '{\"name\": \"John\", \"age\": 30}')"
                    }
                },
                "required": ["database_name", "collection_name", "document"]
            }
        ),
        Tool(
            name="insert_many_documents",
            description="Insert multiple documents into a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "documents": {
                        "type": "string",
                        "description": "Array of documents to insert (JSON string, e.g., '[{\"name\": \"John\"}, {\"name\": \"Jane\"}]')"
                    }
                },
                "required": ["database_name", "collection_name", "documents"]
            }
        ),
        Tool(
            name="update_document",
            description="Update a single document in a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "filter_query": {
                        "type": "string",
                        "description": "Filter query to find document (JSON string, e.g., '{\"_id\": \"...\"}')"
                    },
                    "update_data": {
                        "type": "string",
                        "description": "Update data (JSON string, e.g., '{\"name\": \"John Updated\"}')"
                    },
                    "upsert": {
                        "type": "boolean",
                        "description": "Create document if it doesn't exist (default: false)"
                    }
                },
                "required": ["database_name", "collection_name", "filter_query", "update_data"]
            }
        ),
        Tool(
            name="update_many_documents",
            description="Update multiple documents in a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "filter_query": {
                        "type": "string",
                        "description": "Filter query to find documents"
                    },
                    "update_data": {
                        "type": "string",
                        "description": "Update data for matching documents"
                    },
                    "upsert": {"type": "boolean", "description": "Create documents if they don't exist"}
                },
                "required": ["database_name", "collection_name", "filter_query", "update_data"]
            }
        ),
        Tool(
            name="delete_document",
            description="Delete a single document from a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "filter_query": {
                        "type": "string",
                        "description": "Filter query to find document to delete"
                    }
                },
                "required": ["database_name", "collection_name", "filter_query"]
            }
        ),
        Tool(
            name="delete_many_documents",
            description="Delete multiple documents from a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "filter_query": {
                        "type": "string",
                        "description": "Filter query to find documents to delete"
                    }
                },
                "required": ["database_name", "collection_name", "filter_query"]
            }
        ),
        Tool(
            name="count_documents",
            description="Count documents in a collection matching a query",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "query": {
                        "type": "string",
                        "description": "Query filter (JSON string, optional)"
                    }
                },
                "required": ["database_name", "collection_name"]
            }
        ),
        Tool(
            name="aggregate",
            description="Run MongoDB aggregation pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {"type": "string", "description": "Database name"},
                    "collection_name": {"type": "string", "description": "Collection name"},
                    "pipeline": {
                        "type": "string",
                        "description": "Aggregation pipeline (JSON array string, e.g., '[{\"$match\": {...}}, {\"$group\": {...}}]')"
                    }
                },
                "required": ["database_name", "collection_name", "pipeline"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool execution"""
    try:
        # Reload config on each call to ensure we have the latest
        current_config = load_config()
        current_mongo_uri = current_config.get('mongodb', {}).get('uri', '')
        
        if not current_mongo_uri:
            # Try to provide helpful error message
            config_path = Path(__file__).parent.parent / 'config.json'
            error_msg = {
                "success": False,
                "error": "MongoDB URI not configured",
                "details": "Please add 'mongodb.uri' to config.json",
                "config_location": str(config_path),
                "config_exists": config_path.exists(),
                "config_keys": list(current_config.keys())
            }
            if 'error' in current_config:
                error_msg["config_error"] = current_config['error']
            return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]
        
        result = None
        
        if name == "list_databases":
            result = mongo.list_databases(current_mongo_uri)
        
        elif name == "list_collections":
            database_name = arguments.get("database_name")
            result = mongo.list_collections(current_mongo_uri, database_name)
        
        elif name == "find_documents":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            query = arguments.get("query")
            limit = arguments.get("limit", 100)
            skip = arguments.get("skip", 0)
            sort = arguments.get("sort")
            result = mongo.find_documents(current_mongo_uri, database_name, collection_name, query, limit, skip, sort)
        
        elif name == "insert_document":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            document = arguments.get("document")
            result = mongo.insert_document(current_mongo_uri, database_name, collection_name, document)
        
        elif name == "insert_many_documents":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            documents = arguments.get("documents")
            result = mongo.insert_many_documents(current_mongo_uri, database_name, collection_name, documents)
        
        elif name == "update_document":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            filter_query = arguments.get("filter_query")
            update_data = arguments.get("update_data")
            upsert = arguments.get("upsert", False)
            result = mongo.update_document(current_mongo_uri, database_name, collection_name, filter_query, update_data, upsert)
        
        elif name == "update_many_documents":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            filter_query = arguments.get("filter_query")
            update_data = arguments.get("update_data")
            upsert = arguments.get("upsert", False)
            result = mongo.update_many_documents(current_mongo_uri, database_name, collection_name, filter_query, update_data, upsert)
        
        elif name == "delete_document":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            filter_query = arguments.get("filter_query")
            result = mongo.delete_document(current_mongo_uri, database_name, collection_name, filter_query)
        
        elif name == "delete_many_documents":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            filter_query = arguments.get("filter_query")
            result = mongo.delete_many_documents(current_mongo_uri, database_name, collection_name, filter_query)
        
        elif name == "count_documents":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            query = arguments.get("query")
            result = mongo.count_documents(current_mongo_uri, database_name, collection_name, query)
        
        elif name == "aggregate":
            database_name = arguments.get("database_name")
            collection_name = arguments.get("collection_name")
            pipeline = arguments.get("pipeline")
            result = mongo.aggregate(current_mongo_uri, database_name, collection_name, pipeline)
        
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

