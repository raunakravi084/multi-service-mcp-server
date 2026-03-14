# How MCP Works with Databases - Complete Flow Explanation

## Example: "Give me all the tables"

Let's trace the complete flow when you ask Claude: **"Give me all the tables"**

---

## Step-by-Step Flow

### 1. **User Input in Claude Desktop**
```
You: "Give me all the tables"
```

### 2. **Claude Analyzes Request**
Claude understands you want database information and looks for available tools:
- Sees `list_tables` tool from PostgreSQL MCP server
- Determines this is the right tool to use

### 3. **MCP Protocol Communication (stdio)**
Claude Desktop sends an MCP request through stdio (standard input/output):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_tables",
    "arguments": {}
  }
}
```

This goes to: `D:\mcplatestv1\src\postgres_mcp.py`

### 4. **MCP Server Receives Request**

**File**: `src/postgres_mcp.py`

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # name = "list_tables"
    # arguments = {}
```

The `@server.call_tool()` decorator automatically handles:
- Parsing the JSON-RPC request
- Extracting tool name and arguments
- Routing to the correct handler

### 5. **Tool Routing**

```python
if name == "list_tables":
    # Loads config to get database URL
    current_config = load_config()
    current_db_url = current_config.get('database', {}).get('url', '')
    
    # Calls the database function
    result = db.list_tables(current_db_url)
```

**What happens here:**
- Loads `config.json` to get PostgreSQL connection string
- Gets: `postgresql://neondb_owner:...@.../neondb?...`
- Calls the actual database function

### 6. **Database Function Execution**

**File**: `src/postgres_db.py`

```python
def list_tables(db_url):
    """List all tables in the database"""
    conn = None
    try:
        # 1. Parse connection URL
        conn = get_connection(db_url)
        
        # 2. Execute SQL query
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
        
        # 3. Close connection
        conn.close()
        
        # 4. Return results
        return {
            "success": True,
            "tables": tables,
            "count": len(tables)
        }
```

**Database connection flow:**
1. `get_connection(db_url)` → Parses URL and connects via `psycopg2.connect()`
2. Opens connection to Neon PostgreSQL database
3. Creates cursor with `RealDictCursor` (returns rows as dictionaries)
4. Executes SQL query against `information_schema.tables`
5. Fetches results
6. Closes connection
7. Returns JSON-serializable result

### 7. **Response Formation**

**Back in**: `src/postgres_mcp.py`

```python
# Result from database function:
result = {
    "success": True,
    "tables": [
        {"table_name": "users", "table_schema": "public"},
        {"table_name": "orders", "table_schema": "public"}
    ],
    "count": 2
}

# Wrap in MCP TextContent
return [TextContent(
    type="text",
    text=json.dumps(result, indent=2, default=str)
)]
```

### 8. **MCP Server Sends Response (stdio)**

The MCP server sends JSON-RPC response back through stdio:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"success\": true,\n  \"tables\": [...],\n  \"count\": 2\n}"
      }
    ]
  }
}
```

### 9. **Claude Desktop Receives Response**

- Claude Desktop reads the response from stdio
- Parses the JSON
- Extracts the text content
- Passes it to Claude AI

### 10. **Claude AI Formats Response**

Claude receives the structured data and formats it nicely:

```
Claude: "Here are all the tables in your database:

1. users (public schema)
2. orders (public schema)

Total: 2 tables"
```

### 11. **User Sees Result**

You see Claude's formatted response in the chat interface.

---

## Visual Flow Diagram

```
┌─────────────┐
│ Claude User │
│  "Give me   │
│  all tables"│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Claude Desktop      │
│  (AI Assistant)      │
│  - Analyzes request  │
│  - Selects tool      │
└──────┬───────────────┘
       │
       │ MCP Protocol (stdio)
       │ JSON-RPC Request
       ▼
┌─────────────────────┐
│  postgres_mcp.py     │
│  @server.call_tool() │
│  - Receives request  │
│  - Routes to handler │
└──────┬───────────────┘
       │
       │ Calls function
       ▼
┌─────────────────────┐
│  postgres_db.py      │
│  list_tables()       │
│  - Parses config     │
│  - Connects to DB    │
│  - Executes SQL      │
└──────┬───────────────┘
       │
       │ SQL Query
       │ psycopg2
       ▼
┌─────────────────────┐
│  PostgreSQL Database│
│  (Neon)              │
│  - Executes query    │
│  - Returns results   │
└──────┬───────────────┘
       │
       │ Query Results
       │ (rows)
       ▼
┌─────────────────────┐
│  postgres_db.py      │
│  - Formats results   │
│  - Returns JSON      │
└──────┬───────────────┘
       │
       │ JSON Result
       ▼
┌─────────────────────┐
│  postgres_mcp.py     │
│  - Wraps in MCP      │
│  - Returns response  │
└──────┬───────────────┘
       │
       │ MCP Protocol (stdio)
       │ JSON-RPC Response
       ▼
┌─────────────────────┐
│  Claude Desktop      │
│  - Receives response │
│  - Formats display   │
└──────┬───────────────┘
       │
       ▼
┌─────────────┐
│ Claude User │
│  Sees table │
│  list       │
└─────────────┘
```

---

## Key Components Explained

### 1. **MCP Protocol (Model Context Protocol)**
- **Purpose**: Standardized way for AI assistants to interact with external tools
- **Transport**: stdio (standard input/output) for Claude Desktop
- **Format**: JSON-RPC 2.0 messages
- **Benefits**: 
  - Claude doesn't need to know database specifics
  - Tools can be swapped/modified independently
  - Standardized interface

### 2. **MCP Server (`postgres_mcp.py`)**
- **Role**: Bridge between Claude and database functions
- **Responsibilities**:
  - Register tools (define what's available)
  - Handle tool calls (route to correct function)
  - Format responses (wrap in MCP format)
  - Manage lifecycle (connection, errors, etc.)

### 3. **Database Functions (`postgres_db.py`)**
- **Role**: Pure database operations
- **Responsibilities**:
  - Connection management
  - SQL execution
  - Result formatting
  - Error handling

### 4. **Configuration (`config.json`)**
- **Stores**: Connection strings, credentials
- **Security**: Kept separate from code
- **Access**: Read by MCP server on each request

---

## Example: Write Operation Flow

For a write operation like "Insert a new user":

1. **User**: "Insert a new user with name='John' and email='john@example.com'"
2. **Claude**: Selects `execute_write` tool
3. **MCP Request**: 
   ```json
   {
     "name": "execute_write",
     "arguments": {
       "query": "INSERT INTO users (name, email) VALUES ($1, $2)",
       "params": ["John", "john@example.com"]
     }
   }
   ```
4. **MCP Server**: Routes to `db.execute_write()`
5. **Database Function**:
   - Connects
   - Executes INSERT
   - Commits transaction
   - Returns `{"rows_affected": 1}`
6. **MCP Response**: Wrapped in TextContent
7. **Claude**: Formats as "Successfully inserted 1 row"

---

## Why This Architecture?

### **Separation of Concerns**
- **MCP Server**: Protocol handling, tool registration
- **Database Functions**: Pure business logic
- **Configuration**: Externalized settings

### **Reusability**
- Database functions can be used standalone
- MCP server can be swapped for HTTP API
- Tools can be easily added/removed

### **Error Handling**
Each layer handles errors appropriately:
- Database errors → JSON error response
- MCP errors → JSON-RPC error response
- Claude formats errors for user

---

## Advanced: Multiple Tools in One Request

When you ask: "Show me all tables and count users"

1. Claude makes **two tool calls** sequentially
2. Each follows the same flow independently
3. Results are combined in Claude's response

---

## Debugging Tips

To see the actual flow, you can add logging:

**In `postgres_mcp.py`:**
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    print(f"DEBUG: Tool called: {name}", file=sys.stderr)
    print(f"DEBUG: Arguments: {arguments}", file=sys.stderr)
    # ... rest of code
```

**In `postgres_db.py`:**
```python
def list_tables(db_url):
    print(f"DEBUG: Connecting to database...", file=sys.stderr)
    # ... rest of code
```

These `stderr` messages appear in Claude Desktop's logs.

---

## Summary

**The Complete Flow:**
1. User asks Claude
2. Claude selects MCP tool
3. MCP request sent via stdio (JSON-RPC)
4. MCP server receives and routes
5. Database function executes SQL
6. Database returns results
7. Database function formats JSON
8. MCP server wraps in MCP format
9. MCP response sent via stdio
10. Claude formats and displays to user

**All happens automatically** - you just chat with Claude!

