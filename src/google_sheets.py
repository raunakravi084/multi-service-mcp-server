from googleapiclient.discovery import build
from src.google_auth import get_credentials

def get_sheets_service():
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)

def read_sheet_data(spreadsheet_id, range_name):
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        return {
            'success': True,
            'data': values,
            'range': result.get('range', range_name)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def write_sheet_data(spreadsheet_id, range_name, values):
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        
        return {
            'success': True,
            'updatedCells': result.get('updatedCells', 0),
            'updatedRange': result.get('updatedRange', range_name)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def append_sheet_data(spreadsheet_id, range_name, values):
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        
        updates = result.get('updates', {})
        return {
            'success': True,
            'updatedCells': updates.get('updatedCells', 0),
            'updatedRange': updates.get('updatedRange', range_name)
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

def get_sheet_info(spreadsheet_id):
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.get(spreadsheetId=spreadsheet_id).execute()
        
        properties = result.get('properties', {})
        sheets_info = []
        
        for sheet_info in result.get('sheets', []):
            sheet_props = sheet_info.get('properties', {})
            grid_props = sheet_props.get('gridProperties', {})
            sheets_info.append({
                'title': sheet_props.get('title', ''),
                'sheetId': sheet_props.get('sheetId', ''),
                'rowCount': grid_props.get('rowCount', 0),
                'columnCount': grid_props.get('columnCount', 0)
            })
        
        return {
            'success': True,
            'title': properties.get('title', ''),
            'sheets': sheets_info
        }
    except Exception as error:
        return {
            'success': False,
            'error': str(error)
        }

