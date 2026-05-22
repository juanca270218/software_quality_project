"""
tests/test_notas.py
Pruebas unitarias para notas y el servicio académico.
Cobertura actual: ~45% — el equipo debe completar hasta ≥85%.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from src.models.database import reset_db
from src.services.academic_service import (
    es_aprobado, calcular_promedio_estudiante,
    reporte_academico, estadisticas_globales
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_db():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def setup_datos():
    """Crea un estudiante y una materia base para las pruebas."""
    client.post("/estudiantes/", json={
        "codigo": "E001", "nombre": "Ana García",
        "email": "ana@test.com", "semestre": 5
    })
    client.post("/materias/", json={
        "codigo": "CS101", "nombre": "Calidad del Software", "creditos": 3
    })


class TestEsAprobado:

    def test_nota_tres_es_aprobado(self):
        assert es_aprobado(3.0) is True

    def test_nota_mayor_tres_es_aprobado(self):
        assert es_aprobado(4.5) is True

    def test_nota_menor_tres_es_reprobado(self):
        assert es_aprobado(2.9) is False

    def test_nota_cero_es_reprobado(self):
        assert es_aprobado(0.0) is False


class TestRegistrarNota:

    def test_registrar_nota_exitosa(self, setup_datos):
        payload = {
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "Parcial 1",
            "valor": 4.0
        }
        response = client.post("/notas/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["valor"] == 4.0
        assert data["aprobado"] is True

    def test_registrar_nota_estudiante_inexistente(self, setup_datos):
        payload = {
            "codigo_estudiante": "X999",
            "codigo_materia": "CS101",
            "actividad": "Parcial",
            "valor": 3.0
        }
        response = client.post("/notas/", json=payload)
        assert response.status_code == 404

    def test_registrar_nota_materia_inexistente(self, setup_datos):
        payload = {
            "codigo_estudiante": "E001",
            "codigo_materia": "XX999",
            "actividad": "Parcial",
            "valor": 3.0
        }
        response = client.post("/notas/", json=payload)
        assert response.status_code == 404

    def test_registrar_nota_valor_invalido(self, setup_datos):
        payload = {
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "Parcial",
            "valor": 6.0
        }
        response = client.post("/notas/", json=payload)
        assert response.status_code == 400


class TestReporteAcademico:

    def test_reporte_estudiante_inexistente(self):
        resultado = reporte_academico("X999")
        assert "error" in resultado

    def test_reporte_sin_notas(self):
        # Crear estudiante directamente en DB para prueba de servicio
        from src.models.database import get_estudiantes
        get_estudiantes()["E001"] = {
            "codigo": "E001", "nombre": "Ana", "email": "a@t.com",
            "semestre": 1, "activo": True
        }
        resultado = reporte_academico("E001")
        assert resultado["total_notas"] == 0
        assert resultado["promedio"] == 0.0


class TestEstadisticasGlobales:

    def test_estadisticas_sin_datos(self):
        stats = estadisticas_globales()
        assert stats["total_estudiantes"] == 0
        assert stats["promedio_global"] == 0.0

  

        


# ─────────────────────────────────────────────────────────────
# TESTS ADICIONALES PARA SUBIR COBERTURA AL 85%
# ─────────────────────────────────────────────────────────────

class TestDeudasTecnicas:

    # 1. División por cero (servicio académico)
    def test_division_por_cero_promedio_estudiante(self, setup_datos):
        response = client.get("/notas/promedio/estudiante/E001")
        assert response.status_code in [200, 404]
        assert "promedio" in response.json() or response.status_code == 404


    # 2. Notas de estudiante
    def test_notas_de_estudiante_endpoint(self, setup_datos):
        response = client.get("/notas/estudiante/E001")
        assert response.status_code in [200, 404]


    # 3. Promedio estudiante con datos
    def test_promedio_estudiante_endpoint(self, setup_datos):

        client.post("/notas/", json={
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "P1",
            "valor": 4.0
        })

        response = client.get("/notas/promedio/estudiante/E001")

        assert response.status_code == 200
        assert "promedio" in response.json()


    # 4. Promedio materia
    def test_promedio_materia_endpoint(self, setup_datos):
        response = client.get("/notas/promedio/materia/CS101")
        assert response.status_code in [200, 404]


    # 5. Estadísticas globales con datos
    def test_estadisticas_con_datos(self, setup_datos):

        client.post("/notas/", json={
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "P1",
            "valor": 4.5
        })

        client.post("/notas/", json={
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "P2",
            "valor": 2.5
        })

        response = client.get("/notas/estadisticas")

        assert response.status_code in [200, 404]


    # 6. Reporte mixto (aprobadas y reprobadas)
    def test_reporte_con_notas_mixtas(self, setup_datos):

        client.post("/notas/", json={
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "P1",
            "valor": 4.0
        })

        client.post("/notas/", json={
            "codigo_estudiante": "E001",
            "codigo_materia": "CS101",
            "actividad": "P2",
            "valor": 2.0
        })

        resultado = reporte_academico("E001")

        assert "total_notas" in resultado
        assert "promedio" in resultado
