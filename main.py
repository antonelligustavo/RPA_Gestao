# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys
from config import get_log_filename, CONFIG, EXCEL_FILE, LOGS_FOLDER
from automatizador import AutomatizadorGestao

# Obter nível de log da variável de ambiente (padrão: INFO)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

log_file = get_log_filename()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Função principal do automatizador"""
    try:
        logger.info("=" * 60)
        logger.info("AUTOMATIZADOR DE GESTÃO DE ACESSOS")
        logger.info("=" * 60)
        logger.info(f"Logs serão salvos em: {log_file}")
        logger.info(f"Pasta de logs: {LOGS_FOLDER}")
        logger.info(f"Nível de log: {LOG_LEVEL}")
        logger.info("")
        
        automatizador = AutomatizadorGestao()
        await automatizador.executar(EXCEL_FILE)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Processamento concluído com sucesso!")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"❌ Arquivo não encontrado: {e}")
        logger.error("Verifique se o arquivo 'usuarios.xlsx' está na pasta 'Arquivos'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro na execução principal: {e}")
        logger.exception("Detalhes do erro:")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Execução interrompida pelo usuário")
        sys.exit(0)