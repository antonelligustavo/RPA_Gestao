# -*- coding: utf-8 -*-
"""
Script auxiliar para descobrir os valores corretos dos selects do sistema
Execute este script para ver quais valores estão disponíveis
"""
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Importar configurações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CONFIG, ENV_PATH

load_dotenv(dotenv_path=ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def descobrir_valores():
    """Descobre os valores disponíveis nos selects"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False para ver o que está acontecendo
        page = await browser.new_page()
        
        try:
            # Fazer login
            logger.info("🔐 Fazendo login...")
            await page.goto(CONFIG["url"])
            await page.wait_for_load_state("networkidle")
            
            # Encontrar frame de login
            frame = None
            for f in page.frames:
                if CONFIG["selectors"]["login_frame_pattern"] in f.url:
                    frame = f
                    break
            
            if not frame:
                raise Exception("Frame de login não encontrado")
            
            # Obter credenciais
            username = os.getenv('APP_USERNAME')
            password = os.getenv('APP_PASSWORD')
            
            if not username or not password:
                raise Exception("Configure APP_USERNAME e APP_PASSWORD no arquivo .env")
            
            await frame.fill(CONFIG["selectors"]["username_field"], username)
            await frame.fill(CONFIG["selectors"]["password_field"], password)
            await frame.click(CONFIG["selectors"]["login_button"])
            await page.wait_for_load_state("networkidle")
            
            logger.info("✅ Login realizado")
            
            # Navegar para incluir acesso
            logger.info("🔍 Navegando para incluir acesso...")
            
            # Encontrar frame do menu
            menu_frame = None
            for f in page.frames:
                if CONFIG["selectors"]["login_frame_pattern"] in f.url:
                    menu_frame = f
                    break
            
            if not menu_frame:
                raise Exception("Frame do menu não encontrado")
            
            await menu_frame.click(CONFIG["selectors"]["access_link"])
            await page.wait_for_load_state("networkidle")
            
            # Encontrar frame de incluir acesso
            acesso_frame = None
            for f in page.frames:
                if "usuarios_incluiAcesso.do" in f.url:
                    acesso_frame = f
                    break
            
            if not acesso_frame:
                raise Exception("Frame de incluir acesso não encontrado")
            
            await acesso_frame.select_option(CONFIG["selectors"]["frequency_select"], CONFIG["values"]["frequency_id"])
            await acesso_frame.click(CONFIG["selectors"]["submit_button"])
            await asyncio.sleep(2)
            
            # Encontrar frame de grupo
            grupo_frame = None
            for f in page.frames:
                if "usuarios_incluiGrupo.do" in f.url:
                    grupo_frame = f
                    break
            
            if not grupo_frame:
                raise Exception("Frame de grupo não encontrado")
            
            logger.info("✅ Navegação concluída")
            logger.info("")
            logger.info("=" * 80)
            logger.info("VALORES DISPONÍVEIS NOS SELECTS")
            logger.info("=" * 80)
            
            # Descobrir valores do SUBGRUPO
            logger.info("\n📋 SUBGRUPO:")
            subgrupo_opcoes = await grupo_frame.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return null;
                    return Array.from(select.options).map(opt => ({
                        value: opt.value,
                        text: opt.text
                    }));
                }
            """, CONFIG["selectors"]["subgroup_select"])
            
            if subgrupo_opcoes:
                for opcao in subgrupo_opcoes:
                    if opcao['value']:  # Pular opções vazias
                        logger.info(f"  Valor: '{opcao['value']}' | Texto: '{opcao['text']}'")
            
            # Selecionar primeiro subgrupo válido
            primeira_opcao = next((opt for opt in subgrupo_opcoes if opt['value']), None)
            if primeira_opcao:
                await grupo_frame.select_option(CONFIG["selectors"]["subgroup_select"], primeira_opcao['value'])
            
            await asyncio.sleep(1)
            
            # Descobrir valores de TIPO DE PESSOA
            logger.info("\n📋 TIPO DE PESSOA:")
            tipo_pes_opcoes = await grupo_frame.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return null;
                    return Array.from(select.options).map(opt => ({
                        value: opt.value,
                        text: opt.text
                    }));
                }
            """, CONFIG["selectors"]["tipo_pes_select"])
            
            if tipo_pes_opcoes:
                for opcao in tipo_pes_opcoes:
                    if opcao['value']:
                        logger.info(f"  Valor: '{opcao['value']}' | Texto: '{opcao['text']}'")
            
            # Descobrir valores de CARGO
            logger.info("\n📋 CARGO:")
            cargo_opcoes = await grupo_frame.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return null;
                    return Array.from(select.options).map(opt => ({
                        value: opt.value,
                        text: opt.text
                    }));
                }
            """, CONFIG["selectors"]["cargo_select"])
            
            if cargo_opcoes:
                for opcao in cargo_opcoes:
                    if opcao['value']:
                        valor_repr = repr(opcao['value'])  # Mostra espaços ocultos
                        logger.info(f"  Valor: {valor_repr} | Texto: '{opcao['text']}'")
            
            # Descobrir valores de SETOR
            logger.info("\n📋 SETOR:")
            setor_opcoes = await grupo_frame.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return null;
                    return Array.from(select.options).map(opt => ({
                        value: opt.value,
                        text: opt.text
                    }));
                }
            """, CONFIG["selectors"]["setor_select"])
            
            if setor_opcoes:
                for opcao in setor_opcoes:
                    if opcao['value']:
                        valor_repr = repr(opcao['value'])
                        logger.info(f"  Valor: {valor_repr} | Texto: '{opcao['text']}'")
            
            logger.info("\n" + "=" * 80)
            logger.info("💡 INSTRUÇÕES:")
            logger.info("=" * 80)
            logger.info("1. Copie os valores EXATOS (incluindo espaços) que você vê acima")
            logger.info("2. Cole-os no arquivo config.py na seção 'values'")
            logger.info("3. Exemplo:")
            logger.info('   "cargo_id": "55 ",  # Se o valor tiver espaço no final')
            logger.info('   "setor_id": "43",   # Sem espaço')
            logger.info("\n⏸️  Janela ficará aberta por 30 segundos para você verificar visualmente...")
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            logger.exception("Detalhes:")
            await asyncio.sleep(10)
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🔍 Descobrindo valores dos selects...")
    print("📌 Este script abrirá o navegador e mostrará os valores disponíveis")
    print("")
    asyncio.run(descobrir_valores())