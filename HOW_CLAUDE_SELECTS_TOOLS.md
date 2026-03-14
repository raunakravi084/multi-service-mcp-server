# How Claude Understands Which Tool to Call

## The Question: How does Claude know to call `list_tables`?

When you say **"Give me all the tables"**, how does Claude know to:
1. Recognize this is a database request
2. Select the `list_tables` tool
3. Not use `execute_query` or other tools?

---

## Step 1: Tool Registration - Telling Claude What's Available

When Claude Desktop starts, it first asks the MCP server: **"What tools do you have?"**

### Initialization Flow

```
Claude Desktop → MCP Server: "What tools are available?"
MCP Server → Claude Desktop: Returns tool list with descriptions
```

### Code: Tool Registration (`postgres_mcp.py`)

```python
@server.list_tools()
async def list_tools():
    """This function is called ONCE when Claude Desktop starts"""
    return [
        Tool(
            name="list_tables",                    # ← Tool identifier
            description="List all tables in the database with their schemas",  # ← Claude reads this!
            inputSchema={
                "type": "object",
                "properties": {},
                # No parameters needed - makes it easy to use
            }
        ),
        Tool(
            name="execute_query",
            description="Execute a SELECT query and return results. Use for reading data from tables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        # ... other tools
    ]
```

### What Claude Receives

Claude gets a JSON response like this:

```json
{
  "tools": [
    {
      "name": "list_tables",
      "description": "List all tables in the database with their schemas",
      "inputSchema": {"properties": {}}
    },
    {
      "name": "execute_query",
      "description": "Execute a SELECT query and return results. Use for reading data from tables.",
      "inputSchema": {
        "properties": {
          "query": {"type": "string", "description": "SQL SELECT query"}
        },
        "required": ["query"]
      }
    }
  ]
}
```

---

## Step 2: Claude's Natural Language Understanding

Claude has been trained on:
- Natural language patterns
- Database concepts (tables, queries, schemas)
- Tool descriptions from MCP servers

### Semantic Matching Process

When you say: **"Give me all the tables"**

Claude's internal process:

1. **Parse Intent:**
   - "Give me" = request for information
   - "all the tables" = wants complete list of database tables

2. **Match Against Available Tools:**
   - Searches through registered tool descriptions
   - Looks for semantic matches

3. **Semantic Matching Example:**

```
Your Request: "Give me all the tables"

Tool: list_tables
Description: "List all tables in the database with their schemas"
Match Score: ⭐⭐⭐⭐⭐ (Perfect match - "all tables" = "List all tables")

Tool: execute_query  
Description: "Execute a SELECT query and return results"
Match Score: ⭐⭐ (Partial - could work but requires writing SQL)

Tool: describe_table
Description: "Get detailed schema information for a specific table"
Match Score: ⭐ (Wrong - needs specific table name)
```

4. **Selection Logic:**
   - `list_tables` has highest semantic match
   - No parameters needed (easy to use)
   - Purpose directly matches the request
   - **Selected! ✅**

---

## Step 3: How Tool Descriptions Guide Selection

### Good Description = Better Matching

**Tool Definition:**
```python
Tool(
    name="list_tables",
    description="List all tables in the database with their schemas"
    #         ↑ "all tables" ← Claude matches your phrase here!
)
```

**Key phrases Claude looks for:**
- "all tables" → matches "List **all tables**"
- "show tables" → matches "**List** all **tables**"
- "what tables exist" → matches "List all **tables in the database**"
- "database tables" → matches "List all tables **in the database**"

### Example: Why Other Tools Don't Match

**User:** "Give me all the tables"

**Tool: `execute_query`**
- Description: "Execute a SELECT query and return results"
- Match: ⚠️ Requires writing SQL: `SELECT table_name FROM information_schema.tables`
- Claude thinks: "I could use this, but it's harder. Is there a better tool?"

**Tool: `list_tables`**
- Description: "List all tables in the database"
- Match: ✅ Directly matches "all the tables"
- Claude thinks: "Perfect! This is exactly what the user wants."

**Result:** Claude selects `list_tables`

---

## Step 4: Claude's Decision Process (Simplified)

```
User Input: "Give me all the tables"
    ↓
Claude's Internal Reasoning:
    
    1. Parse request:
       - Intent: GET information
       - Topic: database tables
       - Scope: all (not specific table)
    
    2. Check available tools:
       - list_tables: "List all tables..." ← Perfect!
       - execute_query: "Execute SQL..." ← Could work but harder
       - describe_table: "Get schema for specific table" ← Wrong scope
    
    3. Select best match:
       ✅ list_tables
         - No parameters needed
         - Direct semantic match
         - Purpose aligns perfectly
    
    4. Call tool:
       {"name": "list_tables", "arguments": {}}
```

---

## How Tool Schema Helps

### Schema Provides Context

```python
Tool(
    name="list_tables",
    description="List all tables in the database with their schemas",
    inputSchema={
        "type": "object",
        "properties": {}  # ← No parameters = simple, safe to call
    }
)
```

Claude sees:
- ✅ No required parameters = easy to use
- ✅ Safe operation (read-only)
- ✅ Direct match for "all tables"

Compare to:

```python
Tool(
    name="describe_table",
    description="Get detailed schema information for a specific table",
    inputSchema={
        "properties": {
            "table_name": {"type": "string"}  # ← Requires parameter
        },
        "required": ["table_name"]  # ← Can't call without this!
    }
)
```

Claude sees:
- ⚠️ Requires `table_name` parameter
- ⚠️ You said "all tables" but this needs one table
- ❌ Not a good match for "all"

---

## Real Examples

### Example 1: "Give me all the tables"
```
User: "Give me all the tables"
    ↓
Claude matches:
    "all the tables" → "List all tables" ✅
    ↓
Calls: list_tables()
```

### Example 2: "Show me users table structure"
```
User: "Show me users table structure"
    ↓
Claude matches:
    "users table structure" → "Get detailed schema information for a specific table" ✅
    ↓
Calls: describe_table(table_name="users")
```

### Example 3: "How many users are there?"
```
User: "How many users are there?"
    ↓
Claude matches:
    "How many" → needs to count
    "users" → table name
    ↓
Claude generates SQL: SELECT COUNT(*) FROM users
    ↓
Calls: execute_query(query="SELECT COUNT(*) FROM users")
```

---

## How Claude Handles Complex Requests

### Example: "Show me all tables and count users in each"

Claude's process:
1. **Break down request:**
   - Part 1: "all tables" → `list_tables()`
   - Part 2: "count users in each" → needs iteration

2. **Execute sequentially:**
   ```
   Step 1: Call list_tables()
       Result: ["users", "orders", "products"]
   
   Step 2: For each table, count documents
       execute_query("SELECT COUNT(*) FROM users") → 150
       execute_query("SELECT COUNT(*) FROM orders") → 500
       execute_query("SELECT COUNT(*) FROM products") → 50
   ```

3. **Combine results:**
   ```
   Tables: users (150 rows), orders (500 rows), products (50 rows)
   ```

---

## Improving Tool Selection: Writing Better Descriptions

### ❌ Bad Description
```python
Tool(
    name="list_tables",
    description="Database tool"  # Too vague!
)
```

### ✅ Good Description
```python
Tool(
    name="list_tables",
    description="List all tables in the database with their schemas"  # Specific and clear!
)
```

### ✅ Better Description (with use cases)
```python
Tool(
    name="list_tables",
    description="List all tables in the database with their schemas. Use this when the user asks to see all tables, what tables exist, or wants a list of database tables."
)
```

---

## The Magic: Semantic Understanding

Claude doesn't do exact string matching. It uses:

1. **Semantic similarity:**
   - "all tables" ≈ "list all tables"
   - "show tables" ≈ "list tables"
   - "what tables" ≈ "list all tables"

2. **Context understanding:**
   - Understands database concepts
   - Knows what "tables" means
   - Understands "all" vs "specific"

3. **Parameter inference:**
   - If tool needs parameters, Claude tries to extract them
   - If tool has no parameters, Claude knows it's simple

---

## Summary

**How Claude knows to call `list_tables`:**

1. **Tool Registration:** MCP server tells Claude about `list_tables` with description
2. **Semantic Matching:** Claude's AI matches "all tables" → "List all tables"
3. **Schema Analysis:** No parameters needed = easy to use
4. **Selection:** Best match is `list_tables`
5. **Execution:** Claude calls the tool

**Key Point:** The `description` field in tool registration is **critical** - it's what Claude reads to understand when to use each tool!

The better your description, the better Claude's tool selection will be.

