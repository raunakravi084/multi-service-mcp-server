#!/usr/bin/env python3
"""
Pure MCP Server - Standard Implementation
Works with any MCP client via stdio
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
import src.google_sheets as sheets
import src.google_gmail as gmail
import src.google_calendar as calendar

def load_config():
    try:
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            return json.load(f)
    except:
        return {'google': {}}

config = load_config()

server = Server("google-services-mcp-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_sheet",
            description="Read data from a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheetId": {"type": "string", "description": "The ID of the spreadsheet"},
                    "range": {"type": "string", "description": "The range to read (e.g., 'Sheet1!A1:B10')"}
                },
                "required": ["spreadsheetId", "range"]
            }
        ),
        Tool(
            name="write_sheet",
            description="Write data to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheetId": {"type": "string"},
                    "range": {"type": "string"},
                    "values": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                        "description": "2D array of values to write"
                    }
                },
                "required": ["spreadsheetId", "range", "values"]
            }
        ),
        Tool(
            name="append_sheet",
            description="Append data to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheetId": {"type": "string"},
                    "range": {"type": "string"},
                    "values": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "required": ["spreadsheetId", "range", "values"]
            }
        ),
        Tool(
            name="get_sheet_info",
            description="Get information about a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheetId": {"type": "string"}
                },
                "required": ["spreadsheetId"]
            }
        ),
        Tool(
            name="list_emails",
            description="List emails from Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "maxResults": {"type": "integer", "description": "Maximum number of emails", "default": 10},
                    "query": {"type": "string", "description": "Gmail search query", "default": ""}
                }
            }
        ),
        Tool(
            name="get_email_detail",
            description="Get detailed information about a specific email",
            inputSchema={
                "type": "object",
                "properties": {
                    "messageId": {"type": "string", "description": "The Gmail message ID"}
                },
                "required": ["messageId"]
            }
        ),
        Tool(
            name="send_email",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "isHtml": {"type": "boolean", "description": "Whether the body is HTML", "default": False}
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails in Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_calendar_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendarId": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                    "maxResults": {"type": "integer", "description": "Maximum number of events", "default": 10},
                    "timeMin": {"type": "string", "description": "Minimum time (ISO 8601 format)"}
                }
            }
        ),
        Tool(
            name="create_calendar_event",
            description="Create a new calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendarId": {"type": "string", "default": "primary"},
                    "summary": {"type": "string", "description": "Event title"},
                    "description": {"type": "string", "description": "Event description"},
                    "start": {"type": "string", "description": "Start time (ISO 8601 format)"},
                    "end": {"type": "string", "description": "End time (ISO 8601 format)"},
                    "location": {"type": "string", "description": "Event location"},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of attendee email addresses"
                    },
                    "timeZone": {"type": "string", "default": "America/Los_Angeles"}
                },
                "required": ["summary", "start", "end"]
            }
        ),
        Tool(
            name="update_calendar_event",
            description="Update an existing calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendarId": {"type": "string", "default": "primary"},
                    "eventId": {"type": "string", "description": "Event ID to update"},
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "location": {"type": "string"},
                    "attendees": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["eventId"]
            }
        ),
        Tool(
            name="delete_calendar_event",
            description="Delete a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendarId": {"type": "string", "default": "primary"},
                    "eventId": {"type": "string", "description": "Event ID to delete"}
                },
                "required": ["eventId"]
            }
        ),
        Tool(
            name="get_calendar_event",
            description="Get details of a specific calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendarId": {"type": "string", "default": "primary"},
                    "eventId": {"type": "string", "description": "Event ID"}
                },
                "required": ["eventId"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        result = None
        
        if name == "read_sheet":
            spreadsheet_id = arguments.get("spreadsheetId") or config.get("google", {}).get("spreadsheetId")
            result = sheets.read_sheet_data(spreadsheet_id, arguments["range"])
        
        elif name == "write_sheet":
            spreadsheet_id = arguments.get("spreadsheetId") or config.get("google", {}).get("spreadsheetId")
            result = sheets.write_sheet_data(spreadsheet_id, arguments["range"], arguments["values"])
        
        elif name == "append_sheet":
            spreadsheet_id = arguments.get("spreadsheetId") or config.get("google", {}).get("spreadsheetId")
            result = sheets.append_sheet_data(spreadsheet_id, arguments["range"], arguments["values"])
        
        elif name == "get_sheet_info":
            spreadsheet_id = arguments.get("spreadsheetId") or config.get("google", {}).get("spreadsheetId")
            result = sheets.get_sheet_info(spreadsheet_id)
        
        elif name == "list_emails":
            result = gmail.list_emails(arguments.get("maxResults", 10), arguments.get("query", ""))
        
        elif name == "get_email_detail":
            result = gmail.get_email_detail(arguments["messageId"])
        
        elif name == "send_email":
            result = gmail.send_email(
                arguments["to"],
                arguments["subject"],
                arguments["body"],
                arguments.get("isHtml", False)
            )
        
        elif name == "search_emails":
            result = gmail.search_emails(arguments["query"])
        
        elif name == "list_calendar_events":
            result = calendar.list_events(
                arguments.get("calendarId") or config.get("google", {}).get("calendarId", "primary"),
                arguments.get("maxResults", 10),
                arguments.get("timeMin")
            )
        
        elif name == "create_calendar_event":
            result = calendar.create_event(
                arguments.get("calendarId") or config.get("google", {}).get("calendarId", "primary"),
                {
                    "summary": arguments["summary"],
                    "description": arguments.get("description", ""),
                    "start": arguments["start"],
                    "end": arguments["end"],
                    "location": arguments.get("location", ""),
                    "attendees": arguments.get("attendees", []),
                    "timeZone": arguments.get("timeZone", "America/Los_Angeles")
                }
            )
        
        elif name == "update_calendar_event":
            result = calendar.update_event(
                arguments.get("calendarId") or config.get("google", {}).get("calendarId", "primary"),
                arguments["eventId"],
                {
                    "summary": arguments.get("summary"),
                    "description": arguments.get("description"),
                    "start": arguments.get("start"),
                    "end": arguments.get("end"),
                    "location": arguments.get("location"),
                    "attendees": arguments.get("attendees"),
                    "timeZone": arguments.get("timeZone", "America/Los_Angeles")
                }
            )
        
        elif name == "delete_calendar_event":
            result = calendar.delete_event(
                arguments.get("calendarId") or config.get("google", {}).get("calendarId", "primary"),
                arguments["eventId"]
            )
        
        elif name == "get_calendar_event":
            result = calendar.get_event(
                arguments.get("calendarId") or config.get("google", {}).get("calendarId", "primary"),
                arguments["eventId"]
            )
        
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as error:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(error)}, indent=2))]

async def main():
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
