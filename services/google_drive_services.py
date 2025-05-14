"""
google_drive_service.py

Serviço para interação com a API do Google Drive, incluindo busca de pastas e leitura de planilhas.
"""
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']


def get_services_service_account(json_path='service-account.json'):
    """
    Autentica usando conta de serviço e retorna os serviços do Drive e Sheets.
    """
    creds = service_account.Credentials.from_service_account_file(
        json_path, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return drive_service, sheets_service

def get_services(api_key):
    """
    Inicializa serviços Google Drive e Sheets usando API Key.
    """
    drive_service = build('drive', 'v3', developerKey=api_key)
    sheets_service = build('sheets', 'v4', developerKey=api_key)
    return drive_service, sheets_service

def find_folder_id(drive_service, folder_name: str) -> str:
    """
    Retorna o ID da pasta pelo nome.
    """
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resp = drive_service.files().list(q=query, spaces='drive', fields='files(id,name)', pageSize=1).execute()
    files = resp.get('files', [])
    if not files:
        raise FileNotFoundError(f"Pasta '{folder_name}' não encontrada.")
    return files[0]['id']

def list_spreadsheets_in_folder(drive_service, folder_id: str) -> list:
    """
    Lista planilhas dentro da pasta.
    """
    query = (
        f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet' "
        "and trashed = false"
    )
    resp = drive_service.files().list(q=query, spaces='drive', fields='files(id,name)', pageSize=100).execute()
    return resp.get('files', [])

def read_sheet(sheets_service, spreadsheet_id: str, range_name: str = 'A:Z') -> list:
    """
    Lê valores de uma planilha (faixa A:Z por padrão).
    """
    result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])

def create_spreadsheet(sheets_service, drive_service, title, rows, parent_folder_id):
    """
    Cria uma nova planilha no Google Drive e insere as linhas fornecidas.
    """
    spreadsheet = {
        'properties': {'title': title}
    }
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet['spreadsheetId']
    
    if rows:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1',
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
    
    file = drive_service.files().get(fileId=spreadsheet_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))
    
    drive_service.files().update(
        fileId=spreadsheet_id,
        addParents=parent_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return spreadsheet_id

def get_folder_id_by_name(drive_service, folder_name: str) -> str:
    """
    Busca o ID de uma pasta pelo nome.
    """
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resp = drive_service.files().list(q=query, spaces='drive', fields='files(id,name)', pageSize=1).execute()
    files = resp.get('files', [])
    if not files:
        raise FileNotFoundError(f"Pasta '{folder_name}' não encontrada.")
    return files[0]['id'] 