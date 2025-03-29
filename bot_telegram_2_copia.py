# -*- coding: utf-8 -*-
"""
Bot Telegram 2 para envio de sinais em canais.
Versão independente que não depende mais do Bot 1.
Os sinais serão enviados nos seguintes canais:
- Sala ChamaNaAlta: -1002658649212
- Sala do Np.bo: -1002538423500
- Minha sala: -1002317995059
O bot enviará 3 sinais por hora nos minutos 10, 30 e 50.
"""

# Importações necessárias
import traceback
import socket
import pytz
from datetime import datetime, timedelta, time as dt_time
import json
import random
import time
import schedule
import requests
import logging
import sys
import os
from functools import lru_cache

# Verificar disponibilidade do Pillow para manipulação de imagens
PIL_DISPONIVEL = False
try:
    from PIL import Image, ImageDraw
    PIL_DISPONIVEL = True
    logging.info("Biblioteca PIL (Pillow) disponível para manipulação de imagens.")
except ImportError:
    logging.warning("Biblioteca PIL (Pillow) não disponível. As imagens serão enviadas sem tratamento.")

# Configuração do logger específico para o Bot 2
BOT2_LOGGER = logging.getLogger('bot2')
BOT2_LOGGER.setLevel(logging.INFO)
bot2_formatter = logging.Formatter('%(asctime)s - BOT2 - %(levelname)s - %(message)s')

# Evitar duplicação de handlers
if not BOT2_LOGGER.handlers:
    bot2_file_handler = logging.FileHandler("bot_telegram_bot2_logs.log")
    bot2_file_handler.setFormatter(bot2_formatter)
    BOT2_LOGGER.addHandler(bot2_file_handler)

    bot2_console_handler = logging.StreamHandler()
    bot2_console_handler.setFormatter(bot2_formatter)
    BOT2_LOGGER.addHandler(bot2_console_handler)

# Credenciais Telegram
BOT2_TOKEN = '7997585882:AAFDyG-BYskj1gyAbh17X5jd6DDClXdluww'

# Configuração dos canais
BOT2_CANAIS_CONFIG = {
    "-1002658649212": {  # Sala ChamaNaAlta
        "idioma": "pt",
        "link_corretora": "https://trade.xxbroker.com/register?aff=751626&aff_model=revenue&afftrack="
    },
    "-1002538423500": {  # Sala do Np.bo
        "idioma": "pt",
        "link_corretora": "https://trade.xxbroker.com/register?aff=751924&aff_model=revenue&afftrack="
    },
    "-1002317995059": {  # Minha sala
        "idioma": "pt",
        "link_corretora": "https://trade.xxbroker.com/register?aff=751626&aff_model=revenue&afftrack="
    }
}

# Lista de IDs dos canais para facilitar iteração
BOT2_CHAT_IDS = list(BOT2_CANAIS_CONFIG.keys())

# ID para compatibilidade com código existente
BOT2_CHAT_ID_CORRETO = BOT2_CHAT_IDS[0]  # Usar o primeiro canal como padrão

# Limite de sinais por hora
BOT2_LIMITE_SINAIS_POR_HORA = 6

# Categorias dos ativos
ATIVOS_CATEGORIAS = {
    # Ativos Blitz
    "USD/BRL (OTC)": "Blitz",
    "USOUSD (OTC)": "Blitz",
    "BTC/USD (OTC)": "Blitz",
    "Google (OTC)": "Blitz",
    "EUR/JPY (OTC)": "Blitz",
    "ETH/USD (OTC)": "Blitz",
    "MELANIA Coin (OTC)": "Binary",
    "EUR/GBP (OTC)": "Blitz",
    "Apple (OTC)": "Blitz",
    "Amazon (OTC)": "Blitz",
    "TRUMP Coin (OTC)": "Binary",
    "Nike, Inc. (OTC)": "Blitz",
    "DOGECOIN (OTC)": "Blitz",
    "Tesla (OTC)": "Blitz",
    "SOL/USD (OTC)": "Blitz",
    "1000Sats (OTC)": "Binary",
    "XAUUSD (OTC)": "Digital",
    "McDonald´s Corporation (OTC)": "Blitz",
    "Meta (OTC)": "Blitz",
    "Coca-Cola Company (OTC)": "Blitz",
    "CARDANO (OTC)": "Blitz",
    "EUR/USD (OTC)": "Blitz",
    "PEN/USD (OTC)": "Blitz",
    "Bitcoin Cash (OTC)": "Binary",
    "AUD/CAD (OTC)": "Blitz",
    "Tesla/Ford (OTC)": "Blitz",
    "US 100 (OTC)": "Binary",
    "TRON/USD (OTC)": "Blitz",
    "USD/CAD (OTC)": "Blitz",
    "AUD/USD (OTC)": "Blitz",
    "AIG (OTC)": "Binary",
    "Alibaba Group Holding (OTC)": "Blitz",
    "Snap Inc. (OTC)": "Blitz",
    "US 500 (OTC)": "Digital",
    "AUD/CHF (OTC)": "Blitz",
    "Amazon/Alibaba (OTC)": "Blitz",
    "Pepe (OTC)": "Binary",
    "Chainlink (OTC)": "Binary",
    "USD/ZAR (OTC)": "Blitz",
    "Worldcoin (OTC)": "Binary",
    # Ativos Binary serão adicionados a seguir
    "Litecoin (OTC)": "Binary",
    "Injective (OTC)": "Binary",
    "ORDI (OTC)": "Binary",
    "ICP (OTC)": "Binary",
    "Cosmos (OTC)": "Binary",
    "Polkadot (OTC)": "Binary",
    "TON (OTC)": "Binary",
    "Celestia (OTC)": "Binary",
    "NEAR (OTC)": "Binary",
    "Ripple (OTC)": "Binary",
    "Ronin (OTC)": "Binary",
    "Stacks (OTC)": "Binary",
    "Immutable (OTC)": "Binary",
    "EOS (OTC)": "Binary",
    "Jupiter (OTC)": "Binary",
    "Polygon (OTC)": "Binary",
    "Arbitrum (OTC)": "Binary",
    "Sandbox (OTC)": "Binary",
    "Decentraland (OTC)": "Binary",
    "Sei (OTC)": "Binary",
    "IOTA (OTC)": "Binary",
    "Pyth (OTC)": "Binary",
    "Graph (OTC)": "Binary",
    "Floki (OTC)": "Binary",
    "Gala (OTC)": "Binary",
    "Bonk (OTC)": "Binary",
    "Beam (OTC)": "Binary",
    "Hamster Kombat (OTC)": "Binary",
    "NOT (OTC)": "Binary",
    "US 30 (OTC)": "Binary",
    "JP 225 (OTC)": "Binary",
    "HK 33 (OTC)": "Binary",
    "GER 30 (OTC)": "Binary",
    "SP 35 (OTC)": "Binary",
    "UK 100 (OTC)": "Binary",
    # Ativos Digital
    "EUR/THB (OTC)": "Digital",
    "JPY Currency Index": "Digital",
    "USD Currency Index": "Digital",
    "AUS 200 (OTC)": "Digital"
}

# Configurações de horários específicos para cada ativo
HORARIOS_PADRAO = {
    "USD/BRL_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-00:45", "01:15-23:59"],
        "Wednesday": ["00:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "USOUSD_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-23:59"],
        "Thursday": ["00:00-06:00", "06:30-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "BTC/USD_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "Google_OTC": {
        "Monday": ["00:00-15:30", "16:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-15:30", "16:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-15:30", "16:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "EUR/JPY_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-01:00", "01:15-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "ETH/USD_OTC": {
        "Monday": ["00:00-18:45", "19:15-23:59"],
        "Tuesday": ["00:00-18:45", "19:15-23:59"],
        "Wednesday": ["00:00-18:45", "19:15-23:59"],
        "Thursday": ["00:00-18:45", "19:15-23:59"],
        "Friday": ["00:00-18:45", "19:15-23:59"],
        "Saturday": ["00:00-18:45", "19:15-23:59"],
        "Sunday": ["00:00-18:45", "19:15-23:59"]
    },
    "MELANIA_COIN_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "EUR/GBP_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-01:00", "01:15-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "Apple_OTC": {
        "Monday": ["00:00-15:30", "16:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-15:30", "16:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-15:30", "16:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "Amazon_OTC": {
        "Monday": ["00:00-15:30", "16:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-15:30", "16:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-15:30", "16:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "TRUM_Coin_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "Nike_Inc_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "DOGECOIN_OTC": {
        "Monday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Tuesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Wednesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Thursday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Friday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Saturday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Sunday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"]
    },
    "Tesla_OTC": {
        "Monday": ["00:00-15:30", "16:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-15:30", "16:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-15:30", "16:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "SOL/USD_OTC": {
        "Monday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Tuesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Wednesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Thursday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Friday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Saturday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Sunday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"]
    },
    "1000Sats_OTC": {
        "Monday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Tuesday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Wednesday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Thursday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Friday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Saturday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Sunday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"]
    },
    "XAUUSD_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-23:59"],
        "Thursday": ["00:00-06:00", "06:30-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "McDonalds_Corporation_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "Meta_OTC": {
        "Monday": ["00:00-15:30", "16:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-15:30", "16:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-15:30", "16:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "Coca_Cola_Company_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "CARDANO_OTC": {
        "Monday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Tuesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Wednesday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Thursday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Friday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Saturday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"],
        "Sunday": ["00:00-05:45", "06:15-17:45", "18:15-23:59"]
    },
    "EUR/USD_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-01:00", "01:15-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "PEN/USD_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-00:45", "01:15-23:59"],
        "Wednesday": ["00:00-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "Bitcoin_Cash_OTC": {
        "Monday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Tuesday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Wednesday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Thursday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Friday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Saturday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"],
        "Sunday": ["00:00-05:05", "05:10-12:05", "12:10-23:59"]
    },
    "AUD/CAD_OTC": {
        "Monday": ["00:00-23:59"],
        "Tuesday": ["00:00-23:59"],
        "Wednesday": ["00:00-01:00", "01:15-23:59"],
        "Thursday": ["00:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-23:59"]
    },
    "Tesla/Ford_OTC": {
        "Monday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Tuesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Wednesday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Thursday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Friday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Saturday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"],
        "Sunday": ["00:00-05:00", "05:30-12:00", "12:30-23:59"]
    },
    "US_100_OTC": {
        "Monday": ["00:00-11:30", "12:00-17:30", "18:00-23:59"],
        "Tuesday": ["00:00-11:30", "12:00-17:30", "18:00-23:59"],
        "Wednesday": ["00:00-11:30", "12:00-17:30", "18:00-23:59"],
        "Thursday": ["00:00-11:30", "12:00-17:30", "18:00-23:59"],
        "Friday": ["00:00-23:59"],
        "Saturday": ["00:00-23:59"],
        "Sunday": ["00:00-11:30", "12:00-17:30", "18:00-23:59"]
    }
}

# Mapeamento de ativos para padrões de horários
assets = {
    "USD/BRL (OTC)": HORARIOS_PADRAO["USD/BRL_OTC"],
    "USOUSD (OTC)": HORARIOS_PADRAO["USOUSD_OTC"],
    "BTC/USD (OTC)": HORARIOS_PADRAO["BTC/USD_OTC"],
    "Google (OTC)": HORARIOS_PADRAO["Google_OTC"],
    "EUR/JPY (OTC)": HORARIOS_PADRAO["EUR/JPY_OTC"],
    "ETH/USD (OTC)": HORARIOS_PADRAO["ETH/USD_OTC"],
    "MELANIA Coin (OTC)": HORARIOS_PADRAO["MELANIA_COIN_OTC"],
    "EUR/GBP (OTC)": HORARIOS_PADRAO["EUR/GBP_OTC"],
    "Apple (OTC)": HORARIOS_PADRAO["Apple_OTC"],
    "Amazon (OTC)": HORARIOS_PADRAO["Amazon_OTC"],
    "TRUMP Coin (OTC)": HORARIOS_PADRAO["TRUM_Coin_OTC"],
    "Nike, Inc. (OTC)": HORARIOS_PADRAO["Nike_Inc_OTC"],
    "DOGECOIN (OTC)": HORARIOS_PADRAO["DOGECOIN_OTC"],
    "Tesla (OTC)": HORARIOS_PADRAO["Tesla_OTC"],
    "SOL/USD (OTC)": HORARIOS_PADRAO["SOL/USD_OTC"],
    "1000Sats (OTC)": HORARIOS_PADRAO["1000Sats_OTC"],
    "XAUUSD (OTC)": HORARIOS_PADRAO["XAUUSD_OTC"],
    "McDonalds Corporation (OTC)": HORARIOS_PADRAO["McDonalds_Corporation_OTC"],
    "Meta (OTC)": HORARIOS_PADRAO["Meta_OTC"],
    "Coca-Cola Company (OTC)": HORARIOS_PADRAO["Coca_Cola_Company_OTC"],
    "CARDANO (OTC)": HORARIOS_PADRAO["CARDANO_OTC"],
    "EUR/USD (OTC)": HORARIOS_PADRAO["EUR/USD_OTC"],
    "PEN/USD (OTC)": HORARIOS_PADRAO["PEN/USD_OTC"],
    "Bitcoin Cash (OTC)": HORARIOS_PADRAO["Bitcoin_Cash_OTC"],
    "AUD/CAD (OTC)": HORARIOS_PADRAO["AUD/CAD_OTC"],
    "Tesla/Ford (OTC)": HORARIOS_PADRAO["Tesla/Ford_OTC"],
    "US 100 (OTC)": HORARIOS_PADRAO["US_100_OTC"]
}

# Função para inicializar os horários dos ativos que não estão explicitamente mapeados
def inicializar_horarios_ativos():
    """
    Adiciona horários padrão para todos os ativos listados em ATIVOS_CATEGORIAS
    que não têm uma configuração específica em assets.
    """
    for ativo in ATIVOS_CATEGORIAS:
        if ativo not in assets:
            # Define horário padrão baseado na categoria do ativo
            categoria = ATIVOS_CATEGORIAS[ativo]
            if categoria == "Blitz":
                assets[ativo] = {
                    "Monday": ["00:00-23:59"],
                    "Tuesday": ["00:00-23:59"],
                    "Wednesday": ["00:00-23:59"],
                    "Thursday": ["00:00-23:59"],
                    "Friday": ["00:00-23:59"],
                    "Saturday": ["00:00-23:59"],
                    "Sunday": ["00:00-23:59"]
                }
            elif categoria == "Digital":
                assets[ativo] = {
                    "Monday": ["00:00-23:59"],
                    "Tuesday": ["00:00-23:59"],
                    "Wednesday": ["00:00-23:59"],
                    "Thursday": ["00:00-23:59"],
                    "Friday": ["00:00-23:59"],
                    "Saturday": ["00:00-23:59"],
                    "Sunday": ["00:00-23:59"]
                }
            else:  # Binary e outros
                assets[ativo] = {
                    "Monday": ["00:00-23:59"],
                    "Tuesday": ["00:00-23:59"],
                    "Wednesday": ["00:00-23:59"],
                    "Thursday": ["00:00-23:59"],
                    "Friday": ["00:00-23:59"],
                    "Saturday": ["00:00-23:59"],
                    "Sunday": ["00:00-23:59"]
                }

# Inicializa os horários dos ativos
inicializar_horarios_ativos()

# Lista de ativos disponíveis para negociação
ATIVOS_FORNECIDOS = list(ATIVOS_CATEGORIAS.keys())

# Categorias dos ativos do Bot 2 (usando as mesmas do Bot 1)
BOT2_ATIVOS_CATEGORIAS = ATIVOS_CATEGORIAS

# Mapeamento de ativos para padrões de horários do Bot 2 (usando os mesmos do Bot 1)
BOT2_ASSETS = assets

# Função para adicionar ativos
def adicionar_forex(lista_ativos):
    for ativo in lista_ativos:
        # Usar horário específico do ativo se disponível, senão usar horário genérico
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            # Criar um horário padrão para ativos sem configuração específica
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": [],
                "Sunday": []
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_otc(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": ["00:00-23:59"],
                "Sunday": ["00:00-23:59"]
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_digital(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": [],
                "Sunday": []
            }
        ATIVOS_CATEGORIAS[ativo] = "Digital"

def adicionar_digital_otc(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": ["00:00-23:59"],
                "Sunday": ["00:00-23:59"]
            }
        ATIVOS_CATEGORIAS[ativo] = "Digital"

def adicionar_crypto(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": ["00:00-23:59"],
                "Sunday": ["00:00-23:59"]
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_stocks(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["09:30-16:00"],
                "Tuesday": ["09:30-16:00"],
                "Wednesday": ["09:30-16:00"],
                "Thursday": ["09:30-16:00"],
                "Friday": ["09:30-16:00"],
                "Saturday": [],
                "Sunday": []
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_indices(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": ["00:00-23:59"],
                "Sunday": ["00:00-23:59"]
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_commodities(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": [],
                "Sunday": []
            }
        ATIVOS_CATEGORIAS[ativo] = "Binary"

def adicionar_blitz(lista_ativos):
    for ativo in lista_ativos:
        if ativo in HORARIOS_PADRAO:
            assets[ativo] = HORARIOS_PADRAO[ativo]
        else:
            assets[ativo] = {
                "Monday": ["00:00-23:59"],
                "Tuesday": ["00:00-23:59"],
                "Wednesday": ["00:00-23:59"],
                "Thursday": ["00:00-23:59"],
                "Friday": ["00:00-23:59"],
                "Saturday": ["00:00-23:59"],
                "Sunday": ["00:00-23:59"]
            }
        ATIVOS_CATEGORIAS[ativo] = "Blitz"

# Exemplos de como adicionar ativos (comentado para referência)
# adicionar_forex(["EUR/USD", "GBP/USD"])
# adicionar_crypto(["BTC/USD", "ETH/USD"])
# adicionar_stocks(["AAPL", "MSFT"])

# Função para parsear os horários
@lru_cache(maxsize=128)
def parse_time_range(time_str):
    """
    Converte uma string de intervalo de tempo (e.g. "09:30-16:00") para um par de time objects.
    """
    start_str, end_str = time_str.split('-')
    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()
    return start_time, end_time

# Função para verificar disponibilidade de ativos
def is_asset_available(asset, current_time=None, current_day=None):
    """
    Verifica se um ativo está disponível no horário atual.
    """
    if asset not in assets:
        return False

    if current_day not in assets[asset]:
        return False

    if not current_time:
        current_time = datetime.now().strftime("%H:%M")

    current_time_obj = datetime.strptime(current_time, "%H:%M").time()

    for time_range in assets[asset][current_day]:
        start_time, end_time = parse_time_range(time_range)
        if start_time <= current_time_obj <= end_time:
            return True

    return False

# Função para obter hora no fuso horário de Brasília (específica para Bot 2)
def bot2_obter_hora_brasilia():
    """
    Retorna a hora atual no fuso horário de Brasília.
    """
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_horario_brasilia)

def bot2_verificar_disponibilidade():
    """
    Verifica quais ativos estão disponíveis para o sinal atual.
    Retorna uma lista de ativos disponíveis.
    """
    agora = bot2_obter_hora_brasilia()
    current_time = agora.strftime("%H:%M")
    current_day = agora.strftime("%A")

    available_assets = [asset for asset in BOT2_ATIVOS_CATEGORIAS.keys()
                       if is_asset_available(asset, current_time, current_day)]

    return available_assets

def bot2_gerar_sinal_aleatorio():
    """
    Gera um sinal aleatório para enviar.
    Retorna um dicionário com os dados do sinal ou None se não houver sinal.
    """
    ativos_disponiveis = bot2_verificar_disponibilidade()
    if not ativos_disponiveis:
        return None

    ativo = random.choice(ativos_disponiveis)
    direcao = random.choice(['buy', 'sell'])
    categoria = BOT2_ATIVOS_CATEGORIAS.get(ativo, "Não categorizado")

    # Definir o tempo de expiração baseado na categoria
    if categoria == "Blitz":
        expiracao_segundos = random.choice([5, 10, 15, 30])
        tempo_expiracao_minutos = 1  # Fixo em 1 minuto para Blitz
        expiracao_texto = f"⏳ Expiração: {expiracao_segundos} segundos"

    elif categoria == "Digital":
        tempo_expiracao_minutos = random.choice([1, 3, 5])
        expiracao_time = bot2_obter_hora_brasilia() + timedelta(minutes=tempo_expiracao_minutos)
        if tempo_expiracao_minutos == 1:
            expiracao_texto = f"⏳ Expiração: 1 minuto ({expiracao_time.strftime('%H:%M')})"
        else:
            expiracao_texto = f"⏳ Expiração: {tempo_expiracao_minutos} minutos ({expiracao_time.strftime('%H:%M')})"
    elif categoria == "Binary":
        tempo_expiracao_minutos = 1
        expiracao_time = bot2_obter_hora_brasilia() + timedelta(minutes=tempo_expiracao_minutos)
        expiracao_texto = f"⏳ Expiração: 1 minuto ({expiracao_time.strftime('%H:%M')})"
    else:
        tempo_expiracao_minutos = 5
        expiracao_texto = "⏳ Expiração: até 5 minutos"

    return {
        'ativo': ativo,
        'direcao': direcao,
        'categoria': categoria,
        'expiracao_texto': expiracao_texto,
        'tempo_expiracao_minutos': int(tempo_expiracao_minutos)  # Garante que seja inteiro
    }

def bot2_formatar_mensagem(sinal, hora_formatada, idioma):
    """
    Formata a mensagem do sinal em português.
    Retorna a mensagem formatada.
    """
    ativo = sinal['ativo']
    direcao = sinal['direcao']
    categoria = sinal['categoria']
    tempo_expiracao_minutos = sinal['tempo_expiracao_minutos']

    # Debug: registrar os dados sendo usados para formatar a mensagem
    BOT2_LOGGER.info(f"Formatando mensagem com: ativo={ativo}, direção={direcao}, categoria={categoria}, tempo={tempo_expiracao_minutos}")

    # Formatação do nome do ativo para exibição
    nome_ativo_exibicao = ativo.replace("Digital_", "") if ativo.startswith("Digital_") else ativo
    if "(OTC)" in nome_ativo_exibicao and not " (OTC)" in nome_ativo_exibicao:
        nome_ativo_exibicao = nome_ativo_exibicao.replace("(OTC)", " (OTC)")

    # Configura ações e emojis conforme a direção
    action_pt = "COMPRA" if direcao == 'buy' else "VENDA"
    emoji = "🟢" if direcao == 'buy' else "🔴"

    # Hora de entrada convertida para datetime
    hora_entrada = datetime.strptime(hora_formatada, "%H:%M")
    hora_entrada = bot2_obter_hora_brasilia().replace(hour=hora_entrada.hour, minute=hora_entrada.minute, second=0, microsecond=0)
    
    # Determinar quantos minutos adicionar baseado no último dígito do minuto 
    ultimo_digito = hora_entrada.minute % 10
    if ultimo_digito == 3:
        minutos_adicionar = 2  # Se termina em 3, adiciona 2 minutos
    elif ultimo_digito == 7:
        minutos_adicionar = 3  # Se termina em 7, adiciona 3 minutos
    else:
        minutos_adicionar = 2  # Padrão: adiciona 2 minutos

    # Calcular horário de entrada
    hora_entrada_ajustada = hora_entrada + timedelta(minutes=minutos_adicionar)

    # Calcular horário de expiração (a partir do horário de entrada ajustado)
    hora_expiracao = hora_entrada_ajustada + timedelta(minutes=tempo_expiracao_minutos)

    # Calcular horários de reentrada
    # Reentrada 1: Expiração + 2 minutos
    hora_reentrada1 = hora_expiracao + timedelta(minutes=2)

    # Reentrada 2: Reentrada 1 + tempo_expiracao_minutos + 2 minutos
    hora_reentrada2 = hora_reentrada1 + timedelta(minutes=tempo_expiracao_minutos) + timedelta(minutes=2)

    # Formatação dos horários
    hora_entrada_formatada = hora_entrada_ajustada.strftime("%H:%M")
    hora_exp_formatada = hora_expiracao.strftime("%H:%M")
    hora_reentrada1_formatada = hora_reentrada1.strftime("%H:%M")
    hora_reentrada2_formatada = hora_reentrada2.strftime("%H:%M")

    # Texto de expiração
    expiracao_texto_pt = f"⏳ Expiração: {tempo_expiracao_minutos} minuto{'s' if tempo_expiracao_minutos > 1 else ''} ({hora_exp_formatada})"
    
    # Mensagem em PT
    mensagem_pt = (f"⚠️TRADE RÁPIDO⚠️\n\n"
            f"💵 Ativo: {nome_ativo_exibicao}\n"
            f"🏷️ Opções: {categoria}\n"
            f"{emoji} {action_pt}\n"
            f"➡ Entrada: {hora_entrada_formatada}\n"
            f"{expiracao_texto_pt}\n"
            f"Reentrada 1 - {hora_reentrada1_formatada}\n"
            f"Reentrada 2 - {hora_reentrada2_formatada}")
            
    BOT2_LOGGER.info(f"Mensagem formatada final: {mensagem_pt}")
    return mensagem_pt

def bot2_registrar_envio(ativo, direcao, categoria):
    """
    Registra o envio de um sinal no banco de dados.
    Implementação futura: Aqui você adicionaria o código para registrar o envio no banco de dados.
    """
    pass

# Inicialização do Bot 2 quando este arquivo for executado
bot2_sinais_agendados = False
bot2_contador_sinais = 0  # Contador para rastrear quantos sinais foram enviados

# URLs promocionais
XXBROKER_URL = "https://trade.xxbroker.com/register?aff=436564&aff_model=revenue&afftrack="
VIDEO_TELEGRAM_URL = "https://t.me/trendingbrazil/215"

# Diretórios para os vídeos
VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Subdiretórios para organizar os vídeos
VIDEOS_POS_SINAL_DIR = os.path.join(VIDEOS_DIR, "pos_sinal")
VIDEOS_ESPECIAL_DIR = os.path.join(VIDEOS_DIR, "especial")
VIDEOS_PROMO_DIR = os.path.join(VIDEOS_DIR, "promo")

# Criar apenas diretório para vídeos em português
VIDEOS_POS_SINAL_PT_DIR = os.path.join(VIDEOS_POS_SINAL_DIR, "pt")

# Atualização dos diretórios para os vídeos especiais apenas em português
VIDEOS_ESPECIAL_PT_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "pt")

# Criar os subdiretórios se não existirem
os.makedirs(VIDEOS_POS_SINAL_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_DIR, exist_ok=True)
os.makedirs(VIDEOS_PROMO_DIR, exist_ok=True)
os.makedirs(VIDEOS_POS_SINAL_PT_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_PT_DIR, exist_ok=True)

# Configurar vídeos apenas para português 
VIDEOS_POS_SINAL = {
    "pt": [
        os.path.join(VIDEOS_POS_SINAL_PT_DIR, "padrao.webp"),  # Sticker padrão em português (9/10)
        os.path.join(VIDEOS_POS_SINAL_PT_DIR, "especial.webp")  # Sticker especial em português (1/10)
    ]
}

# Vídeo especial a cada 3 sinais (apenas português)
VIDEOS_ESPECIAIS = {
    "pt": os.path.join(VIDEOS_ESPECIAL_PT_DIR, "especial.mp4")
}

# Vídeos promocionais apenas em português
VIDEOS_PROMO = {
    "pt": os.path.join(VIDEOS_PROMO_DIR, "pt.mp4")
}

# Vídeo GIF especial que vai ser enviado a cada 3 sinais
# Usar o mesmo arquivo do vídeo especial para evitar o erro "arquivo não encontrado"
VIDEO_GIF_ESPECIAL_PT = os.path.join(VIDEOS_ESPECIAL_PT_DIR, "especial.mp4")

# Contador para controle dos GIFs pós-sinal
contador_pos_sinal = 0
contador_desde_ultimo_especial = 0

# Função auxiliar para enviar vídeos com tamanho padronizado
def bot2_enviar_video_padronizado(video_path, chat_id, descricao="", horario_atual=None):
    """
    Função auxiliar para enviar vídeos com o tamanho padronizado.
    
    Args:
        video_path (str): Caminho do arquivo de vídeo
        chat_id (str): ID do chat destino
        descricao (str): Descrição do vídeo para logs
        horario_atual (str): Horário atual formatado, opcional
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    if not horario_atual:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
    
    if not os.path.exists(video_path):
        BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de vídeo não encontrado: {video_path}")
        return False
    
    try:
        # Utilizar a API sendVideo do Telegram
        url_base_video = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendVideo"
        
        with open(video_path, 'rb') as video_file:
            files = {
                'video': video_file
            }
            
            # Usar o tamanho renderizado correto: 217 × 85 px
            # E incluir metadados para tamanho intrínseco: 320 × 126 px
            payload_video = {
                'chat_id': chat_id,
                'parse_mode': 'HTML',
                'width': 217,         # Tamanho renderizado - largura
                'height': 85,         # Tamanho renderizado - altura
                'media_width': 320,   # Tamanho intrínseco - largura
                'media_height': 126   # Tamanho intrínseco - altura
            }
            
            resposta_video = requests.post(url_base_video, data=payload_video, files=files)
            
            if resposta_video.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo {descricao} para o canal {chat_id}: {resposta_video.text}")
                return False
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] Vídeo {descricao} ENVIADO COM SUCESSO para o canal {chat_id}, com dimensões: 217×85 (renderizado) e 320×126 (intrínseco)")
                return True
    
    except Exception as e:
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo {descricao}: {str(e)}")
        return False

# Função auxiliar para enviar stickers
def bot2_enviar_sticker(sticker_path, chat_id, descricao="", horario_atual=None):
    """
    Função auxiliar para enviar stickers.
    
    Args:
        sticker_path (str): Caminho do arquivo de sticker
        chat_id (str): ID do chat destino
        descricao (str): Descrição do sticker para logs
        horario_atual (str): Horário atual formatado, opcional
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    if not horario_atual:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
    
    # Verificar se o arquivo existe
    if not os.path.exists(sticker_path):
        BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de sticker não encontrado: {sticker_path}")
        
        # Tentar encontrar arquivo alternativo (diferentes extensões)
        alternativas = []
        base_path = os.path.splitext(sticker_path)[0]
        
        # Lista de possíveis extensões para tentar
        for ext in ['.webp', '.jpg', '.png', '.jpeg']:
            alt_path = f"{base_path}{ext}"
            if os.path.exists(alt_path):
                alternativas.append(alt_path)
                BOT2_LOGGER.info(f"[{horario_atual}] Encontrado arquivo alternativo: {alt_path}")
        
        if alternativas:
            # Usar o primeiro arquivo alternativo encontrado
            sticker_path = alternativas[0]
            BOT2_LOGGER.info(f"[{horario_atual}] Usando arquivo alternativo: {sticker_path}")
        else:
            # Tentar gerar um sticker automático
            nome_base = os.path.splitext(os.path.basename(sticker_path))[0]
            
            if "especial" in nome_base.lower():
                # Sticker especial - usar vermelho
                sticker_path = bot2_gerar_sticker_automatico(
                    nome=nome_base,
                    cor_base=(255, 0, 0),
                    cor_secundaria=(180, 0, 0),
                    texto="ESPECIAL"
                )
            else:
                # Sticker padrão - usar verde
                sticker_path = bot2_gerar_sticker_automatico(
                    nome=nome_base,
                    cor_base=(0, 180, 0),
                    cor_secundaria=(0, 120, 0),
                    texto="SINAL"
                )
            
            if not sticker_path:
                BOT2_LOGGER.error(f"[{horario_atual}] Não foi possível gerar sticker automático")
                return False
            
            BOT2_LOGGER.info(f"[{horario_atual}] Usando sticker gerado automaticamente: {sticker_path}")
    
    # Processar a imagem para garantir compatibilidade com stickers do Telegram
    sticker_path = bot2_otimizar_imagem_para_sticker(sticker_path, horario_atual)
    
    try:
        # Utilizar a API sendSticker do Telegram
        url_base_sticker = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendSticker"
        
        with open(sticker_path, 'rb') as sticker_file:
            files = {
                'sticker': sticker_file
            }
            
            # Configuração básica para enviar o sticker
            payload_sticker = {
                'chat_id': chat_id
                # Stickers não têm opções adicionais de tamanho
            }
            
            resposta_sticker = requests.post(url_base_sticker, data=payload_sticker, files=files)
            
            if resposta_sticker.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar sticker {descricao} para o canal {chat_id}: {resposta_sticker.text}")
                
                # Tentar enviar como foto em caso de erro com sticker
                if '.webp' in sticker_path.lower():
                    BOT2_LOGGER.warning(f"[{horario_atual}] Falha ao enviar como sticker. Tentando enviar como foto...")
                    
                    # Tentar converter para JPG se PIL estiver disponível
                    if PIL_DISPONIVEL:
                        try:
                            img = Image.open(sticker_path)
                            # Converter para RGB (remover transparência)
                            if img.mode == 'RGBA':
                                bg = Image.new('RGB', img.size, (255, 255, 255))
                                bg.paste(img, mask=img.split()[3])
                                img = bg
                            
                            # Salvar como JPG
                            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_stickers")
                            os.makedirs(temp_dir, exist_ok=True)
                            jpg_path = os.path.join(temp_dir, f"photo_{int(time.time())}.jpg")
                            img.save(jpg_path, 'JPEG')
                            img.close()
                            
                            # Enviar como foto
                            url_base_photo = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendPhoto"
                            with open(jpg_path, 'rb') as photo_file:
                                files_photo = {
                                    'photo': photo_file
                                }
                                payload_photo = {
                                    'chat_id': chat_id
                                }
                                resposta_photo = requests.post(url_base_photo, data=payload_photo, files=files_photo)
                                
                                if resposta_photo.status_code == 200:
                                    BOT2_LOGGER.info(f"[{horario_atual}] Sticker enviado como foto com sucesso para o canal {chat_id}")
                                    return True
                                else:
                                    BOT2_LOGGER.error(f"[{horario_atual}] Falha ao enviar como foto: {resposta_photo.text}")
                        except Exception as e:
                            BOT2_LOGGER.error(f"[{horario_atual}] Erro ao converter e enviar como foto: {str(e)}")
                
                return False
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] Sticker {descricao} ENVIADO COM SUCESSO para o canal {chat_id}")
                return True
    
    except Exception as e:
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar sticker {descricao}: {str(e)}")
        return False

# Função para enviar GIF pós-sinal
def bot2_enviar_gif_pos_sinal():
    """
    Envia um sticker após cada sinal.
    Escolhe entre dois stickers: o primeiro é enviado em 9 de 10 sinais, o segundo em 1 de 10 sinais.
    A escolha do sticker especial (segundo) é aleatória, garantindo apenas a proporção de 1 a cada 10.
    """
    global contador_pos_sinal, contador_desde_ultimo_especial
    
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO STICKER PÓS-SINAL...")
        
        # Incrementar os contadores
        contador_pos_sinal += 1
        contador_desde_ultimo_especial += 1
        
        # Decidir qual sticker enviar (9/10 o primeiro, 1/10 o segundo)
        escolha_sticker = 0  # Índice do primeiro sticker por padrão
        
        # Lógica para seleção aleatória do sticker especial
        if contador_desde_ultimo_especial >= 10:
            # Forçar o sticker especial se já passaram 10 sinais desde o último
            escolha_sticker = 1
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO O STICKER ESPECIAL (forçado após 10 sinais)")
            contador_desde_ultimo_especial = 0
        elif contador_desde_ultimo_especial > 1:
            # A probabilidade de enviar o sticker especial aumenta conforme
            # mais sinais passam sem que o especial seja enviado
            probabilidade = (contador_desde_ultimo_especial - 1) / 10.0
            if random.random() < probabilidade:
                escolha_sticker = 1
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO O STICKER ESPECIAL (aleatório com probabilidade {probabilidade:.2f})")
                contador_desde_ultimo_especial = 0
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO O STICKER PADRÃO (probabilidade de especial era {probabilidade:.2f})")
        else:
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO O STICKER PADRÃO (muito cedo para especial)")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Obter o caminho do sticker escolhido
            sticker_path = VIDEOS_POS_SINAL["pt"][escolha_sticker]
            tipo_sticker = "ESPECIAL (1/10)" if escolha_sticker == 1 else "PADRÃO (9/10)"
                
            BOT2_LOGGER.info(f"[{horario_atual}] Caminho do sticker escolhido: {sticker_path}")
            
            # Verificar se o arquivo existe e tentar alternativas
            if not os.path.exists(sticker_path):
                BOT2_LOGGER.warning(f"[{horario_atual}] Arquivo de sticker não encontrado: {sticker_path}")
                
                # Tentar diversos caminhos alternativos com diferentes extensões
                nome_arquivo = "especial" if escolha_sticker == 1 else "padrao"
                diretorios_possiveis = [
                    VIDEOS_POS_SINAL_PT_DIR,
                    VIDEOS_DIR,
                    os.path.dirname(os.path.abspath(__file__))
                ]
                
                # Extensões para tentar
                extensoes = ['.webp', '.jpg', '.jpeg', '.png']
                
                # Procurar por alternativas
                sticker_alternativo = None
                for diretorio in diretorios_possiveis:
                    for ext in extensoes:
                        caminho_tentativa = os.path.join(diretorio, f"{nome_arquivo}{ext}")
                        if os.path.exists(caminho_tentativa):
                            sticker_alternativo = caminho_tentativa
                            BOT2_LOGGER.info(f"[{horario_atual}] Encontrado sticker alternativo: {sticker_alternativo}")
                            break
                    if sticker_alternativo:
                        break
                
                if sticker_alternativo:
                    sticker_path = sticker_alternativo
                else:
                    BOT2_LOGGER.error(f"[{horario_atual}] Não foi possível encontrar nenhuma alternativa para o sticker")
            
            # Usar a função auxiliar para enviar o sticker
            descricao = f"PÓS-SINAL {tipo_sticker}"
            if bot2_enviar_sticker(sticker_path, chat_id, descricao, horario_atual):
                BOT2_LOGGER.info(f"[{horario_atual}] STICKER {descricao} enviado com sucesso para o canal {chat_id}")
            else:
                BOT2_LOGGER.error(f"[{horario_atual}] Falha ao enviar STICKER {descricao} para o canal {chat_id}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar sticker pós-sinal: {str(e)}")
        traceback.print_exc()

def bot2_enviar_promo_pre_sinal():
    """
    Envia uma mensagem promocional antes de cada sinal com vídeo.
    Esta função não é mais utilizada diretamente - foi dividida em bot2_enviar_video_pre_sinal e bot2_enviar_mensagem_pre_sinal.
    Mantida por compatibilidade.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] ATENÇÃO: A função bot2_enviar_promo_pre_sinal está obsoleta. Use as funções separadas.")
        
        # Chama as novas funções separadas
        bot2_enviar_video_pre_sinal()
        # Adiciona um pequeno delay para simular o comportamento anterior
        time.sleep(3)
        bot2_enviar_mensagem_pre_sinal()
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem promocional pré-sinal: {str(e)}")
        traceback.print_exc()

def bot2_enviar_promo_especial():
    """
    Envia uma mensagem promocional especial a cada 3 sinais enviados.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PROMOCIONAL ESPECIAL (A CADA 3 SINAIS) - Contador: {bot2_contador_sinais}...")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            link_corretora = config_canal["link_corretora"]
            
            # Preparar texto com link específico para cada canal
            texto_mensagem = (
                "Seguimos com as operações ✅\n\n"
                "Mantenham a corretora aberta!!\n\n\n"
                "Pra quem ainda não começou a ganhar dinheiro com a gente👇🏻\n\n"
                "🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n"
                f"➡️ <a href=\"{link_corretora}\">CLICANDO AQUI</a>"
            )
            
            # Obter o caminho do vídeo especial
            video_path = VIDEOS_ESPECIAIS["pt"]
            
            # Enviar vídeo especial usando a função auxiliar
            if os.path.exists(video_path):
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO VÍDEO ESPECIAL (A CADA 3 SINAIS) para o canal {chat_id}...")
                if bot2_enviar_video_padronizado(video_path, chat_id, "ESPECIAL (A CADA 3 SINAIS)", horario_atual):
                    BOT2_LOGGER.info(f"[{horario_atual}] VÍDEO ESPECIAL enviado com sucesso para o canal {chat_id}")
                else:
                    BOT2_LOGGER.error(f"[{horario_atual}] Falha ao enviar VÍDEO ESPECIAL para o canal {chat_id}")
            else:
                BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de vídeo especial não encontrado: {video_path}")
            
            # Enviar mensagem com links (agora incorporados diretamente no texto)
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM PROMOCIONAL ESPECIAL (A CADA 3 SINAIS) para o canal {chat_id}...")
            url_base_msg = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
            
            payload_msg = {
                'chat_id': chat_id,
                'text': texto_mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            resposta_msg = requests.post(url_base_msg, data=payload_msg)
            if resposta_msg.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem promocional especial para o canal {chat_id}: {resposta_msg.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM PROMOCIONAL ESPECIAL (A CADA 3 SINAIS) ENVIADA COM SUCESSO para o canal {chat_id}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem promocional especial: {str(e)}")
        traceback.print_exc()

# Função para enviar o GIF especial a cada 3 sinais para todos os canais.
def bot2_enviar_gif_especial_pt():
    """
    Envia um GIF especial a cada 3 sinais para todos os canais.
    Usa o mesmo arquivo de vídeo especial (especial.mp4) para garantir compatibilidade.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO GIF ESPECIAL (A CADA 3 SINAIS)...")
        
        # Garantir que a pasta existe
        if not os.path.exists(VIDEOS_ESPECIAL_PT_DIR):
            os.makedirs(VIDEOS_ESPECIAL_PT_DIR, exist_ok=True)
            BOT2_LOGGER.info(f"[{horario_atual}] Criada pasta para vídeos especiais: {VIDEOS_ESPECIAL_PT_DIR}")
        
        # Verificar se o arquivo existe
        if not os.path.exists(VIDEO_GIF_ESPECIAL_PT):
            BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de GIF especial não encontrado: {VIDEO_GIF_ESPECIAL_PT}")
            BOT2_LOGGER.info(f"[{horario_atual}] Tentando encontrar arquivos na pasta {VIDEOS_ESPECIAL_PT_DIR}: {os.listdir(VIDEOS_ESPECIAL_PT_DIR) if os.path.exists(VIDEOS_ESPECIAL_PT_DIR) else 'PASTA NÃO EXISTE'}")
            
            # Tentar usar o vídeo especial diretamente
            backup_video = os.path.join(VIDEOS_ESPECIAL_PT_DIR, "especial.mp4")
            if os.path.exists(backup_video):
                BOT2_LOGGER.info(f"[{horario_atual}] Usando arquivo de backup: {backup_video}")
                VIDEO_GIF_ESPECIAL_PT = backup_video
            else:
                BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de backup também não encontrado: {backup_video}")
                return
        
        # Enviar para todos os canais configurados
        for chat_id in BOT2_CHAT_IDS:
            BOT2_LOGGER.info(f"[{horario_atual}] Enviando GIF especial para o canal {chat_id}...")
            
            # Primeiro tentar com a função auxiliar padrão
            resultado = bot2_enviar_video_padronizado(VIDEO_GIF_ESPECIAL_PT, chat_id, "GIF ESPECIAL", horario_atual)
            
            # Se falhar, tentar o método alternativo (sendAnimation)
            if not resultado:
                BOT2_LOGGER.info(f"[{horario_atual}] Tentando método alternativo (sendAnimation) para o GIF especial...")
                try:
                    url_alt = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendAnimation"
                    with open(VIDEO_GIF_ESPECIAL_PT, 'rb') as alt_file:
                        files_alt = {'animation': alt_file}
                        payload_alt = {
                            'chat_id': chat_id,
                            'parse_mode': 'HTML',
                            'width': 217,             # Tamanho renderizado - largura
                            'height': 85,             # Tamanho renderizado - altura
                            'media_width': 320,       # Tamanho intrínseco - largura
                            'media_height': 126       # Tamanho intrínseco - altura
                        }
                        resp_alt = requests.post(url_alt, data=payload_alt, files=files_alt)
                        if resp_alt.status_code == 200:
                            BOT2_LOGGER.info(f"[{horario_atual}] GIF ESPECIAL ENVIADO COM SUCESSO via método alternativo para o canal {chat_id}, com dimensões: 217×85 (renderizado) e 320×126 (intrínseco)")
                        else:
                            BOT2_LOGGER.error(f"[{horario_atual}] Falha também no método alternativo: {resp_alt.text}")
                except Exception as e:
                    BOT2_LOGGER.error(f"[{horario_atual}] Erro no método alternativo: {str(e)}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial: {str(e)}")
        traceback.print_exc()

# Modificar a função bot2_send_message para alterar os tempos de agendamento
def bot2_send_message(ignorar_anti_duplicacao=False):
    global bot2_contador_sinais
    
    try:
        # Verifica se já enviou muito recentemente (anti-duplicação)
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO SINAL...")
        
        if not ignorar_anti_duplicacao and hasattr(bot2_send_message, 'ultimo_envio_timestamp'):
            ultimo_envio = bot2_send_message.ultimo_envio_timestamp
            diferenca = (agora - ultimo_envio).total_seconds()
            if diferenca < 60:  # Se a última mensagem foi enviada há menos de 1 minuto
                BOT2_LOGGER.info(f"[{horario_atual}] Anti-duplicação: Mensagem ignorada. Última enviada há {diferenca:.1f} segundos.")
                return

        # Atualiza o timestamp da última mensagem enviada para evitar duplicações
        bot2_send_message.ultimo_envio_timestamp = agora

        # Verifica se não excedeu o limite por hora
        hora_atual = agora.replace(minute=0, second=0, microsecond=0)
        if hora_atual not in bot2_send_message.contagem_por_hora:
            bot2_send_message.contagem_por_hora = {hora_atual: 0}

        if not ignorar_anti_duplicacao and bot2_send_message.contagem_por_hora[hora_atual] >= BOT2_LIMITE_SINAIS_POR_HORA:
            BOT2_LOGGER.info(f"[{horario_atual}] Limite de {BOT2_LIMITE_SINAIS_POR_HORA} sinais por hora atingido. Ignorando este sinal.")
            return

        # Gera um sinal aleatório para enviar
        sinal = bot2_gerar_sinal_aleatorio()
        if not sinal:
            BOT2_LOGGER.error(f"[{horario_atual}] Erro ao gerar sinal. Abortando envio.")
            return

        # Incrementa o contador de mensagens enviadas nesta hora
        bot2_send_message.contagem_por_hora[hora_atual] += 1

        # Registra a hora de geração do sinal
        BOT2_LOGGER.info(f"[{horario_atual}] SINAL GERADO. Enviando para todos os canais configurados...")

        # Obter dados do sinal
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        categoria = sinal['categoria']
        tempo_expiracao_minutos = sinal['tempo_expiracao_minutos']

        # Calcular horários para a operação
        hora_entrada = agora + timedelta(minutes=2)
        hora_expiracao = hora_entrada + timedelta(minutes=tempo_expiracao_minutos)
        hora_reentrada1 = hora_expiracao + timedelta(minutes=1)
        hora_reentrada2 = hora_reentrada1 + timedelta(minutes=tempo_expiracao_minutos)
        
        BOT2_LOGGER.info(f"[{horario_atual}] Detalhes do sinal: Ativo={ativo}, Direção={direcao}, Categoria={categoria}, Expiração={tempo_expiracao_minutos}min")
        BOT2_LOGGER.info(f"[{horario_atual}] Horários: Entrada={hora_entrada.strftime('%H:%M:%S')}, Expiração={hora_expiracao.strftime('%H:%M:%S')}, Reentrada1={hora_reentrada1.strftime('%H:%M:%S')}, Reentrada2={hora_reentrada2.strftime('%H:%M:%S')}")

        # Obtém a hora atual para formatação na mensagem
        hora_formatada = agora.strftime("%H:%M")

        # Loop para enviar a todos os canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal e link específico
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            link_corretora = config_canal["link_corretora"]

            # Formatar mensagem para português
            mensagem = bot2_formatar_mensagem(sinal, hora_formatada, "pt")
            
            # IMPORTANTE: Log detalhado do conteúdo exato da mensagem para debug
            BOT2_LOGGER.info(f"[{horario_atual}] CONTEÚDO EXATO DA MENSAGEM DO SINAL: {mensagem}")

            # Texto do botão em português
            texto_botao = "🔗 Abrir corretora"

            # Configura o teclado inline com o link específico da corretora para este canal
            teclado_inline = {
                "inline_keyboard": [
                    [
                        {
                            "text": texto_botao,
                            "url": link_corretora
                        }
                    ]
                ]
            }

            # Envia a mensagem para o canal
            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"

            payload = {
                'chat_id': chat_id,
                'text': mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
                'reply_markup': json.dumps(teclado_inline)
            }

            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM DO SINAL para o canal {chat_id}...")
            resposta = requests.post(url_base, data=payload)

            if resposta.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar sinal para o canal {chat_id}: {resposta.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM DO SINAL ENVIADA COM SUCESSO para o canal {chat_id}")

        # Registra estatísticas de envio
        bot2_registrar_envio(ativo, direcao, categoria)
        
        # Incrementa o contador global de sinais
        bot2_contador_sinais += 1
        BOT2_LOGGER.info(f"[{horario_atual}] Contador de sinais incrementado: {bot2_contador_sinais}")
        
        # Nova lógica de temporização otimizada para ciclo de 10 minutos:
        import threading
        
        # Agendar vídeo pós-sinal para 3 minutos após o sinal (reduzido de 5 para 3 minutos)
        timer_pos_sinal = threading.Timer(180.0, bot2_enviar_gif_pos_sinal)  # 180 segundos = 3 minutos
        timer_pos_sinal.start()
        BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio do VÍDEO PÓS-SINAL para daqui a 3 minutos...")
        
        # Verifica se é o terceiro sinal (divisível por 3) para iniciar a sequência especial
        if bot2_contador_sinais % 3 == 0:
            BOT2_LOGGER.info(f"[{horario_atual}] Este é o TERCEIRO SINAL da sequência (#{bot2_contador_sinais}). Agendando sequência especial...")
            
            # GIF especial PT 30 segundos após o vídeo pós-sinal (3:30 minutos após o sinal)
            timer_gif_especial = threading.Timer(210.0, bot2_enviar_gif_especial_pt)  # 180 + 30 = 210 segundos
            timer_gif_especial.start()
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio do GIF ESPECIAL PT para 3:30 minutos após o sinal...")
            
            # Mensagem promocional especial 3 segundos após o GIF (3:33 minutos após o sinal)
            timer_promo_especial = threading.Timer(213.0, bot2_enviar_promo_especial)  # 210 + 3 = 213 segundos
            timer_promo_especial.start()
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio da MENSAGEM PROMOCIONAL ESPECIAL para 3:33 minutos após o sinal...")
            
            # Vídeo pré-sinal 2 minutos após a mensagem promocional (5:33 minutos após o sinal)
            timer_video_pre_sinal = threading.Timer(333.0, lambda: bot2_enviar_video_pre_sinal())  # 213 + 120 = 333 segundos
            timer_video_pre_sinal.start()
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio do VÍDEO PRÉ-SINAL para 5:33 minutos após o sinal...")
            
            # Mensagem pré-sinal 3 segundos após o vídeo (5:36 minutos após o sinal)
            timer_msg_pre_sinal = threading.Timer(336.0, lambda: bot2_enviar_mensagem_pre_sinal())  # 333 + 3 = 336 segundos
            timer_msg_pre_sinal.start()
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio da MENSAGEM PRÉ-SINAL para 5:36 minutos após o sinal...")
            
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem: {str(e)}")
        traceback.print_exc()

# Função auxiliar para enviar apenas o vídeo pré-sinal
def bot2_enviar_video_pre_sinal():
    """
    Envia apenas o vídeo promocional pré-sinal.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO VÍDEO PRÉ-SINAL...")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Obter caminho do vídeo
            video_path = VIDEOS_PROMO.get("pt")
            
            # Usar a função auxiliar para enviar o vídeo padronizado
            if bot2_enviar_video_padronizado(video_path, chat_id, "PROMOCIONAL PRÉ-SINAL", horario_atual):
                BOT2_LOGGER.info(f"[{horario_atual}] VÍDEO PROMOCIONAL PRÉ-SINAL enviado com sucesso para o canal {chat_id}")
            else:
                BOT2_LOGGER.error(f"[{horario_atual}] Falha ao enviar VÍDEO PROMOCIONAL PRÉ-SINAL para o canal {chat_id}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo pré-sinal: {str(e)}")
        traceback.print_exc()

# Função auxiliar para enviar apenas a mensagem pré-sinal
def bot2_enviar_mensagem_pre_sinal():
    """
    Envia apenas a mensagem promocional pré-sinal.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PRÉ-SINAL...")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            link_corretora = config_canal["link_corretora"]
            
            # Preparar texto com o link específico para cada canal
            texto_mensagem = (
                "👉🏼Abram a corretora Pessoal\n\n"
                "⚠️FIQUEM ATENTOS⚠️\n\n"
                "🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n"
                f"➡️ <a href=\"{link_corretora}\">CLICANDO AQUI</a>"
            )
            
            # Enviar mensagem com link (agora incorporado diretamente no texto, não como botão)
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM PROMOCIONAL PRÉ-SINAL para o canal {chat_id}...")
            url_base_msg = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
            
            payload_msg = {
                'chat_id': chat_id,
                'text': texto_mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            resposta_msg = requests.post(url_base_msg, data=payload_msg)
            if resposta_msg.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem promocional para o canal {chat_id}: {resposta_msg.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM PROMOCIONAL PRÉ-SINAL ENVIADA COM SUCESSO para o canal {chat_id}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal: {str(e)}")
        traceback.print_exc()

# Inicializações para a função send_message
bot2_send_message.ultimo_envio_timestamp = bot2_obter_hora_brasilia()
bot2_send_message.contagem_por_hora = {bot2_obter_hora_brasilia().replace(minute=0, second=0, microsecond=0): 0}

def bot2_schedule_messages():
    """Agenda o envio de mensagens para o Bot 2."""
    try:
        # Verificar se já existe agendamento
        if hasattr(bot2_schedule_messages, 'scheduled'):
            BOT2_LOGGER.info("Agendamentos já existentes. Pulando...")
            return

        BOT2_LOGGER.info("Iniciando agendamento de mensagens para o Bot 2")

        # Agendar envio de sinais a cada 10 minutos (00, 10, 20, 30, 40, 50)
        for hora in range(24):
            # Minutos 00, 10, 20, 30, 40, 50
            for minuto in [0, 10, 20, 30, 40, 50]:
                # Agendar o sinal principal
                schedule.every().day.at(f"{hora:02d}:{minuto:02d}:02").do(bot2_send_message)
                
                BOT2_LOGGER.info(f"Sinal agendado para {hora:02d}:{minuto:02d}:02")

        # Marcar como agendado
        bot2_schedule_messages.scheduled = True

        BOT2_LOGGER.info("Agendamento de mensagens do Bot 2 concluído com sucesso")
        BOT2_LOGGER.info("Sinais agendados a cada 10 minutos: XX:00, XX:10, XX:20, XX:30, XX:40, XX:50")

    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao agendar mensagens do Bot 2: {str(e)}")
        traceback.print_exc()

def bot2_testar_envio_promocional():
    """
    Função para testar o envio das mensagens promocionais e vídeos.
    """
    BOT2_LOGGER.info("Iniciando teste de avisos pré-sinais...")
    
    # Testar mensagem promocional pré-sinal
    BOT2_LOGGER.info("Testando envio de mensagem promocional pré-sinal...")
    bot2_enviar_promo_pre_sinal()
    
    # Agendar o teste de envio do sinal para 30 segundos depois
    BOT2_LOGGER.info("Agendando teste de envio do sinal para 30 segundos depois...")
    import threading
    timer_sinal = threading.Timer(30.0, lambda: bot2_send_message(ignorar_anti_duplicacao=True))
    timer_sinal.start()
    
    BOT2_LOGGER.info("Iniciando operação normal do Bot 2...")

# Função para testar toda a sequência de sinais imediatamente
def bot2_testar_sequencia_completa():
    """
    Função para testar toda a sequência de sinais conforme a nova temporização para ciclo de 10min:
    1. Sinal
    2. Vídeo pós-sinal (3 minutos depois)
    3. GIF especial PT (3:30 minutos após o sinal)
    4. Mensagem promocional especial (3:33 minutos após o sinal)
    5. Vídeo pré-sinal (5:33 minutos após o sinal)
    6. Mensagem pré-sinal (5:36 minutos após o sinal)
    """
    BOT2_LOGGER.info("TESTE COMPLETO: Iniciando teste da sequência completa (nova temporização para ciclo de 10min)...")
    
    # Ajuste os tempos para teste (acelerados para facilitar o teste)
    # Em um teste real, os tempos seriam muito longos para esperar
    tempo_aceleracao = 0.1  # Fator de aceleração (0.1 = 10x mais rápido)
    
    # Função para executar cada etapa da sequência
    def executar_etapa(etapa, func, delay_segundos=0):
        delay_ajustado = delay_segundos * tempo_aceleracao
        BOT2_LOGGER.info(f"TESTE COMPLETO: Etapa {etapa} será executada em {delay_ajustado:.1f} segundos (original: {delay_segundos}s)...")
        if delay_segundos > 0:
            import threading
            timer = threading.Timer(delay_ajustado, func)
            timer.start()
        else:
            func()
    
    # Etapa 1: Enviar o sinal
    executar_etapa(1, lambda: bot2_send_message(ignorar_anti_duplicacao=True), 0)
    
    # Etapa 2: Enviar vídeo pós-sinal após 3 minutos (acelerado)
    executar_etapa(2, lambda: bot2_enviar_gif_pos_sinal(), 180)
    
    # Etapa 3: Enviar GIF especial PT após 3:30 minutos (acelerado)
    executar_etapa(3, lambda: bot2_enviar_gif_especial_pt(), 210)
    
    # Etapa 4: Enviar mensagem promocional especial após 3:33 minutos (acelerado)
    executar_etapa(4, lambda: bot2_enviar_promo_especial(), 213)
    
    # Etapa 5: Enviar vídeo pré-sinal após 5:33 minutos (acelerado)
    executar_etapa(5, lambda: bot2_enviar_video_pre_sinal(), 333)
    
    # Etapa 6: Enviar mensagem pré-sinal após 5:36 minutos (acelerado)
    executar_etapa(6, lambda: bot2_enviar_mensagem_pre_sinal(), 336)
    
    BOT2_LOGGER.info(f"TESTE COMPLETO: Sequência de teste agendada com sucesso! (Aceleração: {tempo_aceleracao:.1f}x)")
    BOT2_LOGGER.info(f"TESTE COMPLETO: A sequência completa levará aproximadamente {336 * tempo_aceleracao:.1f} segundos.")
    
    # Força o contador de sinais para simular o terceiro sinal
    global bot2_contador_sinais
    bot2_contador_sinais = 3

# Modificar a função de inicialização para não executar a sequência de teste
def iniciar_ambos_bots():
    """
    Inicializa ambos os bots quando executado como script principal.
    """
    # Não executar o teste, iniciar o bot normalmente
    # bot2_testar_sequencia_completa()  # Comentado para executar normalmente
    
    # Inicializar o Bot 1 (original)
    try:
        logging.info("Inicializando Bot 1...")
        # Verifica se já existe uma instância do bot rodando
        if is_bot_already_running():
            logging.error("O bot já está rodando em outra instância. Encerrando...")
            sys.exit(1)
        schedule_messages()      # Função original do bot 1
    except Exception as e:
        logging.error(f"Erro ao inicializar Bot 1: {str(e)}")
    
    # Inicializar o Bot 2
    try:
        BOT2_LOGGER.info("Inicializando Bot 2 em modo normal...")
        bot2_schedule_messages()  # Agendar mensagens nos horários normais
        bot2_keep_bot_running()  # Chamada direta para a função do Bot 2
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao inicializar Bot 2: {str(e)}")
    
    logging.info("Ambos os bots estão em execução!")
    BOT2_LOGGER.info("Ambos os bots estão em execução em modo normal!")
    
    # Loop principal para verificar os agendamentos
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Erro no loop principal: {str(e)}")
            BOT2_LOGGER.error(f"Erro no loop principal: {str(e)}")
            time.sleep(5)  # Pausa maior em caso de erro

# Função para verificar se o bot já está em execução
def is_bot_already_running():
    """
    Verifica se já existe uma instância do bot em execução usando um socket.
    """
    try:
        # Tenta criar um socket em uma porta específica
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 9876))  # Porta arbitrária para verificação
        return False
    except socket.error:
        # Se a porta estiver em uso, assume que o bot está rodando
        return True

# Função original do Bot 1 (implementação mínima para compatibilidade)
def schedule_messages():
    """
    Função de compatibilidade com o Bot 1 original.
    Esta implementação é um placeholder e não realiza agendamentos reais.
    """
    logging.info("Função schedule_messages() do Bot 1 chamada (sem efeito)")
    pass

# Função para manter o Bot 2 em execução
def bot2_keep_bot_running():
    """
    Mantém o Bot 2 em execução, verificando os agendamentos.
    """
    BOT2_LOGGER.info("Iniciando função keep_bot_running do Bot 2")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        BOT2_LOGGER.error(f"Erro na função keep_bot_running do Bot 2: {str(e)}")
        traceback.print_exc()

# Executar se este arquivo for o script principal
if __name__ == "__main__":
    iniciar_ambos_bots()

# Função para gerar automaticamente um sticker/imagem
def bot2_gerar_sticker_automatico(nome="auto_sticker", cor_base=(255, 0, 0), cor_secundaria=None, texto=None):
    """
    Gera automaticamente um sticker quando não for possível encontrar o arquivo original.
    
    Args:
        nome (str): Nome base para o arquivo gerado
        cor_base (tuple): Cor base RGB (r, g, b)
        cor_secundaria (tuple): Cor secundária para gradiente, opcional
        texto (str): Texto a ser incluído no sticker, opcional
        
    Returns:
        str: Caminho do sticker gerado ou None em caso de falha
    """
    if not PIL_DISPONIVEL:
        BOT2_LOGGER.error("Não é possível gerar sticker: PIL não disponível")
        return None
    
    try:
        # Criar diretório para stickers automáticos
        auto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_stickers")
        os.makedirs(auto_dir, exist_ok=True)
        
        # Caminho do arquivo a ser gerado
        output_path = os.path.join(auto_dir, f"{nome}_{int(time.time())}.webp")
        
        # Criar imagem base (512x512 é o tamanho padrão para stickers)
        img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Desenhar um retângulo com gradiente ou cor única
        if cor_secundaria:
            # Implementação simples de gradiente linear
            for y in range(512):
                # Calcular a cor para esta linha (interpolação linear)
                fator = y / 512.0
                r = int(cor_base[0] * (1 - fator) + cor_secundaria[0] * fator)
                g = int(cor_base[1] * (1 - fator) + cor_secundaria[1] * fator)
                b = int(cor_base[2] * (1 - fator) + cor_secundaria[2] * fator)
                
                # Desenhar uma linha horizontal com esta cor
                draw.line([(0, y), (511, y)], fill=(r, g, b, 255))
        else:
            # Cor única
            draw.rectangle([(0, 0), (511, 511)], fill=cor_base)
        
        # Adicionar texto se fornecido
        if texto and PIL_DISPONIVEL:
            try:
                # Tentar importar o módulo ImageFont
                from PIL import ImageFont
                
                # Usar fonte padrão se disponível
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    font = ImageFont.load_default()
                
                # Calcular posição do texto (centro)
                text_width, text_height = draw.textbbox((0, 0), texto, font=font)[2:4]
                position = ((512 - text_width) // 2, (512 - text_height) // 2)
                
                # Desenhar texto
                draw.text(position, texto, fill=(255, 255, 255, 255), font=font)
                
            except Exception as e:
                BOT2_LOGGER.error(f"Erro ao adicionar texto ao sticker: {str(e)}")
        
        # Salvar imagem no formato webp
        img.save(output_path, 'WEBP')
        BOT2_LOGGER.info(f"Sticker gerado automaticamente: {output_path}")
        
        return output_path
    
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao gerar sticker automático: {str(e)}")
        return None

# Função auxiliar para processar e otimizar imagem para sticker
def bot2_otimizar_imagem_para_sticker(imagem_path, horario_atual=None):
    """
    Processa uma imagem para garantir que esteja otimizada para uso como sticker no Telegram.
    
    Args:
        imagem_path (str): Caminho da imagem a ser otimizada
        horario_atual (str): Horário atual formatado para logs
        
    Returns:
        str: Caminho da imagem otimizada (pode ser o mesmo da entrada) ou None em caso de falha
    """
    if not horario_atual:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
    
    if not PIL_DISPONIVEL:
        BOT2_LOGGER.warning(f"[{horario_atual}] Não é possível otimizar a imagem: PIL não disponível.")
        return imagem_path  # Retorna a mesma imagem sem processamento
    
    try:
        # Criar diretório para stickers processados
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_stickers")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Abrir a imagem
        img = Image.open(imagem_path)
        nome_base = os.path.splitext(os.path.basename(imagem_path))[0]
        
        # Verificar formato da imagem
        precisa_converter = img.format not in ['WEBP']
        
        # Verificar dimensões
        width, height = img.size
        precisa_redimensionar = width > 512 or height > 512
        
        # Se não precisar de alterações, retorna o caminho original
        if not precisa_converter and not precisa_redimensionar:
            img.close()
            return imagem_path
        
        # Redimensionar se necessário
        if precisa_redimensionar:
            BOT2_LOGGER.info(f"[{horario_atual}] Redimensionando imagem de {width}x{height} para max 512x512")
            
            # Calcular proporção para manter aspecto
            ratio = min(512 / width, 512 / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Redimensionar
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Salvar imagem processada como webp
        output_path = os.path.join(temp_dir, f"proc_{nome_base}_{int(time.time())}.webp")
        img.save(output_path, 'WEBP')
        BOT2_LOGGER.info(f"[{horario_atual}] Imagem otimizada para sticker: {output_path}")
        
        img.close()
        return output_path
        
    except Exception as e:
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao otimizar imagem para sticker: {str(e)}")
        return imagem_path  # Em caso de erro, retorna a imagem original
