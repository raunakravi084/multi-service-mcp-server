# Multi-Service MCP Server for Claude Desktop


MCP (Model Context Protocol) server for Claude Desktop that provides access to Google Sheets, Gmail, Google Calendar, PostgreSQL, and MongoDB. 

## Features

- **13 MCP Tools**:
  - **Google Sheets (4 tools)**: Read, write, append, and get sheet info
  - **Gmail (4 tools)**: List, search, get details, and send emails
  - **Google Calendar (5 tools)**: List, create, update, delete, and get event details
  - **PostgreSQL MCP server**
  - Run read/write SQL queries
  - List tables, describe schema, count rows
- **MongoDB MCP server**
  - List databases and collections
  - Find, insert, update, delete, count, and aggregate documents


## Prerequisites

- Python 3.8 or higher
- Google Cloud Project with APIs enabled:
  - Google Sheets API
  - Gmail API
  - Google Calendar API
- OAuth 2.0 credentials (`credentials.json`)
- Claude Desktop installed

## Installation

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd mcplatestv1

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Google OAuth

1. Download `credentials.json` from [Google Cloud Console](https://console.cloud.google.com/)
2. Place `credentials.json` in the project root directory
3. Run the setup script to authenticate:

```bash
python src/setup.py
```

4. Follow the prompts to authorize access to your Google account
5. The script will create `tokens.json` with your access tokens

### 3. Configure Your Services

Edit `config.json`:

```json
{
  "google": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "redirectUri": "http://localhost",
    "spreadsheetId": "your-spreadsheet-id",
    "calendarId": "primary"
  }
}
```

**Note**: `spreadsheetId` and `calendarId` are optional - you can specify them per tool call.

## Claude Desktop Setup

### Step 1: Find Claude Desktop Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
Example: `C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json`

**Mac:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Edit Config File

Open the config file (create it if it doesn't exist) and add:

```json
{
  "mcpServers": {
    "google-services": {
      "command": "python",
      "args": [
        "D:\\mcplatestv1\\src\\mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

**Important**: 
- Update the path to match your actual project location
- On Windows, use double backslashes (`\\`) in the path
- On Mac/Linux, use forward slashes (`/`)

### Step 3: Restart Claude Desktop

**Completely quit and restart Claude Desktop** for the changes to take effect.

### Step 4: Verify Connection

After restarting:
1. Claude Desktop will automatically start the MCP server
2. All 13 tools should be available
3. Test by asking Claude: *"What tools do you have access to?"*

## Usage

Once connected, you can ask Claude to:

- **Read from Sheets**: "Read the data from Sheet1!A1:B10"
- **Write to Sheets**: "Write these values to my spreadsheet: [['Name', 'Age'], ['John', '30']]"
- **List Emails**: "Show me my last 10 emails"
- **Send Email**: "Send an email to john@example.com with subject 'Hello' and body 'Test message'"
- **Create Events**: "Create a calendar event for tomorrow at 2pm titled 'Meeting'"

## Available Tools

### Google Sheets
- `read_sheet` - Read data from a range
- `write_sheet` - Write data to a range
- `append_sheet` - Append data to a sheet
- `get_sheet_info` - Get spreadsheet information

### Gmail
- `list_emails` - List emails from inbox
- `get_email_detail` - Get detailed email information
- `send_email` - Send an email
- `search_emails` - Search emails with a query

### Google Calendar
- `list_calendar_events` - List upcoming events
- `create_calendar_event` - Create a new event
- `update_calendar_event` - Update an existing event
- `delete_calendar_event` - Delete an event
- `get_calendar_event` - Get event details

## Troubleshooting

### Server Won't Start

1. **Check Python path**: Make sure Python is in your system PATH
   - Test: Open terminal and type `python --version`
   - If not found, use full path: `"C:\\Python\\python.exe"`

2. **Check file path**: Verify the path to `mcp_server.py` is correct
   - Use absolute path in config file
   - Windows: `D:\\mcplatestv1\\src\\mcp_server.py`
   - Mac/Linux: `/path/to/mcplatestv1/src/mcp_server.py`

3. **Check dependencies**: Make sure all packages are installed
   ```bash
   pip install -r requirements.txt
   ```

### Tools Not Appearing

1. **Check Claude Desktop logs**:
   - Look for error messages in Claude Desktop console
   - Check if server process is running

2. **Verify authentication**:
   - Make sure `tokens.json` exists and is valid
   - Re-run `python src/setup.py` if needed

3. **Restart Claude Desktop**:
   - Completely quit (not just close window)
   - Restart and check again

### Authentication Errors

1. **Re-authenticate**: Run `python src/setup.py` again
2. **Check credentials**: Verify `credentials.json` is valid
3. **Check scopes**: Ensure all required APIs are enabled in Google Cloud Console

## Project Structure

```
mcplatestv1/
├── src/
│   ├── mcp_server.py          # Main MCP server (stdio protocol)
│   ├── google_auth.py         # Google OAuth handling
│   ├── google_sheets.py       # Google Sheets functions
│   ├── google_gmail.py        # Gmail functions
│   ├── google_calendar.py     # Calendar functions
│   ├── agent.py               # Automatic decision logic
│   └── setup.py               # Initial setup script
├── config.json                # Configuration (your credentials)
├── config.example.json        # Configuration template
├── credentials.json           # Google OAuth credentials (download from Cloud Console)
├── tokens.json               # OAuth tokens (generated by setup.py)
├── requirements.txt           # Python dependencies
├── claude_desktop_config.json # Example Claude Desktop config
└── README.md                  # This file
```

## License

This project is for personal use. Make sure to keep your `credentials.json` and `config.json` files secure and never commit them to version control.
