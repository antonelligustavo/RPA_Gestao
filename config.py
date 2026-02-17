# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        # Executável PyInstaller
        return sys._MEIPASS
    else:
        # Script Python normal
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)

def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)

BASE_PATH = get_base_path()
ARQUIVOS_FOLDER = get_resource_path("Arquivos")
LOGS_FOLDER = get_resource_path("Log")

ENV_PATH = os.path.join(ARQUIVOS_FOLDER, "env_file.env")
EXCEL_FILE = os.path.join(ARQUIVOS_FOLDER, "usuarios.xlsx")

ensure_directory_exists(ARQUIVOS_FOLDER)
ensure_directory_exists(LOGS_FOLDER)

CONFIG = {
    "url": "https://files.jall.com.br",
    "selectors": {
        "login_frame_pattern": "menu.do",
        "username_field": "#l_username",
        "password_field": "#l_password",
        "login_button": "#entrar",
        "access_link": 'a[href="usuarios_incluiAcesso.do"]',
        "gestao_acesso_link": 'a[href="menu.do"]',
        "frequency_select": "#frq_id",
        "submit_button": "#enviar",
        "subgroup_select": "#subgrupo",
        "login_gestor": "#loginGestor",
        "email_gestor": "#emailGestor",
        "login_gestor2": "#loginGestor2",
        "email_gestor2": "#emailGestor2",
        "nome": "#nome",
        "obs": "#obs",
        "usuario": "#usuario",
        "email": "#email",
        "filtro_cliente": "#filtro_cliente",
        "tipo_pes_select": 'select[name="tipo_pes_id"]',
        "cargo_select": 'select[name="cargo"]',
        "setor_select": 'select[name="setor"]',
        "lupa_button": 'img[src="imagens/icones/lupa.gif"]',
        "empresa_input": 'input[name="empresa_id"]',
        # Seletores para detectar mensagens de erro/alerta
        "mensagem_erro": ".mensagem-erro, .alert, .error, div[class*='erro']",
        "mensagem_alerta": ".alert-warning, .aviso, div[class*='alert']"
    },
    "values": {
        "frequency_id": "90",
        "tipo_pes_id": "1",
        "cargo_id": "55 ",
        "setor_id": "43 ",
        "obs_text": "Automatizado pelo RPA",
    },
    "defaults": {
        "subgroup_id": "32",
        "empresa_input_position": 0
    },
    "timeouts": {
        "navigation": 30000,
        "element": 15000,
        "element_critical": 20000,
        "page_load": 3000,
        "frame_stability": 2000,
        "retry_delay": 2000,
        "polling_interval": 1000,
        "empresa_input_timeout": 25000
    }
}

def get_log_filename():
    ensure_directory_exists(LOGS_FOLDER)
    filename = f'automatizador_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    return os.path.join(LOGS_FOLDER, filename)

def get_report_filename():
    ensure_directory_exists(LOGS_FOLDER)
    filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return os.path.join(LOGS_FOLDER, filename)

def get_report_txt_filename():
    ensure_directory_exists(LOGS_FOLDER)
    filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return os.path.join(LOGS_FOLDER, filename)

def verificar_arquivos_necessarios():
    print(f"📁 Caminho base do projeto: {BASE_PATH}")
    print(f"📁 Pasta Arquivos: {ARQUIVOS_FOLDER}")
    print(f"📁 Pasta Log: {LOGS_FOLDER}")
    
    if os.path.exists(ENV_PATH):
        print(f"✅ Arquivo .env encontrado: {ENV_PATH}")
    else:
        print(f"❌ Arquivo .env NÃO encontrado: {ENV_PATH}")
        print("💡 Crie o arquivo 'env_file.env' na pasta 'Arquivos' com suas credenciais!")
    
    if os.path.exists(EXCEL_FILE):
        print(f"✅ Planilha Excel encontrada: {EXCEL_FILE}")
    else:
        print(f"❌ Planilha Excel NÃO encontrada: {EXCEL_FILE}")
        print("💡 Coloque o arquivo 'usuarios.xlsx' na pasta 'Arquivos'!")
    
    return os.path.exists(ENV_PATH) and os.path.exists(EXCEL_FILE)

if __name__ == "__main__":
    print("🔍 Verificando estrutura de arquivos...")
    verificar_arquivos_necessarios()