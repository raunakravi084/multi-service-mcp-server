from googleapiclient.discovery import build
from datetime import datetime, timedelta
from src.google_auth import get_credentials

def get_calendar_service():
    creds = get_credentials()
    return build('calendar', 'v3', credentials=creds)

def list_events(calendar_id='primary', max_results=10, time_min=None):
    try:
        service = get_calendar_service()
        
        if time_min is None:
            time_min = datetime.utcnow().isoformat() + 'Z'
        else:
            time_min = datetime.fromisoformat(time_min.replace('Z', '+00:00')).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event.get('id', ''),
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date', ''),
                'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date', ''),
                'location': event.get('location', ''),
                'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                'status': event.get('status', '')
            })
        
        return {
            'success': True,
            'events': formatted_events,
            'total': len(formatted_events)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def create_event(calendar_id='primary', event_data=None):
    try:
        if event_data is None:
            event_data = {}
        
        service = get_calendar_service()
        
        event = {
            'summary': event_data.get('summary', ''),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data.get('start', datetime.utcnow().isoformat() + 'Z'),
                'timeZone': event_data.get('timeZone', 'America/Los_Angeles')
            },
            'end': {
                'dateTime': event_data.get('end', (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'),
                'timeZone': event_data.get('timeZone', 'America/Los_Angeles')
            }
        }
        
        if event_data.get('location'):
            event['location'] = event_data['location']
        
        if event_data.get('attendees'):
            event['attendees'] = [{'email': email} for email in event_data['attendees']]
        
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        return {
            'success': True,
            'eventId': created_event.get('id', ''),
            'htmlLink': created_event.get('htmlLink', ''),
            'event': {
                'id': created_event.get('id', ''),
                'summary': created_event.get('summary', ''),
                'start': created_event.get('start', {}).get('dateTime') or created_event.get('start', {}).get('date', ''),
                'end': created_event.get('end', {}).get('dateTime') or created_event.get('end', {}).get('date', '')
            }
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def update_event(calendar_id='primary', event_id=None, event_data=None):
    try:
        if event_data is None:
            event_data = {}
        if event_id is None:
            raise ValueError('event_id is required')
        
        service = get_calendar_service()
        
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        if event_data.get('summary'):
            event['summary'] = event_data['summary']
        if event_data.get('description'):
            event['description'] = event_data['description']
        if event_data.get('start'):
            event['start'] = {
                'dateTime': event_data['start'],
                'timeZone': event_data.get('timeZone', 'America/Los_Angeles')
            }
        if event_data.get('end'):
            event['end'] = {
                'dateTime': event_data['end'],
                'timeZone': event_data.get('timeZone', 'America/Los_Angeles')
            }
        if event_data.get('location'):
            event['location'] = event_data['location']
        if event_data.get('attendees'):
            event['attendees'] = [{'email': email} for email in event_data['attendees']]
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        return {
            'success': True,
            'eventId': updated_event.get('id', ''),
            'htmlLink': updated_event.get('htmlLink', '')
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def delete_event(calendar_id='primary', event_id=None):
    try:
        if event_id is None:
            raise ValueError('event_id is required')
        
        service = get_calendar_service()
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        return {
            'success': True,
            'message': 'Event deleted successfully'
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def get_event(calendar_id='primary', event_id=None):
    try:
        if event_id is None:
            raise ValueError('event_id is required')
        
        service = get_calendar_service()
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        return {
            'success': True,
            'event': {
                'id': event.get('id', ''),
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date', ''),
                'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date', ''),
                'location': event.get('location', ''),
                'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                'status': event.get('status', '')
            }
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

