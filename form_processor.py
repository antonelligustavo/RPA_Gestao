# -*- coding: utf-8 -*-
import asyncio
import logging
import pandas as pd
from config import CONFIG
from utils import encontrar_frame, aguardar_elemento, aguardar_elemento_com_polling, obter_subgroup_id, obter_empresa_input_position

logger = logging.getLogger(__name__)

async def selecionar_opcao_robusta(frame, seletor, valor_desejado, nome_campo="campo"):
    """
    Seleciona opção de um select de forma robusta, tratando valores com espaços
    e tentando métodos alternativos
    """
    try:
        logger.debug(f"Tentando selecionar '{valor_desejado}' no {nome_campo}")
        
        # Aguardar o select estar disponível
        await frame.wait_for_selector(seletor, state="visible", timeout=10000)
        await asyncio.sleep(0.5)
        
        # Obter todas as opções disponíveis
        opcoes_disponiveis = await frame.evaluate("""
            (selector) => {
                const select = document.querySelector(selector);
                if (!select) return null;
                return Array.from(select.options).map(opt => ({
                    value: opt.value,
                    text: opt.text,
                    index: opt.index
                }));
            }
        """, seletor)
        
        if not opcoes_disponiveis:
            raise Exception(f"Não foi possível obter opções do select {nome_campo}")
        
        logger.debug(f"Opções disponíveis em {nome_campo}: {opcoes_disponiveis}")
        
        # Tentar encontrar o valor exato
        opcao_encontrada = None
        valor_limpo = valor_desejado.strip()
        
        # 1. Tentar match exato
        for opcao in opcoes_disponiveis:
            if opcao['value'] == valor_desejado:
                opcao_encontrada = opcao
                logger.debug(f"Match exato encontrado: {opcao}")
                break
        
        # 2. Tentar match com trim
        if not opcao_encontrada:
            for opcao in opcoes_disponiveis:
                if opcao['value'].strip() == valor_limpo:
                    opcao_encontrada = opcao
                    logger.debug(f"Match com trim encontrado: {opcao}")
                    break
        
        # 3. Tentar match por texto
        if not opcao_encontrada:
            for opcao in opcoes_disponiveis:
                if valor_limpo.lower() in opcao['text'].lower():
                    opcao_encontrada = opcao
                    logger.debug(f"Match por texto encontrado: {opcao}")
                    break
        
        # 4. Se ainda não encontrou, usar primeira opção válida (índice 1, pular opção vazia)
        if not opcao_encontrada:
            logger.warning(f"Valor '{valor_desejado}' não encontrado em {nome_campo}, usando primeira opção válida")
            for opcao in opcoes_disponiveis:
                if opcao['index'] > 0 and opcao['value']:  # Pular opção vazia (índice 0)
                    opcao_encontrada = opcao
                    logger.info(f"Usando opção padrão: {opcao}")
                    break
        
        if not opcao_encontrada:
            raise Exception(f"Nenhuma opção válida encontrada em {nome_campo}. Opções: {opcoes_disponiveis}")
        
        # Tentar selecionar usando diferentes métodos
        valor_final = opcao_encontrada['value']
        
        # Método 1: select_option padrão
        try:
            logger.debug(f"Método 1: Tentando select_option com valor '{valor_final}'")
            await frame.select_option(seletor, valor_final, timeout=5000)
            logger.debug(f"✅ {nome_campo} selecionado com sucesso (método 1)")
            return True
        except Exception as e1:
            logger.warning(f"Método 1 falhou: {e1}")
        
        # Método 2: JavaScript setValue
        try:
            logger.debug(f"Método 2: Tentando JavaScript setValue")
            await frame.evaluate("""
                (selector, value) => {
                    const select = document.querySelector(selector);
                    if (select) {
                        select.value = value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        select.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            """, seletor, valor_final)
            
            # Verificar se foi selecionado
            await asyncio.sleep(0.3)
            valor_selecionado = await frame.evaluate(f"document.querySelector('{seletor}').value")
            if valor_selecionado == valor_final:
                logger.debug(f"✅ {nome_campo} selecionado com sucesso (método 2)")
                return True
            else:
                raise Exception(f"Valor não foi aplicado corretamente")
        except Exception as e2:
            logger.warning(f"Método 2 falhou: {e2}")
        
        # Método 3: Selecionar por índice
        try:
            logger.debug(f"Método 3: Tentando selecionar por índice {opcao_encontrada['index']}")
            await frame.evaluate("""
                (selector, index) => {
                    const select = document.querySelector(selector);
                    if (select && select.options[index]) {
                        select.selectedIndex = index;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        select.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            """, seletor, opcao_encontrada['index'])
            
            await asyncio.sleep(0.3)
            indice_selecionado = await frame.evaluate(f"document.querySelector('{seletor}').selectedIndex")
            if indice_selecionado == opcao_encontrada['index']:
                logger.debug(f"✅ {nome_campo} selecionado com sucesso (método 3)")
                return True
        except Exception as e3:
            logger.warning(f"Método 3 falhou: {e3}")
        
        raise Exception(f"Todos os métodos de seleção falharam para {nome_campo}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao selecionar {nome_campo}: {e}")
        raise

async def configurar_grupo(page, dados):
    """Configura o grupo/subgrupo do usuário"""
    try:
        logger.debug("Configurando grupo...")
        
        target_frame = await encontrar_frame(page, "usuarios_incluiGrupo.do")
        
        subgroup_id = obter_subgroup_id(dados)
        logger.debug(f"Usando subgroup_id: {subgroup_id}")
        
        # Usar função robusta para selecionar
        await selecionar_opcao_robusta(
            target_frame, 
            CONFIG["selectors"]["subgroup_select"], 
            subgroup_id,
            "subgrupo"
        )
        
        logger.debug("Grupo configurado com sucesso")
        return target_frame
        
    except Exception as e:
        logger.error(f"Erro na configuração do grupo: {e}")
        raise

async def preencher_dados_usuario(frame, dados):
    """Preenche os dados do usuário no formulário"""
    try:
        logger.debug(f"Preenchendo dados do usuário: {dados.get('usuario', 'N/A')}")
        
        # Campos opcionais de gestor
        if 'loginGestor' in dados and pd.notna(dados['loginGestor']):
            await frame.fill(CONFIG["selectors"]["login_gestor"], str(dados["loginGestor"]))
        
        if 'emailGestor' in dados and pd.notna(dados['emailGestor']):
            await frame.fill(CONFIG["selectors"]["email_gestor"], str(dados["emailGestor"]))
        
        if 'loginGestor2' in dados and pd.notna(dados['loginGestor2']):
            await frame.fill(CONFIG["selectors"]["login_gestor2"], str(dados["loginGestor2"]))
        
        if 'emailGestor2' in dados and pd.notna(dados['emailGestor2']):
            await frame.fill(CONFIG["selectors"]["email_gestor2"], str(dados["emailGestor2"]))
        
        # Campos obrigatórios
        campos_obrigatorios = ['nome', 'usuario', 'email', 'filtro_cliente']
        
        for campo in campos_obrigatorios:
            if campo not in dados or pd.isna(dados[campo]):
                raise Exception(f"Campo obrigatório '{campo}' não encontrado ou vazio")
            
            seletor = CONFIG["selectors"][campo]
            valor = str(dados[campo])
            await frame.fill(seletor, valor)
        
        await frame.fill(CONFIG["selectors"]["obs"], CONFIG["values"]["obs_text"])
        
        logger.debug("Dados do usuário preenchidos com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no preenchimento dos dados: {e}")
        raise

async def configurar_selects(frame):
    """Configura os campos select do formulário usando método robusto"""
    try:
        logger.debug("Configurando campos select...")
        
        # Tipo de Pessoa
        await selecionar_opcao_robusta(
            frame,
            CONFIG["selectors"]["tipo_pes_select"],
            CONFIG["values"]["tipo_pes_id"],
            "tipo_pes"
        )
        
        # Cargo
        await selecionar_opcao_robusta(
            frame,
            CONFIG["selectors"]["cargo_select"],
            CONFIG["values"]["cargo_id"],
            "cargo"
        )
        
        # Setor
        await selecionar_opcao_robusta(
            frame,
            CONFIG["selectors"]["setor_select"],
            CONFIG["values"]["setor_id"],
            "setor"
        )
        
        logger.debug("✅ Todos os campos select configurados com sucesso")
        
    except Exception as e:
        logger.error(f"Erro na configuração dos selects: {e}")
        raise

async def finalizar_cadastro(frame, dados):
    """Finaliza o cadastro do usuário"""
    try:
        logger.debug("Finalizando cadastro...")
        
        await frame.click(CONFIG["selectors"]["lupa_button"])
        
        # Aguardar o elemento empresa_input com timeout estendido e retry
        logger.debug("Aguardando elemento empresa_input aparecer...")
        
        # Primeira tentativa com a função melhorada
        elemento_encontrado = await aguardar_elemento(frame, CONFIG["selectors"]["empresa_input"], timeout=15000)
        
        if not elemento_encontrado:
            logger.warning("Elemento empresa_input não encontrado com método padrão, tentando polling...")
            # Tentativa com polling manual
            elemento_encontrado = await aguardar_elemento_com_polling(frame, CONFIG["selectors"]["empresa_input"], timeout=20000)
        
        if elemento_encontrado:
            logger.debug("Elemento empresa_input encontrado, prosseguindo...")
            inputs = frame.locator(CONFIG["selectors"]["empresa_input"])
            
            # Aguardar carregamento completo
            await frame.wait_for_load_state("networkidle")
            
            # Verificar se os inputs estão disponíveis
            try:
                count = await inputs.count()
                logger.debug(f"Encontrados {count} inputs de empresa")
                
                if count > 0:
                    posicao_input = obter_empresa_input_position(dados)
                    logger.debug(f"Usando empresa_input_position: {posicao_input}")
                    
                    # Garantir que a posição não excede o número de inputs disponíveis
                    if posicao_input >= count:
                        logger.warning(f"Posição {posicao_input} excede número de inputs ({count}), usando posição 0")
                        posicao_input = 0
                    
                    # Aguardar o input específico ficar visível
                    input_especifico = inputs.nth(posicao_input)
                    await input_especifico.wait_for(state="visible", timeout=5000)
                    
                    await input_especifico.click()
                    logger.debug(f"Clique realizado no input de empresa na posição {posicao_input}")
                else:
                    logger.error("Nenhum input de empresa encontrado")
                    raise Exception("Nenhum input de empresa disponível")
                    
            except Exception as input_error:
                logger.error(f"Erro ao processar inputs de empresa: {input_error}")
                raise
        else:
            logger.error("Elemento empresa_input não foi encontrado após todas as tentativas")
            raise Exception("Timeout crítico: elemento empresa_input não encontrado")
        
        await asyncio.sleep(0.5)
        
        # Executar checkAll() com tratamento de erro
        try:
            await frame.evaluate("checkAll()")
            logger.debug("Função checkAll() executada")
        except Exception as check_error:
            logger.warning(f"Erro ao executar checkAll(): {check_error}")
            # Tentar método alternativo se checkAll() falhar
            try:
                await frame.evaluate("document.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => cb.checked = true)")
                logger.debug("Checkboxes marcados via método alternativo")
            except Exception as alt_error:
                logger.warning(f"Método alternativo para checkboxes também falhou: {alt_error}")
        
        await frame.click(CONFIG["selectors"]["submit_button"])
        
        # Aguardar um pouco para processar
        await asyncio.sleep(1)
        
        logger.debug("Cadastro finalizado")
        
        # Retornar o frame para verificação posterior
        return frame
        
    except Exception as e:
        logger.error(f"Erro na finalização do cadastro: {e}")
        raise