import unittest
import os
from datetime import datetime, timedelta
from ot_manager import OTManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DB = os.path.join(BASE_DIR, "test_mantenimiento_amazonas.db")

class TestOTManager(unittest.TestCase):
    def setUp(self):
        # Asegurar un estado limpio de la base de datos de pruebas
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.manager = OTManager(db_path=TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_registrar_y_obtener_elemento(self):
        # Registrar elemento válido
        res = self.manager.registrar_elemento("NOD-001", "Nodo Chachapoyas", "Nodo", "Chachapoyas Centro")
        self.assertTrue(res)
        
        # Obtener y validar datos
        el = self.manager.obtener_elemento("NOD-001")
        self.assertIsNotNone(el)
        self.assertEqual(el["nombre"], "Nodo Chachapoyas")
        self.assertEqual(el["tipo"], "Nodo")
        self.assertEqual(el["ubicacion"], "Chachapoyas Centro")

    def test_registrar_elemento_tipo_invalido(self):
        with self.assertRaises(ValueError):
            self.manager.registrar_elemento("IAO-001", "Colegio 123", "OtroTipo", "Ubicacion")

    def test_registrar_elemento_duplicado(self):
        self.manager.registrar_elemento("NOD-001", "Nodo Chachapoyas", "Nodo")
        with self.assertRaises(ValueError):
            self.manager.registrar_elemento("NOD-001", "Otro Nombre", "Nodo")

    def test_listar_elementos(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        self.manager.registrar_elemento("IAO-002", "Colegio B", "IAO")
        elementos = self.manager.listar_elementos()
        self.assertEqual(len(elementos), 2)

    def test_crear_ot_valida(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        hora_recepcion = datetime(2026, 6, 14, 10, 0, 0)
        res = self.manager.crear_ot(
            id_ot="OT-2026-0001",
            id_elemento="NOD-001",
            prioridad="Alta",
            diagnostico_inicial="Enlace Caído",
            hora_recepcion=hora_recepcion
        )
        self.assertTrue(res)
        
        ot = self.manager.obtener_ot("OT-2026-0001")
        self.assertIsNotNone(ot)
        self.assertEqual(ot["estado"], "Abierta")
        self.assertEqual(ot["prioridad"], "Alta")
        self.assertEqual(ot["hora_recepcion"], hora_recepcion)

    def test_crear_ot_elemento_inexistente(self):
        with self.assertRaises(ValueError):
            self.manager.crear_ot("OT-0001", "NOD-INEXISTENTE", "Media", "Falla")

    def test_crear_ot_prioridad_invalida(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        with self.assertRaises(ValueError):
            self.manager.crear_ot("OT-0001", "NOD-001", "Muy Alta", "Falla")

    def test_flujo_estados_completo(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        t_recepcion = datetime(2026, 6, 14, 8, 0, 0)
        t_despacho = t_recepcion + timedelta(minutes=30)
        t_llegada = t_despacho + timedelta(hours=1)
        t_cierre = t_llegada + timedelta(hours=2)

        # 1. Crear OT (Abierta)
        self.manager.crear_ot("OT-1", "NOD-001", "Media", "Falla Fuente", t_recepcion)
        ot = self.manager.obtener_ot("OT-1")
        self.assertEqual(ot["estado"], "Abierta")

        # 2. Despachar Cuadrilla (Despachada)
        self.manager.despachar_cuadrilla("OT-1", t_despacho)
        ot = self.manager.obtener_ot("OT-1")
        self.assertEqual(ot["estado"], "Despachada")
        self.assertEqual(ot["hora_despacho"], t_despacho)

        # 3. Registrar Llegada (En Sitio)
        self.manager.registrar_llegada_sitio("OT-1", t_llegada)
        ot = self.manager.obtener_ot("OT-1")
        self.assertEqual(ot["estado"], "En Sitio")
        self.assertEqual(ot["hora_llegada"], t_llegada)

        # 4. Cerrar OT (Cerrada)
        self.manager.cerrar_ot("OT-1", t_cierre)
        ot = self.manager.obtener_ot("OT-1")
        self.assertEqual(ot["estado"], "Cerrada")
        self.assertEqual(ot["hora_cierre"], t_cierre)

    def test_transiciones_invalidas(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        t_recepcion = datetime(2026, 6, 14, 8, 0, 0)
        self.manager.crear_ot("OT-1", "NOD-001", "Media", "Falla", t_recepcion)

        # Tratar de llegar a sitio sin despachar
        with self.assertRaises(ValueError):
            self.manager.registrar_llegada_sitio("OT-1")

        # Tratar de cerrar sin llegar a sitio
        with self.assertRaises(ValueError):
            self.manager.cerrar_ot("OT-1")

        # Despachar con fecha anterior a recepción
        with self.assertRaises(ValueError):
            self.manager.despachar_cuadrilla("OT-1", t_recepcion - timedelta(minutes=1))

    def test_eliminar_elemento_con_ot(self):
        self.manager.registrar_elemento("NOD-001", "Nodo A", "Nodo")
        self.manager.crear_ot("OT-1", "NOD-001", "Media", "Falla")
        
        # Debe fallar la eliminación por restricción de FK
        with self.assertRaises(ValueError):
            self.manager.eliminar_elemento("NOD-001")

if __name__ == "__main__":
    unittest.main()
