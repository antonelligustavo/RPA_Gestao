# -*- coding: utf-8 -*-
import asyncio
import logging
import pandas as pd
import re
from functools import wraps
from config import CONFIG

logger = logging.getLogger(__name__)

def retry_async(max_attempts=3, delay=1, backoff=1.5, log_level="WARNING"):
    """Decorator para retry automático em funções assíncronas"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"{func.__name__} falhou após {max_attempts} tentativas")
                        raise
                    
                    # Usar nível de log configurável
                    if log_level == "DEBUG":
                        logger.debug(f"{func.__name__} falhou (tentativa {attempt}/{max_attempts}): {e}")
                    elif log_level == "WARNING":
                        logger.warning(f"{func.__name__} falhou (tentativa {attempt}/{max_attempts}): {e}")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator

@retry_async(max_attempts=10, delay=0.5, backoff=1.2, log_level="DEBUG")
async def encontrar_frame(page, url_pattern):
    """Encontra frame com validação de estado ativo"""
    logger.debug(f"Procurando frame com padrão: {url_pattern}")
    
    frame = next((f for f in page.frames if url_pattern in f.url), None)
    if frame:
        # Validar que frame está ativo
        try:
            await frame.evaluate('() => document.readyState')
            logger.debug(f"Frame encontrado e validado: {frame.url}")
            return frame
        except Exception as e:
            if "detached" in str(e).lower():
                logger.debug("Frame detached, tentando novamente...")
                raise
            raise
    
    raise RuntimeError(f"Frame com padrão '{url_pattern}' não encontrado")

@retry_async(max_attempts=3, delay=2, backoff=1.5, log_level="DEBUG")
async def aguardar_elemento(frame_ou_page, seletor, timeout=10000):
    """Aguarda um elemento aparecer e ficar visível"""
    logger.debug(f"Aguardando elemento '{seletor}'")
    
    # Aguardar o elemento ficar visível
    await frame_ou_page.wait_for_selector(seletor, timeout=timeout, state='visible')
    logger.debug(f"Elemento '{seletor}' encontrado e visível")
    return True

async def aguardar_elemento_com_polling(frame_ou_page, seletor, timeout=30000, intervalo_polling=1000):
    """Versão alternativa com polling manual - use como fallback"""
    tempo_inicial = asyncio.get_event_loop().time()
    timeout_segundos = timeout / 1000
    intervalo_segundos = intervalo_polling / 1000
    
    logger.debug(f"Iniciando polling para elemento '{seletor}'")
    
    while (asyncio.get_event_loop().time() - tempo_inicial) < timeout_segundos:
        try:
            elementos = frame_ou_page.locator(seletor)
            count = await elementos.count()
            
            if count > 0:
                # Verificar se pelo menos um elemento está visível
                for i in range(count):
                    try:
                        elemento = elementos.nth(i)
                        if await elemento.is_visible():
                            logger.debug(f"Elemento '{seletor}' encontrado via polling")
                            return True
                    except:
                        continue
            
            await asyncio.sleep(intervalo_segundos)
            
        except Exception as e:
            logger.debug(f"Erro no polling para '{seletor}': {e}")
            await asyncio.sleep(intervalo_segundos)
    
    logger.error(f"Timeout no polling para elemento {seletor}")
    return False

async def verificar_usuario_ja_cadastrado(page):
    """
    Verifica se apareceu mensagem de 'Usuário já cadastrado' após submissão
    Retorna True se o usuário já existe, False caso contrário
    """
    try:
        # Aguardar um pouco para a mensagem aparecer
        await asyncio.sleep(1)
        
        # Procurar em todos os frames por mensagens de erro/alerta
        mensagens_usuario_existente = [
            "já cadastrado",
            "ja cadastrado",
            "já existe",
            "ja existe",
            "usuário existente",
            "usuario existente",
            "duplicate",
            "duplicado"
        ]
        
        for frame in page.frames:
            try:
                # Obter todo o texto da página
                texto_pagina = await frame.evaluate("() => document.body.innerText")
                texto_lower = texto_pagina.lower()
                
                # Verificar se alguma mensagem de usuário existente está presente
                for mensagem in mensagens_usuario_existente:
                    if mensagem in texto_lower:
                        logger.debug(f"Detectada mensagem de usuário existente: '{mensagem}' no frame {frame.url}")
                        return True
                
                # Procurar por alertas/mensagens de erro visíveis
                alertas = [
                    "div[class*='alert']",
                    "div[class*='error']",
                    "div[class*='mensagem']",
                    "div[class*='aviso']",
                    "span[class*='error']",
                    ".alert",
                    ".error",
                    ".mensagem"
                ]
                
                for seletor in alertas:
                    try:
                        elementos = frame.locator(seletor)
                        count = await elementos.count()
                        
                        for i in range(count):
                            texto_elemento = await elementos.nth(i).inner_text()
                            texto_elemento_lower = texto_elemento.lower()
                            
                            for mensagem in mensagens_usuario_existente:
                                if mensagem in texto_elemento_lower:
                                    logger.debug(f"Mensagem de usuário existente encontrada em alerta: '{texto_elemento}'")
                                    return True
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Erro ao verificar frame {frame.url}: {e}")
                continue
        
        return False
        
    except Exception as e:
        logger.debug(f"Erro ao verificar usuário já cadastrado: {e}")
        return False

async def verificar_sessao_ativa(page):
    """Verifica se a sessão ainda está ativa"""
    try:
        current_url = page.url
        if "login" in current_url.lower() or "erro" in current_url.lower():
            logger.warning("Sessão pode ter expirado")
            return False
        return True
    except:
        return False

def obter_subgroup_id(dados):
    """Obtém o ID do subgrupo com mapeamento de tipos de cliente"""
    mapeamento_subgroup = {
        "Cliente ADM": "32",
        "Rastreio/TMK": "113",
        "Rastreio/Consulta": "133"
    }
    
    if 'subgroup_id' in dados and pd.notna(dados['subgroup_id']):
        valor = str(dados['subgroup_id']).strip()
        
        if valor in mapeamento_subgroup:
            id_retornado = mapeamento_subgroup[valor]
            logger.debug(f"Tipo de cliente '{valor}' mapeado para ID: {id_retornado}")
            return id_retornado
        
        logger.debug(f"Usando subgroup_id direto: {valor}")
        return valor
    
    return CONFIG["defaults"]["subgroup_id"]

def obter_empresa_input_position(dados):
    """Obtém a posição do input de empresa"""
    if 'empresa_input_position' in dados and pd.notna(dados['empresa_input_position']):
        try:
            posicao = int(dados['empresa_input_position'])
            if posicao < 0:
                logger.warning(f"empresa_input_position negativo ({posicao}), usando padrão")
                return CONFIG["defaults"]["empresa_input_position"]
            return posicao
        except ValueError:
            logger.warning(f"empresa_input_position inválido, usando padrão")
            return CONFIG["defaults"]["empresa_input_position"]
    
    return CONFIG["defaults"]["empresa_input_position"]

def validar_email(email):
    """
    Valida formato de email de forma mais permissiva
    Aceita números no início do local-part (antes do @)
    """
    # Pattern mais permissivo que aceita:
    # - Números, letras, pontos, underscores, hífens, mais e porcentagem antes do @
    # - Aceita números no início (ex: 53668.ana@callinksys.com.br)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_usuario(usuario):
    """
    Valida formato de nome de usuário de forma mais permissiva
    Aceita qualquer combinação de letras, números e símbolos comuns
    """
    # Pattern permissivo que aceita números no início e símbolos comuns
    # Mínimo 3 caracteres
    pattern = r'^[a-zA-Z0-9@._%+-]{3,}$'
    return re.match(pattern, usuario) is not None

def sanitizar_dados_usuario(dados):
    """
    Remove espaços e normaliza dados do usuário automaticamente
    Retorna uma cópia dos dados com valores limpos
    """
    dados_limpos = dados.copy()
    
    campos_para_limpar = ['usuario', 'email', 'nome', 'filtro_cliente', 
                          'loginGestor', 'emailGestor', 'loginGestor2', 'emailGestor2']
    
    for campo in campos_para_limpar:
        if campo in dados_limpos and pd.notna(dados_limpos[campo]):
            valor_original = str(dados_limpos[campo])
            valor_limpo = valor_original.strip()  # Remove espaços do início e fim
            
            if valor_original != valor_limpo:
                # Mostrar quantidade de espaços removidos
                espacos_inicio = len(valor_original) - len(valor_original.lstrip())
                espacos_fim = len(valor_original) - len(valor_original.rstrip())
                
                info_espacos = []
                if espacos_inicio > 0:
                    info_espacos.append(f"{espacos_inicio} espaço(s) no início")
                if espacos_fim > 0:
                    info_espacos.append(f"{espacos_fim} espaço(s) no fim")
                
                logger.info(f"🧹 Campo '{campo}' sanitizado ({', '.join(info_espacos)}): '{valor_limpo}'")
                dados_limpos[campo] = valor_limpo
    
    return dados_limpos

def validar_dados_usuario(dados):
    """Validação de business rules antes de processar"""
    usuario = dados.get('usuario', '')
    if not validar_usuario(usuario):
        raise ValueError(
            f"Usuário com formato inválido: '{usuario}'. "
            f"Use apenas letras, números e os símbolos: @ . _ % + - (mínimo 3 caracteres)"
        )
    
    email = dados.get('email', '')
    if not validar_email(email):
        raise ValueError(
            f"Email com formato inválido: '{email}'. "
            f"Formato esperado: exemplo@dominio.com"
        )

def validar_dados_planilha(df):
    """Valida estrutura e dados da planilha"""
    try:
        logger.info("Validando dados da planilha...")
        
        colunas_obrigatorias = ['nome', 'usuario', 'email', 'filtro_cliente']
        colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltando:
            raise Exception(f"Colunas obrigatórias faltando no Excel: {colunas_faltando}")
        
        # Validar dados linha por linha
        erros_validacao = []
        dados_sanitizados = 0
        
        for idx, linha in df.iterrows():
            # Sanitizar dados automaticamente
            linha_limpa = sanitizar_dados_usuario(linha)
            
            # Contar quantos campos foram sanitizados
            campos_alterados = 0
            for campo in ['usuario', 'email', 'nome', 'filtro_cliente']:
                if campo in linha and pd.notna(linha[campo]):
                    if str(linha[campo]) != str(linha_limpa[campo]):
                        campos_alterados += 1
            
            if campos_alterados > 0:
                dados_sanitizados += 1
            
            # Validar dados limpos
            try:
                validar_dados_usuario(linha_limpa)
            except ValueError as e:
                erro_msg = f"Linha {idx + 2}: {e}"  # +2 porque Excel começa em 1 e tem header
                erros_validacao.append(erro_msg)
                logger.warning(erro_msg)
        
        # Reportar sanitização
        if dados_sanitizados > 0:
            logger.info(f"🧹 {dados_sanitizados} linha(s) com espaços foram sanitizadas automaticamente")
        
        # Se houver muitos erros, reportar resumo
        if erros_validacao:
            logger.warning(f"⚠️  {len(erros_validacao)} linha(s) com problemas de validação")
            if len(erros_validacao) > 5:
                logger.warning("Primeiros 5 erros:")
                for erro in erros_validacao[:5]:
                    logger.warning(f"  {erro}")
                logger.warning(f"  ... e mais {len(erros_validacao) - 5} erros")
            else:
                for erro in erros_validacao:
                    logger.warning(f"  {erro}")
        
        colunas_opcionais = ['subgroup_id', 'empresa_input_position']
        
        for coluna in colunas_opcionais:
            if coluna in df.columns:
                valores_nao_nulos = df[df[coluna].notna()][coluna]
                
                if coluna == 'subgroup_id':
                    for idx, valor in valores_nao_nulos.items():
                        try:
                            str(valor)
                            logger.debug(f"Linha {idx + 2}: subgroup_id = {valor}")
                        except:
                            logger.warning(f"Linha {idx + 2}: subgroup_id inválido ({valor}), será usado valor padrão")
                
                elif coluna == 'empresa_input_position':
                    for idx, valor in valores_nao_nulos.items():
                        try:
                            int(valor)
                            if int(valor) < 0:
                                logger.warning(f"Linha {idx + 2}: empresa_input_position negativo ({valor}), será usado valor padrão")
                            else:
                                logger.debug(f"Linha {idx + 2}: empresa_input_position = {valor}")
                        except:
                            logger.warning(f"Linha {idx + 2}: empresa_input_position inválido ({valor}), será usado valor padrão")
            else:
                logger.info(f"Coluna '{coluna}' não encontrada, será usado valor padrão para todos os usuários")
        
        logger.info("✅ Validação da planilha concluída")
        
    except Exception as e:
        logger.error(f"Erro na validação da planilha: {e}")
        raise