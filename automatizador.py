# -*- coding: utf-8 -*-
import asyncio
import pandas as pd
import logging
import os
import json
import time
from datetime import datetime
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

from config import get_report_filename, get_report_txt_filename
from utils import verificar_sessao_ativa, validar_dados_planilha, obter_subgroup_id, obter_empresa_input_position, sanitizar_dados_usuario, verificar_usuario_ja_cadastrado
from navigation import fazer_login, navegar_para_incluir_acesso, voltar_para_gestao_acesso
from form_processor import configurar_grupo, preencher_dados_usuario, configurar_selects, finalizar_cadastro

logger = logging.getLogger(__name__)

@asynccontextmanager
async def medir_tempo(operacao):
    """Context manager para medir tempo de operações"""
    inicio = time.time()
    try:
        yield
    finally:
        duracao = time.time() - inicio
        logger.info(f"⏱️  {operacao}: {duracao:.2f}s")

class AutomatizadorGestao:
    def __init__(self):
        self.stats = {
            "total": 0,
            "sucessos": 0,
            "erros": 0,
            "ja_existentes": 0,
            "usuarios_erro": [],
            "tempo_total": 0,
            "inicio_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    async def verificar_usuario_existente(self, frame, usuario):
        """Verifica se usuário já existe no sistema (previne duplicação)"""
        try:
            logger.debug(f"Verificando se usuário '{usuario}' já existe...")
            
            # Adaptar conforme o sistema - este é um exemplo genérico
            # Se o sistema tiver uma busca específica, use-a aqui
            
            # Exemplo: se houver campo de filtro por usuário
            # await frame.fill('#filtro_usuario', usuario)
            # await frame.click('#buscar')
            # await asyncio.sleep(1)
            # resultados = await frame.locator('.resultado-busca').count()
            # return resultados > 0
            
            # Por enquanto, retorna False (não implementado)
            return False
            
        except Exception as e:
            logger.warning(f"Não foi possível verificar existência de '{usuario}': {e}")
            return False

    async def processar_usuario(self, page, dados, frame_inicial):
        """Processa um único usuário"""
        # SANITIZAR DADOS ANTES DE PROCESSAR
        dados = sanitizar_dados_usuario(dados)
        
        usuario = dados.get('usuario', 'USUARIO_DESCONHECIDO')
        
        try:
            async with medir_tempo(f"Processamento de {usuario}"):
                logger.info(f"Iniciando processamento do usuário: {usuario}")
                
                subgroup_id = obter_subgroup_id(dados)
                empresa_position = obter_empresa_input_position(dados)
                logger.info(f"Usuário {usuario} - Tipo de Cliente: {subgroup_id}, Slot do Cliente: {empresa_position}")
                
                if not await verificar_sessao_ativa(page):
                    logger.warning("Sessão não está ativa, tentando relogar...")
                    frame_inicial = await fazer_login(page)
                
                frame_acesso = await navegar_para_incluir_acesso(page, frame_inicial)
                
                frame_grupo = await configurar_grupo(page, dados)
                
                await preencher_dados_usuario(frame_grupo, dados)
                
                await configurar_selects(frame_grupo)
                
                frame_final = await finalizar_cadastro(frame_grupo, dados)
                
                # VERIFICAR SE USUÁRIO JÁ ESTAVA CADASTRADO
                if await verificar_usuario_ja_cadastrado(page):
                    logger.warning(f"⚠️  Usuário {usuario} já estava cadastrado no sistema")
                    self.stats["ja_existentes"] += 1
                    # Ainda assim, voltar ao menu para continuar processamento
                    await voltar_para_gestao_acesso(page, frame_inicial)
                    return True
                
                await voltar_para_gestao_acesso(page, frame_inicial)
                
                logger.info(f"✅ Usuário {usuario} criado com sucesso!")
                self.stats["sucessos"] += 1
                
                return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar usuário {usuario}: {e}")
            self.stats["erros"] += 1
            self.stats["usuarios_erro"].append({
                "usuario": usuario,
                "erro": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return False

    async def gerar_relatorio(self):
        """Gera relatórios em JSON e texto"""
        self.stats["tempo_total"] = time.time() - self.tempo_inicio
        self.stats["fim_execucao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info("=" * 60)
        logger.info("RELATÓRIO FINAL DE EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Total de usuários processados: {self.stats['total']}")
        logger.info(f"✅ Sucessos: {self.stats['sucessos']}")
        logger.info(f"❌ Erros: {self.stats['erros']}")
        logger.info(f"⚠️  Já existentes: {self.stats['ja_existentes']}")
        
        if self.stats['total'] > 0:
            taxa_sucesso = (self.stats['sucessos'] / self.stats['total'] * 100)
            logger.info(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        logger.info(f"⏱️  Tempo total de execução: {self.stats['tempo_total']:.2f}s")
        
        if self.stats["usuarios_erro"]:
            logger.info("\n❌ Usuários com erro:")
            for erro in self.stats["usuarios_erro"]:
                logger.info(f"  - {erro['usuario']}: {erro['erro']}")
        
        # Salvar relatório JSON
        relatorio_json = get_report_filename()
        with open(relatorio_json, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        logger.info(f"\n📄 Relatório JSON salvo em: {relatorio_json}")
        
        # Salvar relatório texto
        relatorio_txt = get_report_txt_filename()
        with open(relatorio_txt, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RELATÓRIO DE EXECUÇÃO - AUTOMATIZADOR GESTÃO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Início: {self.stats['inicio_execucao']}\n")
            f.write(f"Fim: {self.stats['fim_execucao']}\n")
            f.write(f"Tempo total: {self.stats['tempo_total']:.2f}s\n\n")
            f.write(f"Total processados: {self.stats['total']}\n")
            f.write(f"✅ Sucessos: {self.stats['sucessos']}\n")
            f.write(f"❌ Erros: {self.stats['erros']}\n")
            f.write(f"⚠️  Já existentes: {self.stats['ja_existentes']}\n")
            
            if self.stats['total'] > 0:
                taxa_sucesso = (self.stats['sucessos'] / self.stats['total'] * 100)
                f.write(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%\n\n")
            
            if self.stats["usuarios_erro"]:
                f.write("\n" + "=" * 60 + "\n")
                f.write("USUÁRIOS COM ERRO\n")
                f.write("=" * 60 + "\n\n")
                for erro in self.stats["usuarios_erro"]:
                    f.write(f"Usuário: {erro['usuario']}\n")
                    f.write(f"Erro: {erro['erro']}\n")
                    f.write(f"Horário: {erro['timestamp']}\n")
                    f.write("-" * 60 + "\n")
        
        logger.info(f"📄 Relatório TXT salvo em: {relatorio_txt}")

    async def executar(self, arquivo_excel):
        """Executa o processo completo de automação"""
        browser = None
        self.tempo_inicio = time.time()
        
        try:
            if not os.path.exists(arquivo_excel):
                raise FileNotFoundError(f"Arquivo Excel não encontrado: {arquivo_excel}")
            
            logger.info(f"Carregando dados do arquivo: {arquivo_excel}")
            df = pd.read_excel(arquivo_excel)
            
            if df.empty:
                raise Exception("Arquivo Excel está vazio")
            
            self.stats["total"] = len(df)
            logger.info(f"Carregados {len(df)} usuários para processamento")
            
            validar_dados_planilha(df)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                try:
                    page = await browser.new_page()
                    
                    logger.info("Fazendo login inicial...")
                    frame_inicial = await fazer_login(page)
                    
                    for idx, linha in df.iterrows():
                        logger.info(f"\n{'='*60}")
                        logger.info(f"Processando usuário {idx + 1}/{len(df)}")
                        logger.info(f"{'='*60}")
                        
                        try:
                            await self.processar_usuario(page, linha, frame_inicial)
                            
                            # Pequena pausa entre usuários
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Erro crítico no processamento do usuário {idx + 1}: {e}")
                            self.stats["erros"] += 1
                            self.stats["usuarios_erro"].append({
                                "usuario": linha.get('usuario', f'Linha_{idx + 1}'),
                                "erro": f"Erro crítico: {str(e)}",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                
                finally:
                    # Garantir fechamento do browser
                    if browser:
                        await browser.close()
                        logger.info("Browser fechado com sucesso")
            
            await self.gerar_relatorio()
            
        except Exception as e:
            logger.error(f"Erro crítico na execução: {e}")
            raise
        finally:
            # Garantir que relatório é gerado mesmo com erro
            if self.stats["total"] > 0:
                try:
                    await self.gerar_relatorio()
                except:
                    pass