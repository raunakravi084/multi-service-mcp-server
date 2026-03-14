#!/usr/bin/env python3
import asyncio
import json
import re
from datetime import datetime, timedelta
from src.mcp_client import create_mcp_client, list_tools, call_tool

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {'google': {}}

def analyze_emails_for_actions(emails):
    actions = []
    
    if not emails or not emails.get('messages') or len(emails['messages']) == 0:
        return actions
    
    for email in emails['messages']:
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        
        if 'meeting' in subject or 'schedule' in subject or 'meeting' in body:
            actions.append({
                'type': 'calendar_check',
                'email': email,
                'reason': 'Email mentions meeting - checking calendar'
            })
        
        if 'task' in subject or 'todo' in subject or 'please add' in body:
            actions.append({
                'type': 'sheet_add',
                'email': email,
                'reason': 'Email mentions task - adding to sheet'
            })
        
        email_from = email.get('from', '').lower()
        if 'urgent' in email_from or 'urgent' in subject:
            actions.append({
                'type': 'priority',
                'email': email,
                'reason': 'Urgent email detected'
            })
    
    return actions

def extract_meeting_info(email):
    subject = email.get('subject', '')
    body = email.get('body', '')
    
    time_pattern = r'(\d{1,2}):(\d{2})\s*(am|pm)'
    date_pattern = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)'
    
    time_matches = re.findall(time_pattern, body, re.IGNORECASE)
    date_matches = re.findall(date_pattern, body, re.IGNORECASE)
    
    return {
        'hasTime': len(time_matches) > 0,
        'hasDate': len(date_matches) > 0,
        'subject': subject
    }

def generate_event_from_email(email, spreadsheet_id):
    meeting_info = extract_meeting_info(email)
    
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    end_time = tomorrow + timedelta(hours=1)
    
    from_email = email.get('from', '')
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_email)
    attendee_email = email_match.group(0) if email_match else None
    
    return {
        'summary': email.get('subject', 'Meeting from Email'),
        'description': f"Meeting requested via email from {from_email}\n\n{email.get('body', '')[:200]}",
        'start': tomorrow.isoformat(),
        'end': end_time.isoformat(),
        'location': '',
        'attendees': [attendee_email] if attendee_email else []
    }

def generate_task_from_email(email):
    return {
        'task': email.get('subject', 'Task from Email'),
        'source': email.get('from', 'Unknown'),
        'date': datetime.now().isoformat(),
        'status': 'Pending',
        'description': email.get('body', '')[:200] if email.get('body') else ''
    }

async def process_decision(session, decision, config):
    try:
        if decision['type'] == 'calendar_check':
            print('Checking calendar for upcoming events...')
            events = await call_tool(session, 'list_calendar_events', {
                'maxResults': 5
            })
            
            if events.get('success') and events.get('events'):
                print(f"Found {len(events['events'])} upcoming events")
                if len(events['events']) > 0:
                    print('Upcoming events:')
                    for event in events['events']:
                        print(f"  - {event.get('summary', '')} on {event.get('start', '')}")
        
        elif decision['type'] == 'sheet_add':
            print('Adding task to spreadsheet...')
            task = generate_task_from_email(decision['email'])
            values = [[
                task['date'],
                task['task'],
                task['source'],
                task['status'],
                task['description']
            ]]
            
            result = await call_tool(session, 'append_sheet', {
                'spreadsheetId': config.get('google', {}).get('spreadsheetId'),
                'range': 'Sheet1',
                'values': values
            })
            
            if result.get('success'):
                print('Task added to spreadsheet successfully')
            else:
                print(f"Failed to add task: {result.get('error', 'Unknown error')}")
        
        elif decision['type'] == 'calendar_create':
            print('Creating calendar event...')
            event_data = generate_event_from_email(decision['email'], config.get('google', {}).get('spreadsheetId'))
            result = await call_tool(session, 'create_calendar_event', event_data)
            
            if result.get('success'):
                print(f"Event created: {result.get('eventId', '')}")
                print(f"Event link: {result.get('htmlLink', 'N/A')}")
            else:
                print(f"Failed to create event: {result.get('error', 'Unknown error')}")
        
        elif decision['type'] == 'email_response':
            print('Sending email response...')
            result = await call_tool(session, 'send_email', {
                'to': decision['email'].get('from', ''),
                'subject': f"Re: {decision['email'].get('subject', '')}",
                'body': decision.get('response', 'Thank you for your email. I have processed your request.')
            })
            
            if result.get('success'):
                print('Email sent successfully')
            else:
                print(f"Failed to send email: {result.get('error', 'Unknown error')}")
        
        elif decision['type'] == 'priority':
            print('Urgent email detected - taking priority action')
            task = generate_task_from_email(decision['email'])
            task['status'] = 'Urgent'
            
            sheet_result = await call_tool(session, 'append_sheet', {
                'spreadsheetId': config.get('google', {}).get('spreadsheetId'),
                'range': 'Sheet1',
                'values': [[
                    task['date'],
                    task['task'],
                    task['source'],
                    task['status'],
                    task['description']
                ]]
            })
            
            if sheet_result.get('success'):
                print('Urgent task added to spreadsheet')
    
    except Exception as error:
        print(f"Error processing decision {decision.get('type', 'unknown')}: {str(error)}")

async def make_automatic_decisions(session, config):
    print('Starting automatic decision-making process...\n')
    
    print('Step 1: Checking emails...')
    emails = await call_tool(session, 'list_emails', {
        'maxResults': 10,
        'query': 'in:inbox'
    })
    
    if not emails.get('success'):
        print(f"Failed to fetch emails: {emails.get('error', 'Unknown error')}")
        return
    
    print(f"Found {len(emails.get('messages', []))} emails\n")
    
    print('Step 2: Analyzing emails for actions...')
    actions = analyze_emails_for_actions(emails)
    print(f"Identified {len(actions)} potential actions\n")
    
    if len(actions) == 0:
        print('No actions required based on email analysis')
        return
    
    print('Step 3: Processing decisions...\n')
    for action in actions:
        print(f"Processing: {action['reason']}")
        
        if action['type'] == 'calendar_check':
            meeting_info = extract_meeting_info(action['email'])
            if meeting_info['hasTime'] or meeting_info['hasDate']:
                action['type'] = 'calendar_create'
                action['reason'] = 'Email contains meeting info - creating calendar event'
        
        if action['type'] == 'sheet_add' and action['email'].get('from'):
            action['response'] = f"I have added your request \"{action['email'].get('subject', '')}\" to my task list."
            await process_decision(session, action, config)
            
            response_action = {
                'type': 'email_response',
                'email': action['email'],
                'response': action['response']
            }
            await process_decision(session, response_action, config)
        else:
            await process_decision(session, action, config)
        
        print('')
    
    print('Step 4: Checking calendar status...')
    events = await call_tool(session, 'list_calendar_events', {
        'maxResults': 5
    })
    
    if events.get('success'):
        print(f"Calendar has {len(events.get('events', []))} upcoming events")
    
    print('\nAutomatic decision-making process completed')

async def main():
    try:
        print('Initializing MCP Client...')
        session = await create_mcp_client()
        
        print('Fetching available tools...')
        tools = await list_tools(session)
        print(f"Connected. Available tools: {len(tools)}\n")
        
        config = load_config()
        
        await make_automatic_decisions(session, config)
        
        print('\nAgent session ended')
    
    except Exception as error:
        print(f'Agent error: {str(error)}')
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    asyncio.run(main())

