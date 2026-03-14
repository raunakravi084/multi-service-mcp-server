from googleapiclient.discovery import build
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText
from src.google_auth import get_credentials

def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def list_emails(max_results=10, query=''):
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        message_details = []
        
        for message in messages:
            detail = get_email_detail(message['id'])
            if detail['success']:
                message_details.append(detail['data'])
        
        return {
            'success': True,
            'messages': message_details,
            'total': results.get('resultSizeEstimate', 0)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def get_email_detail(message_id):
    try:
        service = get_gmail_service()
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        
        def get_header(name):
            for header in headers:
                if header['name'].lower() == name.lower():
                    return header['value']
            return ''
        
        data = {
            'id': message['id'],
            'threadId': message.get('threadId', ''),
            'subject': get_header('subject'),
            'from': get_header('from'),
            'to': get_header('to'),
            'date': get_header('date'),
            'snippet': message.get('snippet', ''),
            'body': extract_body(message.get('payload', {}))
        }
        
        return {
            'success': True,
            'data': data
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def extract_body(payload):
    if not payload:
        return ''
    
    body_data = payload.get('body', {}).get('data')
    if body_data:
        return urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            body_data = part.get('body', {}).get('data')
            if body_data:
                return urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        elif part.get('mimeType') == 'text/html':
            body_data = part.get('body', {}).get('data')
            if body_data:
                return urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    
    return ''

def send_email(to, subject, body, is_html=False):
    try:
        service = get_gmail_service()
        
        message = MIMEText(body, 'html' if is_html else 'plain')
        message['to'] = to
        message['subject'] = subject
        
        raw_message = urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            'success': True,
            'messageId': send_message.get('id', ''),
            'threadId': send_message.get('threadId', '')
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def search_emails(query):
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        return {
            'success': True,
            'messageIds': [msg['id'] for msg in messages],
            'total': results.get('resultSizeEstimate', 0)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

