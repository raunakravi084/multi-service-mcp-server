# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Setup Google Authentication

1. Download `credentials.json` from Google Cloud Console
2. Place it in the project root
3. Run:
```bash
python src/setup.py
```
4. Follow the prompts to authorize

## Step 3: Configure Claude Desktop

1. **Find config file:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add this to config file:**
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

**IMPORTANT**: Replace `D:\\mcplatestv1\\src\\mcp_server.py` with your actual project path!

3. **Restart Claude Desktop completely**

4. **Test**: Ask Claude "What tools do you have access to?"

## Troubleshooting

- **Path issues**: Use absolute path, double backslashes on Windows
- **Python not found**: Use full path to python.exe: `"C:\\Python\\python.exe"`
- **Tools not appearing**: Check Claude Desktop logs, verify server is starting

