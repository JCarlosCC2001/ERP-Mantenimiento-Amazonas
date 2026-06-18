import os
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional

# Ruta del archivo de credenciales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "tensile-impact-499801-g7-64b8caecbe2c.json")

# Nombre del documento y pestañas
SPREADSHEET_NAME = "ERP-Mantenimiento-Amazonas"
WORKSHEET_NAME = "RED A."
MASTER_SHEET_NAME = "Master"

# (Opcional) Si tienes la URL o ID del spreadsheet, ponla aquí para
# evitar el uso de la Google Drive API y solo usar la Sheets API.
SPREADSHEET_URL: Optional[str] = None


class GoogleSheetsService:
    def __init__(self, credentials_path: str = CREDENTIALS_FILE):
        self.credentials_path = credentials_path

        # Scopes de acceso
        self.scopes_sheets_only = [
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
        self.scopes_with_drive = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

    def _get_client(self, use_drive: bool = False) -> gspread.Client:
        """Autentica y devuelve el cliente de gspread."""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"El archivo de credenciales de Google no se encontró en: {self.credentials_path}"
            )

        scopes = self.scopes_with_drive if use_drive else self.scopes_sheets_only
        creds = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes
        )
        return gspread.authorize(creds)

    def _classify_api_error(self, raw_message: str) -> str:
        """Devuelve un mensaje de error descriptivo y accionable para el usuario."""
        msg = raw_message.lower()

        if "drive.googleapis.com" in msg or "drive api" in msg:
            return (
                "DRIVE_API_DISABLED|"
                "La Google Drive API no está habilitada en tu proyecto de Google Cloud. "
                "Habilítala en la consola de GCP o proporciona la URL directa de la hoja de cálculo para evitar este requisito."
            )
        if "sheets.googleapis.com" in msg or "sheets api" in msg:
            return (
                "SHEETS_API_DISABLED|"
                "La Google Sheets API no está habilitada en tu proyecto de Google Cloud. "
                "Habilítala en la consola de GCP."
            )
        if "permission_denied" in msg or "forbidden" in msg or "403" in msg:
            return (
                "PERMISSION_DENIED|"
                "Permiso denegado. Asegúrate de que la cuenta de servicio tenga acceso al documento de Google Sheets."
            )
        if "not_found" in msg or "404" in msg:
            return (
                "NOT_FOUND|"
                f"No se encontró el documento. Verifica que el nombre sea exactamente '{SPREADSHEET_NAME}' y que esté compartido."
            )
        return f"GENERIC_ERROR|{raw_message}"

    def obtener_datos_red(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de la pestaña 'RED A.'."""
        return self._obtener_datos_hoja(WORKSHEET_NAME)

    def obtener_datos_master(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de la pestaña 'Master' (Órdenes de Trabajo)."""
        return self._obtener_datos_hoja(MASTER_SHEET_NAME)

    def obtener_datos_cfms(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de la pestaña 'CFMs'."""
        return self._obtener_datos_hoja("CFMs")

    def _obtener_datos_hoja(self, name: str) -> List[Dict[str, Any]]:
        """Método unificado para leer una pestaña de Google Sheets."""
        try:
            if SPREADSHEET_URL:
                # Usa solo Sheets API (sin Drive API)
                client = self._get_client(use_drive=False)
                spreadsheet = client.open_by_url(SPREADSHEET_URL)
            else:
                # Abre por nombre, requiere Drive API
                client = self._get_client(use_drive=True)
                spreadsheet = client.open(SPREADSHEET_NAME)

            worksheet = spreadsheet.worksheet(name)
            values = worksheet.get_all_values()
            if not values:
                return []
            
            # Procesar cabeceras y renombrar duplicados
            headers = [h.strip() for h in values[0]]
            seen = {}
            unique_headers = []
            for h in headers:
                if not h:
                    h = "COL_VACIA"
                if h in seen:
                    seen[h] += 1
                    unique_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    unique_headers.append(h)
            
            # Mapear filas a diccionarios
            records = []
            for row in values[1:]:
                # Asegurar longitud correcta
                if len(row) < len(unique_headers):
                    row = row + [""] * (len(unique_headers) - len(row))
                
                record = {}
                for h, val in zip(unique_headers, row):
                    record[h] = val
                records.append(record)
            
            return records

        except gspread.exceptions.SpreadsheetNotFound:
            raise ValueError(
                f"NOT_FOUND|No se encontró el documento '{SPREADSHEET_NAME}'. "
                "Asegúrate de que el archivo exista y esté compartido con la cuenta de servicio."
            )
        except gspread.exceptions.WorksheetNotFound:
            raise ValueError(
                f"WORKSHEET_NOT_FOUND|No se encontró la pestaña '{name}' "
                f"en el documento '{SPREADSHEET_NAME}'. Verifica el nombre exacto."
            )
        except gspread.exceptions.APIError as e:
            try:
                raw_msg = e.response.json().get('error', {}).get('message', str(e))
            except Exception:
                raw_msg = str(e)
            raise ValueError(self._classify_api_error(raw_msg))
        except FileNotFoundError as e:
            raise ValueError(f"CREDENTIALS_NOT_FOUND|{str(e)}")
        except Exception as e:
            raise ValueError(f"GENERIC_ERROR|Error inesperado al conectar con Google Sheets: {str(e)}")


# Instancia singleton
sheets_service = GoogleSheetsService()
