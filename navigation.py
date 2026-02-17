# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from dotenv import load_dotenv
from config import CONFIG, ENV_PATH
from utils import encontrar_frame, aguardar_elemento, verificar_sessao_ativa

load_dotenv(dotenv_path=ENV_PATH)
logger = logging.getLogger(__name__)

async def fazer_login(page):
    """Realiza login no sistema"""
    try:
        logger.info("Iniciando processo de login...")
        
        await page.goto(CONFIG["url"])
        await page.wait_for_load_state("networkidle")
        
        frame = await encontrar_frame(page, CONFIG["selectors"]["login_frame_pattern"])
        
        if not await aguardar_elemento(frame, CONFIG["selectors"]["username_field"]):
            raise Exception("Campo de usuário não encontrado")
        
        # Obter credenciais - SEM FALLBACK
        username = os.getenv('APP_USERNAME')
        password = os.getenv('APP_PASSWORD')
        
        if not username or not password:
            raise Exception(
                "Credenciais não encontradas. Configure APP_USERNAME e APP_PASSWORD "
                "no arquivo env_file.env na pasta Arquivos"
            )
        
        await frame.fill(CONFIG["selectors"]["username_field"], username)
        await frame.fill(CONFIG["selectors"]["password_field"], password)
        await frame.click(CONFIG["selectors"]["login_button"])
        
        # Aguardar carregamento usando wait_for_load_state ao invés de sleep
        await page.wait_for_load_state("networkidle")
        
        logger.info("✅ Login realizado com sucesso")
        return frame
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise

async def voltar_para_gestao_acesso(page, frame):
    """Volta para o menu principal de gestão de acesso"""
    try:
        logger.debug("Voltando para o menu principal...")
        
        await page.wait_for_load_state("domcontentloaded")
        
        tentativas_maximas = 3
        selectors_alternativos = [
            'a[href="menu.do"]',
            'a[href*="menu.do"]',
            'a:has-text("Menu")',
            'a:has-text("Voltar")',
            'a:has-text("Principal")',
        ]
        
        for tentativa in range(tentativas_maximas):
            logger.debug(f"Tentativa {tentativa + 1} de voltar ao menu")
            
            await asyncio.sleep(0.5)
            
            frames = page.frames
            link_clicado = False
            
            for seletor in selectors_alternativos:
                if link_clicado:
                    break
                    
                for current_frame in frames:
                    try:
                        await current_frame.wait_for_load_state("domcontentloaded", timeout=5000)
                        
                        links = current_frame.locator(seletor)
                        count = await links.count()
                        
                        if count > 0:
                            logger.debug(f"Encontrados {count} links com seletor '{seletor}'")
                            
                            for i in range(count):
                                link = links.nth(i)
                                try:
                                    await link.wait_for(state="visible", timeout=3000)
                                    
                                    if await link.is_visible() and await link.is_enabled():
                                        try:
                                            await link.click(timeout=5000)
                                            logger.debug(f"✅ Clique realizado com sucesso no link para voltar ao menu")
                                        except:
                                            await link.evaluate("element => element.click()")
                                            logger.debug(f"✅ Clique via JavaScript realizado")
                                        
                                        link_clicado = True
                                        break
                                        
                                except Exception as click_error:
                                    logger.debug(f"Link {i+1} não disponível: {click_error}")
                                    continue
                        
                        if link_clicado:
                            break
                            
                    except Exception as frame_error:
                        logger.debug(f"Frame não disponível para seletor '{seletor}': {frame_error}")
                        continue
            
            if link_clicado:
                break
            else:
                logger.debug(f"Tentativa {tentativa + 1} falhou, aguardando...")
                await asyncio.sleep(1.5)
        
        if not link_clicado:
            logger.debug("Tentando navegação direta pela URL...")
            try:
                current_url = page.url
                base_url = current_url.split('/')[0] + '//' + current_url.split('/')[2]
                menu_url = f"{base_url}/menu.do"
                
                await page.goto(menu_url)
                await page.wait_for_load_state("domcontentloaded")
                logger.debug("✅ Navegação direta realizada")
                link_clicado = True
                
            except Exception as url_error:
                logger.debug(f"Navegação direta falhou: {url_error}")
        
        if link_clicado:
            await page.wait_for_load_state("networkidle")
            
            try:
                # Tentar encontrar frame do menu sem warnings excessivos
                menu_frame = await encontrar_frame(page, CONFIG["selectors"]["login_frame_pattern"])
                if menu_frame:
                    await menu_frame.wait_for_selector(CONFIG["selectors"]["access_link"], timeout=5000)
                    logger.debug("✅ Retorno ao menu confirmado")
            except Exception as verify_error:
                # Não é crítico se não conseguir verificar
                logger.debug(f"Verificação do menu: {verify_error}")
        else:
            logger.debug("Não foi possível voltar ao menu de forma explícita, continuando...")
            
            if not await verificar_sessao_ativa(page):
                raise Exception("Sessão possivelmente expirou")
        
    except Exception as e:
        logger.debug(f"Erro ao voltar para o menu: {e}")
        # Não é crítico, continuar processamento
        pass

async def navegar_para_incluir_acesso(page, frame):
    """Navega para a página de incluir acesso"""
    max_tentativas = 3
    
    for tentativa in range(max_tentativas):
        try:
            logger.debug(f"Navegando para incluir acesso... (tentativa {tentativa + 1}/{max_tentativas})")
            
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=5000)
            except:
                logger.debug("Frame pode estar instável, procurando novo frame...")
                frame = await encontrar_frame(page, CONFIG["selectors"]["login_frame_pattern"])
            
            if not await aguardar_elemento(frame, CONFIG["selectors"]["access_link"], timeout=10000):
                raise Exception(f"Link de acesso não encontrado na tentativa {tentativa + 1}")
            
            await frame.click(CONFIG["selectors"]["access_link"], timeout=10000)
            await page.wait_for_load_state("networkidle")
            
            target_frame = await encontrar_frame(page, "usuarios_incluiAcesso.do")
            
            await target_frame.select_option(CONFIG["selectors"]["frequency_select"], CONFIG["values"]["frequency_id"])
            await target_frame.click(CONFIG["selectors"]["submit_button"])
            
            await page.wait_for_load_state("networkidle")
            
            logger.debug("✅ Navegação para incluir acesso concluída")
            return target_frame
            
        except Exception as e:
            if tentativa < max_tentativas - 1:
                logger.debug(f"Tentativa {tentativa + 1} falhou: {e}")
                logger.debug(f"Tentando recuperar sessão...")
                
                try:
                    await voltar_para_gestao_acesso(page, frame)
                    await asyncio.sleep(2)
                    
                    if not await verificar_sessao_ativa(page):
                        logger.warning("Sessão pode ter expirado, tentando relogar...")
                        frame = await fazer_login(page)
                    else:
                        frame = await encontrar_frame(page, CONFIG["selectors"]["login_frame_pattern"])
                    
                except Exception as recovery_error:
                    logger.debug(f"Erro na recuperação: {recovery_error}")
                    if tentativa == max_tentativas - 1:
                        raise Exception(f"Falha após {max_tentativas} tentativas: {e}")
            else:
                logger.error(f"Erro na navegação após {max_tentativas} tentativas: {e}")
                raise Exception(f"Falha crítica na navegação: {e}")
    
    raise Exception(f"Não foi possível navegar após {max_tentativas} tentativas")