import unittest
import os
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient

# Asegurar entorno de pruebas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DB = os.path.join(BASE_DIR, "test_api_mantenimiento.db")

# Cambiar la base de datos de ot_manager temporalmente para pruebas de API
os.environ["AMAZONAS_DB_PATH"] = TEST_DB

import ot_manager
# Forzar a usar la base de datos de test
ot_manager.DB_FILE = TEST_DB

from main import app, ot_db

class TestMantenimientoAPI(unittest.TestCase):
    def setUp(self):
        # Asegurar estado limpio
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass
        ot_db._initialize_db()
        self.client = TestClient(app)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

    @patch('main.sheets_service.obtener_datos_red')
    @patch('main.sheets_service.obtener_datos_master')
    def test_flujo_completo_api(self, mock_master, mock_red):
        # Configurar mocks para simular lectura de Google Sheets
        mock_red.side_effect = [
            [], # Primer GET (vacío)
            [{
                "id_elemento": "NOD-TestAPI",
                "nombre": "Nodo de Prueba API",
                "tipo": "Nodo",
                "ubicacion": "Distrito de Chachapoyas"
            }], # Segundo GET (después de agregar)
            [{
                "id_elemento": "NOD-TestAPI",
                "nombre": "Nodo de Prueba API",
                "tipo": "Nodo",
                "ubicacion": "Distrito de Chachapoyas"
            }]
        ]
        
        mock_master.return_value = [{
            "id_ot": "OT-TEST-99",
            "id_elemento": "NOD-TestAPI",
            "prioridad": "Alta",
            "diagnostico_inicial": "Enlace óptico inestable",
            "hora_recepcion": "2026-06-18T10:00:00",
            "estado": "Abierta"
        }]

        # 1. Listar elementos vacíos
        response = self.client.get("/api/elementos")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # 2. Registrar un elemento (escribe a SQLite local)
        elem_data = {
            "id_elemento": "NOD-TestAPI",
            "nombre": "Nodo de Prueba API",
            "tipo": "Nodo",
            "ubicacion": "Distrito de Chachapoyas"
        }
        response = self.client.post("/api/elementos", json=elem_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id_elemento"], "NOD-TestAPI")

        # 3. Crear OT (escribe a SQLite local)
        ot_data = {
            "id_ot": "OT-TEST-99",
            "id_elemento": "NOD-TestAPI",
            "prioridad": "Alta",
            "diagnostico_inicial": "Enlace óptico inestable"
        }
        response = self.client.post("/api/ots", json=ot_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["estado"], "Abierta")

        # 4. Despachar OT
        response = self.client.post("/api/ots/OT-TEST-99/despachar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "Despachada")
        self.assertIsNotNone(response.json()["hora_despacho"])

        # 5. Registrar llegada
        response = self.client.post("/api/ots/OT-TEST-99/llegada")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "En Sitio")
        self.assertIsNotNone(response.json()["hora_llegada"])

        # 6. Cerrar OT
        response = self.client.post("/api/ots/OT-TEST-99/cerrar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "Cerrada")
        self.assertIsNotNone(response.json()["hora_cierre"])

        # 7. Listar OTs (lee de Sheets mockeado)
        response = self.client.get("/api/ots")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id_ot"], "OT-TEST-99")

    def test_elemento_duplicado_api(self):
        elem_data = {
            "id_elemento": "NOD-Dup",
            "nombre": "Nodo Duplicado",
            "tipo": "Nodo"
        }
        response = self.client.post("/api/elementos", json=elem_data)
        self.assertEqual(response.status_code, 201)
        
        # Enviar de nuevo, debe fallar con 400
        response = self.client.post("/api/elementos", json=elem_data)
        self.assertEqual(response.status_code, 400)

    @patch('main.sheets_service.obtener_datos_red')
    def test_red_amazonas_api(self, mock_red):
        mock_red.return_value = [{"col1": "val1"}]
        response = self.client.get("/api/red-amazonas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"col1": "val1"}])

if __name__ == "__main__":
    unittest.main()
