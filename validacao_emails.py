# -*- coding: utf-8 -*-
"""
Script para testar validação de emails e usuários
Execute este script para verificar se seus dados passarão na validação
"""
import sys
import os
import pandas as pd

# Importar funções de validação
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import validar_email, validar_usuario, validar_dados_usuario
from config import EXCEL_FILE

def testar_sanitizacao():
    """Testa a função de sanitização de dados"""
    print("\n" + "=" * 80)
    print("TESTANDO SANITIZAÇÃO AUTOMÁTICA")
    print("=" * 80)
    
    # Importar a função de sanitização
    from utils import sanitizar_dados_usuario
    
    dados_teste = [
        {
            "usuario": "  usuario123  ",
            "email": " email@exemplo.com ",
            "nome": "  Nome Completo  ",
            "filtro_cliente": " cliente123 "
        },
        {
            "usuario": "normal",
            "email": "normal@exemplo.com",
            "nome": "Nome Normal",
            "filtro_cliente": "cliente456"
        },
        {
            "usuario": "\t\tusuario_tab\t\t",
            "email": "\nemail@tab.com\n",
            "nome": "  Nome   com   espaços  ",
            "filtro_cliente": "cliente"
        }
    ]
    
    print("\n🧹 Testando remoção de espaços:")
    for i, dados in enumerate(dados_teste, 1):
        print(f"\n  Teste {i}:")
        print(f"    Antes:")
        print(f"      usuario: '{dados['usuario']}'")
        print(f"      email: '{dados['email']}'")
        
        dados_limpos = sanitizar_dados_usuario(pd.Series(dados))
        
        print(f"    Depois:")
        print(f"      usuario: '{dados_limpos['usuario']}'")
        print(f"      email: '{dados_limpos['email']}'")

def testar_emails_comuns():
    """Testa emails comuns para garantir que a validação está correta"""
    print("=" * 80)
    print("TESTANDO VALIDAÇÃO DE EMAILS")
    print("=" * 80)
    
    emails_teste = [
        # Emails válidos
        ("53668.ana@callinksys.com.br", True),
        ("58148.ana@callinksys.com.br", True),
        ("usuario@exemplo.com", True),
        ("123456@dominio.com.br", True),
        ("nome.sobrenome@empresa.com", True),
        ("teste_123@site.com.br", True),
        ("user+tag@mail.com", True),
        ("1234567890@email.com", True),
        
        # Emails inválidos
        ("email@", False),
        ("@dominio.com", False),
        ("email sem arroba.com", False),
        ("email@dominio", False),
        ("", False),
    ]
    
    print("\n✅ Emails que DEVEM ser aceitos:")
    for email, esperado in emails_teste:
        if esperado:
            resultado = validar_email(email)
            status = "✅" if resultado else "❌"
            print(f"  {status} {email} -> {'VÁLIDO' if resultado else 'INVÁLIDO (ERRO!)'}")
    
    print("\n❌ Emails que DEVEM ser rejeitados:")
    for email, esperado in emails_teste:
        if not esperado:
            resultado = validar_email(email)
            status = "✅" if not resultado else "❌"
            print(f"  {status} {email} -> {'INVÁLIDO' if not resultado else 'VÁLIDO (ERRO!)'}")

def testar_usuarios_comuns():
    """Testa usuários comuns"""
    print("\n" + "=" * 80)
    print("TESTANDO VALIDAÇÃO DE USUÁRIOS")
    print("=" * 80)
    
    usuarios_teste = [
        # Usuários válidos
        ("53668.ana@callinksys.com.br", True),
        ("usuario123", True),
        ("user_name", True),
        ("123456", True),
        ("user@domain", True),
        ("test.user", True),
        
        # Usuários inválidos
        ("ab", False),  # Muito curto
        ("", False),
        ("user name", False),  # Espaço não permitido
    ]
    
    print("\n✅ Usuários que DEVEM ser aceitos:")
    for usuario, esperado in usuarios_teste:
        if esperado:
            resultado = validar_usuario(usuario)
            status = "✅" if resultado else "❌"
            print(f"  {status} {usuario} -> {'VÁLIDO' if resultado else 'INVÁLIDO (ERRO!)'}")
    
    print("\n❌ Usuários que DEVEM ser rejeitados:")
    for usuario, esperado in usuarios_teste:
        if not esperado:
            resultado = validar_usuario(usuario)
            status = "✅" if not resultado else "❌"
            print(f"  {status} '{usuario}' -> {'INVÁLIDO' if not resultado else 'VÁLIDO (ERRO!)'}")

def testar_planilha():
    """Testa todos os emails da planilha"""
    print("\n" + "=" * 80)
    print("TESTANDO EMAILS DA PLANILHA COM SANITIZAÇÃO")
    print("=" * 80)
    
    if not os.path.exists(EXCEL_FILE):
        print(f"\n❌ Arquivo não encontrado: {EXCEL_FILE}")
        return
    
    try:
        from utils import sanitizar_dados_usuario
        
        df = pd.read_excel(EXCEL_FILE)
        
        if 'email' not in df.columns:
            print("❌ Coluna 'email' não encontrada na planilha")
            return
        
        print(f"\n📊 Total de linhas: {len(df)}")
        
        validos = 0
        invalidos = 0
        sanitizados = 0
        emails_invalidos = []
        
        for idx, linha in df.iterrows():
            # Sanitizar antes de validar
            linha_limpa = sanitizar_dados_usuario(linha)
            
            # Verificar se houve sanitização
            foi_sanitizado = False
            for campo in ['usuario', 'email', 'nome', 'filtro_cliente']:
                if campo in linha and pd.notna(linha[campo]):
                    if str(linha[campo]) != str(linha_limpa[campo]):
                        foi_sanitizado = True
                        break
            
            if foi_sanitizado:
                sanitizados += 1
            
            email = linha_limpa.get('email', '')
            usuario = linha_limpa.get('usuario', '')
            
            try:
                validar_dados_usuario(linha_limpa)
                validos += 1
                status = "🧹" if foi_sanitizado else "✅"
                print(f"  {status} Linha {idx + 2}: {usuario} / {email}")
                if foi_sanitizado:
                    print(f"      (espaços removidos automaticamente)")
            except ValueError as e:
                invalidos += 1
                emails_invalidos.append((idx + 2, usuario, email, str(e)))
                print(f"  ❌ Linha {idx + 2}: {usuario} / {email}")
                print(f"      Erro: {e}")
        
        print("\n" + "=" * 80)
        print("RESUMO")
        print("=" * 80)
        print(f"✅ Válidos: {validos}")
        print(f"🧹 Sanitizados automaticamente: {sanitizados}")
        print(f"❌ Inválidos: {invalidos}")
        
        if sanitizados > 0:
            print(f"\n✨ {sanitizados} linha(s) tinham espaços que serão removidos automaticamente!")
        
        if invalidos > 0:
            print("\n⚠️  ATENÇÃO: Alguns emails/usuários não passaram na validação!")
            print("Eles serão IGNORADOS durante a execução do automatizador.")
            print("\nPara corrigir:")
            print("1. Verifique se os emails estão no formato correto: exemplo@dominio.com")
            print("2. Verifique se os usuários têm pelo menos 3 caracteres")
            print("3. Remova espaços e caracteres especiais inválidos")
        else:
            print("\n🎉 Todos os emails e usuários estão válidos!")
            if sanitizados > 0:
                print("   (Espaços serão removidos automaticamente durante o processamento)")
        
    except Exception as e:
        print(f"\n❌ Erro ao ler planilha: {e}")

if __name__ == "__main__":
    print("🔍 TESTADOR DE VALIDAÇÃO DE DADOS")
    print("Este script verifica se seus emails e usuários passarão na validação\n")
    
    testar_sanitizacao()
    testar_emails_comuns()
    testar_usuarios_comuns()
    testar_planilha()
    
    print("\n" + "=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)