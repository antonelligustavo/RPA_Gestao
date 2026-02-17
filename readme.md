# 🤖 Automatizador de Gestão de Acesso

Um sistema automatizado para gestão de usuários e acessos utilizando RPA (Robotic Process Automation) com Python e Playwright.

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Bibliotecas Utilizadas](#-bibliotecas-utilizadas)
- [Solução de Problemas](#-solução-de-problemas)
- [Compatibilidade](#-compatibilidade)
- [Autor](#-autor)

## 🎯 Sobre o Projeto

O **Automatizador de Gestão de Acesso** é uma solução RPA desenvolvida em Python que automatiza o processo de criação e gestão de usuários em sistemas web. Utilizando Playwright para automação de navegador, o sistema processa dados de planilhas Excel e executa ações automatizadas de forma eficiente e confiável.

### ✨ Funcionalidades

- 🔄 **Automação Web**: Controle automatizado de navegadores
- 📊 **Processamento de Dados**: Leitura e manipulação de planilhas Excel
- 🔐 **Segurança**: Gerenciamento seguro de credenciais via arquivo .env
- 📝 **Logging**: Sistema completo de logs para monitoramento
- ⚡ **Assíncrono**: Execução otimizada com programação assíncrona
- 🎯 **Modular**: Arquitetura organizada em módulos especializados

## 🔧 Pré-requisitos

### Sistema
- **Python**: 3.8 ou superior
- **Sistema Operacional**: Windows 10/11, macOS 10.14+, ou Linux (Ubuntu 18.04+)

### Conhecimentos
- Básico de Python
- Conceitos de automação web
- Manipulação de planilhas Excel

## 📦 Instalação

### Método 1: Instalação Rápida
```bash
# Clone o repositório
git clone [URL_DO_SEU_REPOSITORIO]
cd RPA_Gestao_V1

# Instale as dependências
pip install playwright pandas openpyxl python-dotenv

# Instale os navegadores do Playwright
playwright install chromium
```

### Método 2: Usando requirements.txt
```bash
# Instale as dependências
pip install -r requirements.txt

# Instale os navegadores
playwright install chromium
```

### Método 3: Ambiente Virtual (Recomendado)
```bash
# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
playwright install chromium
```

## ⚙️ Configuração

### 1. Estrutura de Diretórios
Certifique-se de que a estrutura de pastas esteja organizada:

```
RPA_Gestao_V1/
├── main.py                 # Arquivo principal
├── automatizador.py        # Lógica de automação
├── config.py              # Configurações
├── form_processor.py      # Processamento de formulários
├── navigation.py          # Navegação web
├── utils.py               # Utilitários
├── requirements.txt       # Dependências
├── README.md             # Documentação
├── Arquivos/
│   ├── env_file.env      # Variáveis de ambiente
│   └── usuarios.xlsx     # Planilha de usuários
└── Log/                  # Diretório de logs
```

### 2. Configuração do Ambiente
Crie o arquivo `Arquivos/env_file.env`:

```env
# Credenciais de acesso
APP_USERNAME=seu_usuario_aqui
APP_PASSWORD=sua_senha_aqui
```

### 3. Preparação da Planilha Excel
Configure o arquivo `Arquivos/usuarios.xlsx` com as seguintes colunas:

#### Colunas Obrigatórias:
| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `nome` | Nome completo do usuário | João Silva |
| `usuario` | Login do usuário | joao.silva |
| `email` | Email do usuário | joao@empresa.com |
| `filtro_cliente` | Filtro do cliente | CLIENTE_001 |
| `loginGestor` | Login do gestor | - |
| `emailGestor` | Email do gestor | - |
| `loginGestor2` | Login do segundo gestor | - |
| `emailGestor2` | Email do segundo gestor | - |
| `subgroup_id` | ID do subgrupo | 32 |
| `empresa_input_position` | Posição do input da empresa | 0 |

## 🚀 Como Usar

### Execução Básica
```bash
python main.py
```

### Monitoramento
Os logs são salvos automaticamente na pasta `Log/` com timestamp para fácil rastreamento.

## 📚 Bibliotecas Utilizadas

### 🎭 Playwright (v1.41.0)
- **Função**: Automação de navegadores web
- **Por que usar**: Suporte moderno a navegadores, execução assíncrona, confiabilidade

### 🐼 Pandas (v2.1.4)
- **Função**: Manipulação e análise de dados
- **Por que usar**: Processamento eficiente de planilhas Excel, manipulação de DataFrames

### 📊 OpenPyXL (v3.1.2)
- **Função**: Leitura e escrita de arquivos Excel
- **Por que usar**: Compatibilidade total com formato .xlsx

### 🔐 Python-dotenv (v1.0.0)
- **Função**: Carregamento de variáveis de ambiente
- **Por que usar**: Segurança no armazenamento de credenciais

### Bibliotecas Built-in
- `asyncio`: Programação assíncrona
- `logging`: Sistema de logs
- `os`: Operações do sistema
- `json`: Manipulação JSON
- `datetime`: Manipulação de datas

## 🐛 Solução de Problemas

### Problemas Comuns

#### ❌ "playwright not found"
```bash
pip install playwright
playwright install chromium
```

#### ❌ "No module named 'openpyxl'"
```bash
pip install openpyxl
```

#### ❌ "Environment file not found"
- Verifique se `Arquivos/env_file.env` existe
- Confirme as credenciais

#### ❌ Erro de Permissão
```bash
# Windows (executar como administrador)
pip install --user [biblioteca]

# Linux/Mac
sudo pip install [biblioteca]
```

### Comandos de Diagnóstico

```bash
# Verificar Python
python --version

# Verificar pip
pip --version

# Listar bibliotecas instaladas
pip list | grep -E "(playwright|pandas|openpyxl|python-dotenv)"

# Verificar Playwright
playwright --version
```

## 🔄 Atualizações

```bash
# Atualizar todas as bibliotecas
pip install --upgrade playwright pandas openpyxl python-dotenv

# Atualizar navegadores
playwright install chromium
```

## ✅ Checklist de Instalação

- [ ] Python 3.8+ instalado
- [ ] pip funcionando
- [ ] Playwright instalado
- [ ] Navegadores do Playwright instalados
- [ ] Pandas e OpenPyXL instalados
- [ ] Python-dotenv instalado
- [ ] Arquivo `.env` configurado
- [ ] Planilha Excel preparada
- [ ] Estrutura de pastas criada

## 🌐 Compatibilidade

### Sistemas Operacionais
| SO | Status | Versão Mínima |
|----|--------|---------------|
| Windows | ✅ | 10/11 |
| macOS | ✅ | 10.14+ |
| Linux | ✅ | Ubuntu 18.04+ |

### Versões Python
| Versão | Status |
|--------|--------|
| 3.8 | ✅ |
| 3.9 | ✅ |
| 3.10 | ✅ |
| 3.11 | ✅ |
| 3.12 | ✅ |

## 👨‍💻 Autor

**Gustavo Antonelli**

- GitHub: [github.com/antonelligustavo]
- LinkedIn: [www.linkedin.com/in/gustavo-fordiani-antonelli/]
- Email: [antonelligustavo1@gmail.com]

---

</div>
