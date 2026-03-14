#!/usr/bin/env python3
import os
import json
from src.google_auth import get_credentials, get_auth_url, get_token_from_code, is_authorized, CREDENTIALS_PATH

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {'google': {}}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def setup():
    print('Google Services MCP Setup')
    print('=' * 25 + '\n')
    
    print('Step 1: Create credentials.json')
    if not os.path.exists(CREDENTIALS_PATH):
        print('Go to: https://console.cloud.google.com/apis/credentials')
        print('Create OAuth 2.0 Client ID credentials')
        print('Download and save as credentials.json in the project root\n')
        
        input('Press Enter when credentials.json is ready... ')
        
        if not os.path.exists(CREDENTIALS_PATH):
            print('credentials.json not found. Please create it first.')
            return
    
    print('Step 2: Authorization')
    if is_authorized():
        print('Already authorized. Tokens found.')
        reauth = input('Re-authorize? (y/n): ')
        if reauth.lower() != 'y':
            print('Using existing authorization.')
            return
    
    try:
        auth_url = get_auth_url()
        print('\nOpen this URL in your browser:')
        print(auth_url)
        print('\nAfter authorization, you will be redirected to a page.')
        print('Copy the full URL from your browser address bar.')
        
        redirect_url = input('\nPaste the full redirect URL here: ')
        
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        code = query_params.get('code', [None])[0]
        
        if not code:
            print('No authorization code found in URL.')
            return
        
        get_token_from_code(code)
        print('\nAuthorization successful! Tokens saved.')
    
    except Exception as error:
        print(f'\nError during authorization: {str(error)}')
        print('You can also run the agent, and it will open a browser for authorization.')
        return
    
    print('\nStep 3: Configuration')
    config = load_config()
    
    if 'google' not in config:
        config['google'] = {}
    
    spreadsheet_id = input('Enter your Google Spreadsheet ID (optional, press Enter to skip): ')
    if spreadsheet_id:
        config['google']['spreadsheetId'] = spreadsheet_id
    
    calendar_id = input('Enter Calendar ID (default: primary, press Enter for default): ')
    config['google']['calendarId'] = calendar_id or 'primary'
    
    save_config(config)
    print('\nConfiguration saved successfully!')
    
    print('\nSetup complete!')
    print('You can now run: python src/agent.py')

if __name__ == '__main__':
    setup()

