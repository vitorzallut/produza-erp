"""
Produza ERP - Backend API Tests
Tests for: Auth, Orçamentos, Projetos, Clientes, Financeiro
Business Rule: Projects must be created via budget approval
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "contato@produzafilmes.com"
TEST_PASSWORD = "Vz14071614@"


class TestHealth:
    """Health check tests - run first"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "Produza ERP API" in data["message"]


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "usuario" in data
        assert data["usuario"]["email"] == TEST_EMAIL
        assert data["usuario"]["role"] == "admin"
        assert "empresas" in data["usuario"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "senha": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_protected_route_without_token(self):
        """Test accessing protected route without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 403  # No auth header
    
    def test_protected_route_with_token(self):
        """Test accessing protected route with valid token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Access protected route
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL


class TestEmpresas:
    """Company tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_empresas(self, auth_headers):
        """Test listing companies"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one company (Produza Soluções)
        assert len(data) >= 1


class TestClientes:
    """Client/CRM tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def empresa_id(self, auth_headers):
        """Get first empresa ID"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresas = response.json()
        return empresas[0]["id"]
    
    def test_list_clientes(self, auth_headers, empresa_id):
        """Test listing clients filtered by company"""
        response = requests.get(f"{BASE_URL}/api/clientes?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_cliente(self, auth_headers, empresa_id):
        """Test creating a new client"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/clientes", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "nome": f"TEST_Cliente_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "tipo": "PJ"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["nome"] == f"TEST_Cliente_{unique_id}"
        return data["id"]


class TestOrcamentos:
    """Budget tests - Core business logic"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def empresa_id(self, auth_headers):
        """Get first empresa ID"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresas = response.json()
        return empresas[0]["id"]
    
    def test_list_orcamentos(self, auth_headers, empresa_id):
        """Test listing budgets filtered by company"""
        response = requests.get(f"{BASE_URL}/api/orcamentos?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_orcamento(self, auth_headers, empresa_id):
        """Test creating a new budget"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Orçamento_{unique_id}",
            "descricao": "Orçamento de teste"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "numero" in data
        assert data["numero"].startswith("ORC-")
        return data["id"]
    
    def test_add_item_to_orcamento(self, auth_headers, empresa_id):
        """Test adding item to budget with automatic cost calculation"""
        # Create budget first
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Orçamento_Item_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens", headers=auth_headers, json={
            "descricao": "Item de teste",
            "quantidade": 2,
            "unidade": "un",
            "custo_unitario": 100.00,
            "venda_unitario": 150.00
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # Verify budget totals updated
        get_response = requests.get(f"{BASE_URL}/api/orcamentos/{orcamento_id}", headers=auth_headers)
        orcamento = get_response.json()
        assert orcamento["total_custo"] == 200.00  # 2 * 100
        assert orcamento["total_venda"] == 300.00  # 2 * 150
        assert orcamento["total_lucro"] == 100.00  # 300 - 200
    
    def test_approve_orcamento_without_items_fails(self, auth_headers, empresa_id):
        """Test that approving budget without items fails"""
        # Create empty budget
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Orçamento_Empty_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Try to approve
        response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        assert response.status_code == 400
        data = response.json()
        assert "sem itens" in data["detail"].lower() or "itens" in data["detail"].lower()
    
    def test_approve_orcamento_creates_project(self, auth_headers, empresa_id):
        """Test that approving budget creates project automatically"""
        # Create budget
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Orçamento_Approve_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens", headers=auth_headers, json={
            "descricao": "Serviço de teste",
            "quantidade": 1,
            "custo_unitario": 500.00,
            "venda_unitario": 800.00
        })
        
        # Approve budget
        response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projeto_id" in data
        assert "projeto_titulo" in data
        assert data["projeto_titulo"] == f"TEST_Orçamento_Approve_{unique_id}"
        
        # Verify project was created
        projeto_id = data["projeto_id"]
        projeto_response = requests.get(f"{BASE_URL}/api/projetos/{projeto_id}", headers=auth_headers)
        assert projeto_response.status_code == 200
        projeto = projeto_response.json()
        assert projeto["orcamento"]["id"] == orcamento_id
        assert projeto["valor_total"] == 800.00
        
        # Verify Kanban columns were created
        assert len(projeto["colunas"]) == 4
        column_titles = [c["titulo"] for c in projeto["colunas"]]
        assert "A Fazer" in column_titles
        assert "Em Andamento" in column_titles
        assert "Concluído" in column_titles
    
    def test_approve_already_approved_orcamento_fails(self, auth_headers, empresa_id):
        """Test that approving already approved budget fails"""
        # Create and approve budget
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Orçamento_Double_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens", headers=auth_headers, json={
            "descricao": "Serviço",
            "quantidade": 1,
            "custo_unitario": 100.00,
            "venda_unitario": 200.00
        })
        
        # First approval
        requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        
        # Second approval should fail
        response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        assert response.status_code == 400
        data = response.json()
        assert "projeto vinculado" in data["detail"].lower() or "já possui" in data["detail"].lower()


class TestProjetos:
    """Project tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def empresa_id(self, auth_headers):
        """Get first empresa ID"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresas = response.json()
        return empresas[0]["id"]
    
    def test_list_projetos(self, auth_headers, empresa_id):
        """Test listing projects filtered by company"""
        response = requests.get(f"{BASE_URL}/api/projetos?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Projects should show linked budget info
        for projeto in data:
            if projeto.get("orcamento"):
                assert "numero" in projeto["orcamento"]
                assert "total_venda" in projeto["orcamento"]
    
    def test_get_projeto_with_kanban(self, auth_headers, empresa_id):
        """Test getting project with Kanban columns"""
        # First create a project via budget approval
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Projeto_Kanban_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens", headers=auth_headers, json={
            "descricao": "Serviço",
            "quantidade": 1,
            "custo_unitario": 100.00,
            "venda_unitario": 200.00
        })
        
        # Approve to create project
        approve_response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        projeto_id = approve_response.json()["projeto_id"]
        
        # Get project details
        response = requests.get(f"{BASE_URL}/api/projetos/{projeto_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "colunas" in data
        assert len(data["colunas"]) == 4


class TestTarefas:
    """Task tests for Kanban"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def projeto_with_columns(self, auth_headers):
        """Create a project with Kanban columns"""
        # Get empresa
        empresas_response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresa_id = empresas_response.json()[0]["id"]
        
        # Create budget
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/orcamentos", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "titulo": f"TEST_Tarefa_Projeto_{unique_id}"
        })
        orcamento_id = create_response.json()["id"]
        
        # Add item
        requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/itens", headers=auth_headers, json={
            "descricao": "Serviço",
            "quantidade": 1,
            "custo_unitario": 100.00,
            "venda_unitario": 200.00
        })
        
        # Approve
        approve_response = requests.post(f"{BASE_URL}/api/orcamentos/{orcamento_id}/aprovar", headers=auth_headers)
        projeto_id = approve_response.json()["projeto_id"]
        
        # Get project with columns
        projeto_response = requests.get(f"{BASE_URL}/api/projetos/{projeto_id}", headers=auth_headers)
        return projeto_response.json()
    
    def test_create_tarefa(self, auth_headers, projeto_with_columns):
        """Test creating a task in Kanban"""
        coluna_id = projeto_with_columns["colunas"][0]["id"]  # "A Fazer" column
        
        response = requests.post(f"{BASE_URL}/api/tarefas", headers=auth_headers, json={
            "coluna_id": coluna_id,
            "titulo": "TEST_Tarefa de teste"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["titulo"] == "TEST_Tarefa de teste"
    
    def test_delete_tarefa(self, auth_headers, projeto_with_columns):
        """Test deleting a task"""
        coluna_id = projeto_with_columns["colunas"][0]["id"]
        
        # Create task
        create_response = requests.post(f"{BASE_URL}/api/tarefas", headers=auth_headers, json={
            "coluna_id": coluna_id,
            "titulo": "TEST_Tarefa para deletar"
        })
        tarefa_id = create_response.json()["id"]
        
        # Delete task
        response = requests.delete(f"{BASE_URL}/api/tarefas/{tarefa_id}", headers=auth_headers)
        assert response.status_code == 200


class TestFinanceiro:
    """Financial module tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def empresa_id(self, auth_headers):
        """Get first empresa ID"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresas = response.json()
        return empresas[0]["id"]
    
    def test_list_contas(self, auth_headers, empresa_id):
        """Test listing financial accounts"""
        response = requests.get(f"{BASE_URL}/api/contas?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_conta_receber(self, auth_headers, empresa_id):
        """Test creating a receivable account"""
        response = requests.post(f"{BASE_URL}/api/contas", headers=auth_headers, json={
            "empresa_id": empresa_id,
            "tipo": "receber",
            "descricao": "TEST_Conta a receber",
            "valor": 1000.00,
            "data_vencimento": "2026-02-15T00:00:00Z"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_resumo_financeiro(self, auth_headers, empresa_id):
        """Test financial summary"""
        response = requests.get(f"{BASE_URL}/api/financeiro/resumo?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_receber" in data
        assert "total_pagar" in data
        assert "saldo" in data


class TestDashboard:
    """Dashboard tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "senha": TEST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def empresa_id(self, auth_headers):
        """Get first empresa ID"""
        response = requests.get(f"{BASE_URL}/api/empresas", headers=auth_headers)
        empresas = response.json()
        return empresas[0]["id"]
    
    def test_dashboard(self, auth_headers, empresa_id):
        """Test dashboard data"""
        response = requests.get(f"{BASE_URL}/api/dashboard?empresa_id={empresa_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projetos" in data
        assert "orcamentos" in data
        assert "total_clientes" in data
        assert "contas_vencendo" in data
