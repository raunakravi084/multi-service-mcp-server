#!/usr/bin/env python3
"""
MongoDB Database Functions
Function-based operations for MongoDB Atlas database
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
import json
from bson import ObjectId
from bson.json_util import dumps, loads

class MongoDBEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId and other BSON types"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def get_connection(mongo_uri):
    """Get MongoDB database connection"""
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        # Test connection
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        raise Exception(f"Connection error: {str(e)}")
    except Exception as e:
        raise Exception(f"Connection error: {str(e)}")

def list_databases(mongo_uri):
    """List all databases"""
    try:
        client = get_connection(mongo_uri)
        databases = client.list_database_names()
        client.close()
        return {
            "success": True,
            "databases": databases,
            "count": len(databases)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_collections(mongo_uri, database_name):
    """List all collections in a database"""
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collections = db.list_collection_names()
        client.close()
        return {
            "success": True,
            "database": database_name,
            "collections": collections,
            "count": len(collections)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def find_documents(mongo_uri, database_name, collection_name, query=None, limit=100, skip=0, sort=None):
    """Find documents in a collection"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse query if string
        if isinstance(query, str):
            query = json.loads(query) if query else {}
        elif query is None:
            query = {}
        
        # Parse sort if string
        if isinstance(sort, str):
            sort = json.loads(sort) if sort else None
        
        # Build cursor
        cursor = collection.find(query)
        
        # Apply sort
        if sort:
            cursor = cursor.sort(list(sort.items()) if isinstance(sort, dict) else sort)
        
        # Apply skip and limit
        cursor = cursor.skip(skip).limit(limit)
        
        # Fetch results
        documents = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        result = json.loads(dumps(documents))
        
        client.close()
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "documents": result,
            "count": len(result)
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def insert_document(mongo_uri, database_name, collection_name, document):
    """Insert a single document"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse document if string
        if isinstance(document, str):
            document = json.loads(document)
        
        result = collection.insert_one(document)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "inserted_id": str(result.inserted_id),
            "message": "Document inserted successfully"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def insert_many_documents(mongo_uri, database_name, collection_name, documents):
    """Insert multiple documents"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse documents if string
        if isinstance(documents, str):
            documents = json.loads(documents)
        
        result = collection.insert_many(documents)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "inserted_ids": [str(id) for id in result.inserted_ids],
            "count": len(result.inserted_ids),
            "message": f"{len(result.inserted_ids)} documents inserted successfully"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def update_document(mongo_uri, database_name, collection_name, filter_query, update_data, upsert=False):
    """Update a single document"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse queries if strings
        if isinstance(filter_query, str):
            filter_query = json.loads(filter_query)
        
        if isinstance(update_data, str):
            update_data = json.loads(update_data)
        
        # Convert _id string to ObjectId if present
        if '_id' in filter_query:
            filter_query['_id'] = ObjectId(filter_query['_id'])
        
        # Add $set operator if update_data doesn't have operators
        if not any(key.startswith('$') for key in update_data.keys()):
            update_data = {'$set': update_data}
        
        result = collection.update_one(filter_query, update_data, upsert=upsert)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            "message": f"Update completed. Matched: {result.matched_count}, Modified: {result.modified_count}"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def update_many_documents(mongo_uri, database_name, collection_name, filter_query, update_data, upsert=False):
    """Update multiple documents"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse queries if strings
        if isinstance(filter_query, str):
            filter_query = json.loads(filter_query)
        
        if isinstance(update_data, str):
            update_data = json.loads(update_data)
        
        # Convert _id string to ObjectId if present
        if '_id' in filter_query:
            filter_query['_id'] = ObjectId(filter_query['_id'])
        
        # Add $set operator if update_data doesn't have operators
        if not any(key.startswith('$') for key in update_data.keys()):
            update_data = {'$set': update_data}
        
        result = collection.update_many(filter_query, update_data, upsert=upsert)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            "message": f"Update completed. Matched: {result.matched_count}, Modified: {result.modified_count}"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def delete_document(mongo_uri, database_name, collection_name, filter_query):
    """Delete a single document"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse query if string
        if isinstance(filter_query, str):
            filter_query = json.loads(filter_query)
        
        # Convert _id string to ObjectId if present
        if '_id' in filter_query:
            filter_query['_id'] = ObjectId(filter_query['_id'])
        
        result = collection.delete_one(filter_query)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "deleted_count": result.deleted_count,
            "message": f"{result.deleted_count} document(s) deleted"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def delete_many_documents(mongo_uri, database_name, collection_name, filter_query):
    """Delete multiple documents"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse query if string
        if isinstance(filter_query, str):
            filter_query = json.loads(filter_query)
        
        # Convert _id string to ObjectId if present
        if '_id' in filter_query:
            filter_query['_id'] = ObjectId(filter_query['_id'])
        
        result = collection.delete_many(filter_query)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "deleted_count": result.deleted_count,
            "message": f"{result.deleted_count} document(s) deleted"
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def count_documents(mongo_uri, database_name, collection_name, query=None):
    """Count documents in a collection"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse query if string
        if isinstance(query, str):
            query = json.loads(query) if query else {}
        elif query is None:
            query = {}
        
        count = collection.count_documents(query)
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "count": count
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

def aggregate(mongo_uri, database_name, collection_name, pipeline):
    """Run aggregation pipeline"""
    client = None
    try:
        client = get_connection(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse pipeline if string
        if isinstance(pipeline, str):
            pipeline = json.loads(pipeline)
        
        result = list(collection.aggregate(pipeline))
        result_data = json.loads(dumps(result))
        
        client.close()
        
        return {
            "success": True,
            "database": database_name,
            "collection": collection_name,
            "documents": result_data,
            "count": len(result_data)
        }
    except Exception as e:
        if client:
            client.close()
        return {"success": False, "error": str(e)}

