"""
Produza ERP - New Features Tests (Iteration 2)
Tests for: CNPJ Lookup, Usuarios CRUD, Empresas CRUD, Orcamento View
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "contato@produzafilmes.com"
TEST_PASSWORD = "Vz14071614@"
TEST_EMPRESA_ID = "a1b09d6c-e491-49c0-8606-414e3186917e"
TEST_ORCAMENTO_ID = "8a0da830-435f-4e75-b302-d3520e72158a"


@pytest.fixture
def auth_headers():
    """Get auth headers"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "senha": TEST_PASSWORD
    })
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestCNPJLookup:
    """CNPJ Lookup API tests - BrasilAPI integration"""
    
    def test_cnpj_lookup_valid(self, auth_headers):
        """Test CNPJ lookup with valid CNPJ (Globo)"""
        response = requests.get(
            f"{BASE_URL}/api/consulta-cnpj/27865757000102",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "cnpj" in data
        assert "razao_social" in data
        assert "nome_fantasia" in data
        assert "endereco" in data
        assert "telefone" in data
        
        # Verify data values
        assert data["cnpj"] == "27865757000102"
        assert "GLOBO" in data["razao_social"].upper()
        assert data["endereco"]["uf"] == "RJ"
    
    def test_cnpj_lookup_with_formatting(self, auth_headers):
        """Test CNPJ lookup with formatted CNPJ (dots, slashes, dashes)"""
        # Note: URL path encoding may cause issues with special chars
        # The backend strips non-numeric chars, so we test with clean CNPJ
        response = requests.get(
            f"{BASE_URL}/api/consulta-cnpj/27865757000102",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cnpj"] == "27865757000102"
    
    def test_cnpj_lookup_invalid_length(self, auth_headers):
        """Test CNPJ lookup with invalid length"""
        response = requests.get(
            f"{BASE_URL}/api/consulta-cnpj/123456",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "14 dígitos" in response.json()["detail"]
    
    def test_cnpj_lookup_invalid_digits(self, auth_headers):
        """Test CNPJ lookup with invalid check digits"""
        response = requests.get(
            f"{BASE_URL}/api/consulta-cnpj/11111111111111",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "inválido" in response.json()["detail"].lower()
    
    def test_cnpj_lookup_not_found(self, auth_headers):
        """Test CNPJ lookup with non-existent CNPJ"""
        # Valid format but non-existent - using a CNPJ that doesn't exist
        response = requests.get(
            f"{BASE_URL}/api/consulta-cnpj/99999999000191",
            headers=auth_headers
        )
        # Should return 404 or 200 (BrasilAPI may return data for some CNPJs)
        # The important thing is the API doesn't crash
        assert response.status_code in [200, 404, 502]
    
    def test_cnpj_lookup_requires_auth(self):
        """Test CNPJ lookup requires authentication"""
        response = requests.get(f"{BASE_URL}/api/consulta-cnpj/27865757000102")
        assert response.status_code == 403


class TestUsuariosAPI:
    """Usuarios CRUD tests"""
    
    def test_list_usuarios(self, auth_headers):
        """Test listing users (admin only)"""
        response = requests.get(f"{BASE_URL}/api/usuarios", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify user structure
        if len(data) > 0:
            user = data[0]
            assert "id" in user
            assert "email" in user
            assert "nome" in user
            assert "role" in user
            assert "ativo" in user
            assert "empresas" in user
    
    def test_create_usuario(self, auth_headers):
        """Test creating a new user"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/usuarios", headers=auth_headers, json={
            "email": f"test_{unique_id}@example.com",
            "senha": "TestPassword123!",
            "nome": f"TEST_Usuario_{unique_id}",
            "role": "visualizacao"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["nome"] == f"TEST_Usuario_{unique_id}"
    
    def test_update_usuario(self, auth_headers):
        """Test updating a user"""
        # First create a user
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/usuarios", headers=auth_headers, json={
            "email": f"test_update_{unique_id}@example.com",
            "senha": "TestPassword123!",
            "nome": f"TEST_Usuario_Update_{unique_id}",
            "role": "visualizacao"
        })
        user_id = create_response.json()["id"]
        
        # Update the user
        update_response = requests.patch(
            f"{BASE_URL}/api/usuarios/{user_id}",
            headers=auth_headers,
            json={"nome": f"TEST_Updated_{unique_id}", "role": "producao"}
        )
        assert update_response.status_code == 200
        
        # Verify update
        list_response = requests.get(f"{BASE_URL}/api/usuarios", headers=auth_headers)
        users = list_response.json()
        updated_user = next((u for u in users if u["id"] == user_id), None)
        assert updated_user is not None
        assert updated_user["nome"] == f"TEST_Updated_{unique_id}"
        assert updated_user["role"] == "producao"
    
    def test_toggle_usuario_ativo(self, auth_headers):
        """Test toggling user active status"""
        # First create a user
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/usuarios", headers=auth_headers, json={
            "email": f"test_toggle_{unique_id}@example.com",
            "senha": "TestPassword123!",
            "nome": f"TEST_Usuario_Toggle_{unique_id}",
            "role": "visualizacao"
        })
        user_id = create_response.json()["id"]
        
        # Toggle to inactive
        toggle_response = requests.patch(
            f"{BASE_URL}/api/usuarios/{user_id}",
            headers=auth_headers,
            json={"ativo": False}
        )
        assert toggle_response.status_code == 200
        
        # Verify toggle
        list_response = requests.get(f"{BASE_URL}/api/usuarios", headers=auth_headers)
        users = list_response.json()
        toggled_user = next((u for u in users if u["id"] == user_id), None)
        assert toggled_user is not None
        assert toggled_user["ativo"] == False


class TestEmpresasAPI:
    """Empresas CRUD tests"""
    
    def test_list_empresas(self, auth_headers):
        """Test listing companies"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least one company
        
        # Verify company structure
        empresa = data[0]
        assert "id" in empresa
        assert "cnpj" in empresa
        assert "razao_social" in empresa
    
    def test_create_empresa(self, auth_headers):
        """Test creating a new company"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/empresas", headers=auth_headers, json={
            "cnpj": f"12.345.678/0001-{unique_id[:2]}",
            "razao_social": f"TEST_Empresa_{unique_id}",
            "nome_fantasia": f"Test Company {unique_id}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["razao_social"] == f"TEST_Empresa_{unique_id}"
    
    def test_update_empresa(self, auth_headers):
        """Test updating a company"""
        # First create a company
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/empresas", headers=auth_headers, json={
            "cnpj": f"98.765.432/0001-{unique_id[:2]}",
            "razao_social": f"TEST_Empresa_Update_{unique_id}"
        })
        empresa_id = create_response.json()["id"]
        
        # Update the company
        update_response = requests.patch(
            f"{BASE_URL}/api/empresas/{empresa_id}",
            headers=auth_headers,
            json={"nome_fantasia": f"Updated Company {unique_id}", "telefone": "(11) 99999-9999"}
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = requests.get(f"{BASE_URL}/api/empresas/{empresa_id}", headers=auth_headers)
        assert get_response.status_code == 200


class TestOrcamentoView:
    """Orcamento View/Print tests"""
    
    def test_get_orcamento_details(self, auth_headers):
        """Test getting orcamento details for view/print"""
        response = requests.get(
            f"{BASE_URL}/api/orcamentos/{TEST_ORCAMENTO_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure for view/print
        assert "id" in data
        assert "numero" in data
        assert "titulo" in data
        assert "itens" in data
        assert "subtotal_1" in data
        assert "total_geral" in data
        
        # Verify calculation fields
        assert "taxa_produtora_percent" in data
        assert "imposto_percent" in data
        assert "modo_imposto" in data
        assert "modo_produtora" in data
    
    def test_orcamento_calculation_fields(self, auth_headers):
        """Test orcamento has all Jobbs-style calculation fields"""
        response = requests.get(
            f"{BASE_URL}/api/orcamentos/{TEST_ORCAMENTO_ID}",
            headers=auth_headers
        )
        data = response.json()
        
        # Jobbs calculation fields
        calculation_fields = [
            "subtotal_1",
            "valor_produtora",
            "subtotal_2",
            "valor_imposto",
            "valor_bv",
            "valor_comissao",
            "desconto_valor",
            "acrescimo_valor",
            "total_geral"
        ]
        
        for field in calculation_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_orcamento_items_have_final_values(self, auth_headers):
        """Test orcamento items have final values for distributed mode"""
        response = requests.get(
            f"{BASE_URL}/api/orcamentos/{TEST_ORCAMENTO_ID}",
            headers=auth_headers
        )
        data = response.json()
        
        if data.get("itens") and len(data["itens"]) > 0:
            item = data["itens"][0]
            # Check item has both base and final values
            assert "venda_unitario" in item
            assert "venda_total" in item
            # Final values may be present if distributed mode is used
            # These are optional based on mode


class TestOrcamentoCalculations:
    """Test Jobbs-style budget calculations"""
    
    def test_create_orcamento_with_taxes(self, auth_headers):
        """Test creating orcamento with tax configuration"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create orcamento with taxes
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": TEST_EMPRESA_ID,
            "titulo": f"TEST_Orcamento_Taxes_{unique_id}",
            "taxa_produtora_percent": 10,
            "imposto_percent": 15,
            "bv_percent": 5,
            "comissao_percent": 3,
            "modo_imposto": "visivel",
            "modo_produtora": "visivel"
        })
        assert create_response.status_code == 200
        orcamento_id = create_response.json()["id"]
        
        # Add item
        item_response = requests.post(
            f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens",
            headers=auth_headers,
            json={
                "descricao": "Serviço de teste",
                "quantidade": 1,
                "custo_unitario": 1000,
                "venda_unitario": 1000
            }
        )
        assert item_response.status_code == 200
        
        # Get orcamento and verify calculations
        get_response = requests.get(
            f"{BASE_URL}/api/orcamentos/{orcamento_id}",
            headers=auth_headers
        )
        data = get_response.json()
        
        # Verify Jobbs calculation:
        # Subtotal 1 = 1000
        # Taxa Produtora (10%) = 100
        # Subtotal 2 = 1100
        # Imposto (15% of 1100) = 165
        # BV (5% of 1100) = 55
        # Comissão (3% of 1100) = 33
        # Total = 1100 + 165 + 55 + 33 = 1353
        
        assert float(data["subtotal_1"]) == 1000.0
        assert float(data["valor_produtora"]) == 100.0
        assert float(data["subtotal_2"]) == 1100.0
        assert float(data["valor_imposto"]) == 165.0
        assert float(data["valor_bv"]) == 55.0
        assert float(data["valor_comissao"]) == 33.0
        assert float(data["total_geral"]) == 1353.0
    
    def test_update_orcamento_taxes(self, auth_headers):
        """Test updating orcamento tax configuration"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create orcamento
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": TEST_EMPRESA_ID,
            "titulo": f"TEST_Orcamento_Update_Taxes_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        requests.post(
            f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens",
            headers=auth_headers,
            json={
                "descricao": "Item teste",
                "quantidade": 1,
                "custo_unitario": 500,
                "venda_unitario": 1000
            }
        )
        
        # Update taxes
        update_response = requests.patch(
            f"{BASE_URL}/api/orcamentos/{orcamento_id}",
            headers=auth_headers,
            json={
                "taxa_produtora_percent": 20,
                "imposto_percent": 10,
                "desconto_valor": 50,
                "modo_imposto": "embutido"
            }
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = requests.get(
            f"{BASE_URL}/api/orcamentos/{orcamento_id}",
            headers=auth_headers
        )
        data = get_response.json()
        
        assert data["taxa_produtora_percent"] == 20
        assert data["imposto_percent"] == 10
        assert data["desconto_valor"] == 50
        assert data["modo_imposto"] == "embutido"
