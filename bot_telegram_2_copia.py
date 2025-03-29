# -*- coding: utf-8 -*-
"""
Bot Telegram 2 para envio de sinais em canais separados por idioma.
Versão independente que não depende mais do Bot 1.
Os sinais serão enviados da seguinte forma:
- Canal Português: -1002424874613
- Canal Inglês: -1002453956387
- Canal Espanhol: -1002446547846
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

# Configuração dos canais para cada idioma
BOT2_CANAIS_CONFIG = {
    "-1002424874613": {  # Canal para mensagens em português
        "idioma": "pt",
        "link_corretora": "https://trade.xxbroker.com/register?aff=436564&aff_model=revenue&afftrack="
    },
    "-1002453956387": {  # Canal para mensagens em inglês
        "idioma": "en",
        "link_corretora": "https://trade.xxbroker.com/register?aff=436564&aff_model=revenue&afftrack="
    },
    "-1002446547846": {  # Canal para mensagens em espanhol
        "idioma": "es",
        "link_corretora": "https://trade.xxbroker.com/register?aff=436564&aff_model=revenue&afftrack="
    }
}

# Lista de IDs dos canais para facilitar iteração
BOT2_CHAT_IDS = list(BOT2_CANAIS_CONFIG.keys())

# ID para compatibilidade com código existente
BOT2_CHAT_ID_CORRETO = BOT2_CHAT_IDS[0]  # Usar o primeiro canal como padrão

# Limite de sinais por hora
BOT2_LIMITE_SINAIS_POR_HORA = 3

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
    Formata a mensagem do sinal para o idioma especificado.
    Retorna a mensagem formatada no idioma correto (pt, en ou es).
    """
    ativo = sinal['ativo']
    direcao = sinal['direcao']
    categoria = sinal['categoria']
    tempo_expiracao_minutos = sinal['tempo_expiracao_minutos']

    # Debug: registrar os dados sendo usados para formatar a mensagem
    BOT2_LOGGER.info(f"Formatando mensagem com: ativo={ativo}, direção={direcao}, categoria={categoria}, tempo={tempo_expiracao_minutos}, idioma={idioma}")

    # Formatação do nome do ativo para exibição
    nome_ativo_exibicao = ativo.replace("Digital_", "") if ativo.startswith("Digital_") else ativo
    if "(OTC)" in nome_ativo_exibicao and not " (OTC)" in nome_ativo_exibicao:
        nome_ativo_exibicao = nome_ativo_exibicao.replace("(OTC)", " (OTC)")

    # Configura ações e emojis conforme a direção
    action_pt = "COMPRA" if direcao == 'buy' else "VENDA"
    action_en = "BUY" if direcao == 'buy' else "SELL"
    action_es = "COMPRA" if direcao == 'buy' else "VENTA"
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

    # Textos de expiração em diferentes idiomas
    expiracao_texto_pt = f"⏳ Expiração: {tempo_expiracao_minutos} minuto{'s' if tempo_expiracao_minutos > 1 else ''} ({hora_exp_formatada})"
    expiracao_texto_en = f"⏳ Expiration: {tempo_expiracao_minutos} minute{'s' if tempo_expiracao_minutos > 1 else ''} ({hora_exp_formatada})"
    expiracao_texto_es = f"⏳ Expiración: {tempo_expiracao_minutos} minuto{'s' if tempo_expiracao_minutos > 1 else ''} ({hora_exp_formatada})"
    
    # Mensagem em PT
    mensagem_pt = (f"⚠️TRADE RÁPIDO⚠️\n\n"
            f"💵 Ativo: {nome_ativo_exibicao}\n"
            f"🏷️ Opções: {categoria}\n"
            f"{emoji} {action_pt}\n"
            f"➡ Entrada: {hora_entrada_formatada}\n"
            f"{expiracao_texto_pt}\n"
            f"Reentrada 1 - {hora_reentrada1_formatada}\n"
            f"Reentrada 2 - {hora_reentrada2_formatada}")
            
    # Mensagem em EN
    mensagem_en = (f"⚠️QUICK TRADE⚠️\n\n"
            f"💵 Asset: {nome_ativo_exibicao}\n"
            f"🏷️ Options: {categoria}\n"
            f"{emoji} {action_en}\n"
            f"➡ Entry: {hora_entrada_formatada}\n"
            f"{expiracao_texto_en}\n"
            f"Re-entry 1 - {hora_reentrada1_formatada}\n"
            f"Re-entry 2 - {hora_reentrada2_formatada}")
            
    # Mensagem em ES
    mensagem_es = (f"⚠️COMERCIO RÁPIDO⚠️\n\n"
            f"💵 Activo: {nome_ativo_exibicao}\n"
            f"🏷️ Opciones: {categoria}\n"
            f"{emoji} {action_es}\n"
            f"➡ Entrada: {hora_entrada_formatada}\n"
            f"{expiracao_texto_es}\n"
            f"Reentrada 1 - {hora_reentrada1_formatada}\n"
            f"Reentrada 2 - {hora_reentrada2_formatada}")
            
    # Verificar se há algum texto não esperado antes de retornar a mensagem
    if idioma == "pt":
        mensagem_final = mensagem_pt
    elif idioma == "en":
        mensagem_final = mensagem_en
    elif idioma == "es":
        mensagem_final = mensagem_es
    else:  # Padrão para qualquer outro idioma (português)
        mensagem_final = mensagem_pt
        
    BOT2_LOGGER.info(f"Mensagem formatada final para idioma {idioma}: {mensagem_final}")
    return mensagem_final

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

# Base directory para os arquivos do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definindo diretórios para os vídeos
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Subdiretórios para organizar os vídeos
VIDEOS_POS_SINAL_DIR = os.path.join(VIDEOS_DIR, "pos_sinal")
VIDEOS_PROMO_DIR = os.path.join(VIDEOS_DIR, "promo")
VIDEOS_ESPECIAL_DIR = os.path.join(VIDEOS_DIR, "gif_especial")  # Alterado de "especial" para "gif_especial"

# Criar os subdiretórios se não existirem
os.makedirs(VIDEOS_POS_SINAL_DIR, exist_ok=True)
os.makedirs(VIDEOS_PROMO_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_DIR, exist_ok=True)

# Diretórios para vídeos pós-sinal em cada idioma
VIDEOS_POS_SINAL_PT_DIR = os.path.join(VIDEOS_POS_SINAL_DIR, "pt")
VIDEOS_POS_SINAL_EN_DIR = os.path.join(VIDEOS_POS_SINAL_DIR, "en")
VIDEOS_POS_SINAL_ES_DIR = os.path.join(VIDEOS_POS_SINAL_DIR, "es")

# Diretórios para vídeos especiais em cada idioma
VIDEOS_ESPECIAL_PT_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "pt")
VIDEOS_ESPECIAL_EN_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "en")
VIDEOS_ESPECIAL_ES_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "es")

# Criar os subdiretórios para cada idioma se não existirem
os.makedirs(VIDEOS_POS_SINAL_PT_DIR, exist_ok=True)
os.makedirs(VIDEOS_POS_SINAL_EN_DIR, exist_ok=True)
os.makedirs(VIDEOS_POS_SINAL_ES_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_PT_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_EN_DIR, exist_ok=True)
os.makedirs(VIDEOS_ESPECIAL_ES_DIR, exist_ok=True)

# Configurar vídeos pós-sinal específicos para cada idioma 
VIDEOS_POS_SINAL = {
    "pt": [
        os.path.join(VIDEOS_POS_SINAL_PT_DIR, "padrão.mp4"),  # Vídeo padrão em português (9/10)
        os.path.join(VIDEOS_POS_SINAL_PT_DIR, "especial.mp4")  # Vídeo especial em português (1/10)
    ],
    "en": [
        os.path.join(VIDEOS_POS_SINAL_EN_DIR, "padrao.mp4"),  # Vídeo padrão em inglês (9/10)
        os.path.join(VIDEOS_POS_SINAL_EN_DIR, "especial.mp4")  # Vídeo especial em inglês (1/10)
    ],
    "es": [
        os.path.join(VIDEOS_POS_SINAL_ES_DIR, "padrao.mp4"),  # Vídeo padrão em espanhol (9/10)
        os.path.join(VIDEOS_POS_SINAL_ES_DIR, "especial.mp4")  # Vídeo especial em espanhol (1/10)
    ]
}

# Vídeo especial a cada 3 sinais (por idioma)
VIDEOS_ESPECIAIS = {
    "pt": os.path.join(VIDEOS_ESPECIAL_PT_DIR, "especial.mp4"),
    "en": os.path.join(VIDEOS_ESPECIAL_EN_DIR, "especial.mp4"),
    "es": os.path.join(VIDEOS_ESPECIAL_ES_DIR, "especial.mp4")
}

# Vídeos promocionais por idioma
VIDEOS_PROMO = {
    "pt": os.path.join(VIDEOS_PROMO_DIR, "pt.mp4"),
    "en": os.path.join(VIDEOS_PROMO_DIR, "en.mp4"),
    "es": os.path.join(VIDEOS_PROMO_DIR, "es.mp4")
}

# Diretórios para vídeos especiais em cada idioma
VIDEOS_ESPECIAL_PT_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "pt")
VIDEOS_ESPECIAL_EN_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "en")
VIDEOS_ESPECIAL_ES_DIR = os.path.join(VIDEOS_ESPECIAL_DIR, "es")

# Logs para diagnóstico
print(f"VIDEOS_DIR: {VIDEOS_DIR}")
print(f"VIDEOS_ESPECIAL_DIR: {VIDEOS_ESPECIAL_DIR}")
print(f"VIDEOS_ESPECIAL_PT_DIR: {VIDEOS_ESPECIAL_PT_DIR}")

# Caminho para o vídeo do GIF especial PT
VIDEO_GIF_ESPECIAL_PT = os.path.join(VIDEOS_ESPECIAL_PT_DIR, "especial.mp4")
print(f"VIDEO_GIF_ESPECIAL_PT: {VIDEO_GIF_ESPECIAL_PT}")

# Contador para controle dos GIFs pós-sinal
contador_pos_sinal = 0
contador_desde_ultimo_especial = 0

# Função para enviar GIF pós-sinal (1 minuto após cada sinal)
def bot2_enviar_gif_pos_sinal():
    """
    Envia uma imagem após o sinal.
    Esta função é chamada 5 minutos após cada sinal.
    """
    global contador_pos_sinal
    global contador_desde_ultimo_especial
    
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA IMAGEM PÓS-SINAL...")
        
        # Importar biblioteca para processamento de imagens
        try:
            from PIL import Image
            import io
            pil_available = True
            BOT2_LOGGER.info(f"[{horario_atual}] Biblioteca PIL (Pillow) disponível para processamento de imagem")
        except ImportError:
            pil_available = False
            BOT2_LOGGER.warning(f"[{horario_atual}] Biblioteca PIL (Pillow) não disponível. As imagens serão enviadas sem tratamento.")
        
        # Incrementar o contador de envios pós-sinal
        contador_pos_sinal += 1
        contador_desde_ultimo_especial += 1
        
        BOT2_LOGGER.info(f"[{horario_atual}] Contador pós-sinal: {contador_pos_sinal}, Contador desde último especial: {contador_desde_ultimo_especial}")
        
        # Decidir qual imagem enviar (9/10 a primeira, 1/10 a segunda)
        escolha_imagem = 0  # Índice da primeira imagem por padrão
        
        # Lógica para seleção aleatória da imagem especial
        if contador_desde_ultimo_especial >= 10:
            # Forçar a imagem especial se já passaram 10 sinais desde o último
            escolha_imagem = 1
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO A IMAGEM ESPECIAL (forçado após 10 sinais)")
            contador_desde_ultimo_especial = 0
        elif contador_desde_ultimo_especial > 1:
            # A probabilidade de enviar a imagem especial aumenta conforme
            # mais sinais passam sem que o especial seja enviado
            probabilidade = (contador_desde_ultimo_especial - 1) / 10.0
            if random.random() < probabilidade:
                escolha_imagem = 1
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO A IMAGEM ESPECIAL (aleatório com probabilidade {probabilidade:.2f})")
                contador_desde_ultimo_especial = 0
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO A IMAGEM PADRÃO (probabilidade de especial era {probabilidade:.2f})")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal.get("idioma", "pt")  # Usar português como padrão
            
            # Nomes dos arquivos (padronizados sem acentos)
            nome_padrao = "padrao"
            nome_especial = "especial"
            
            # Verificar todos os formatos possíveis para as imagens
            formatos = [".webp", ".png", ".jpg", ".jpeg"]
            
            # Determinar qual imagem enviar com base no idioma
            imagem_selecionada = None
            nome_arquivo = nome_padrao if escolha_imagem == 0 else nome_especial
            
            # Tentar encontrar o arquivo no formato correto
            for formato in formatos:
                caminho = os.path.join(VIDEOS_POS_SINAL_DIR, idioma, f"{nome_arquivo}{formato}")
                if os.path.exists(caminho):
                    imagem_selecionada = caminho
                    BOT2_LOGGER.info(f"[{horario_atual}] Encontrada imagem: {caminho}")
                    break
            
            # Se não encontrou, tentar com acento (para compatibilidade)
            if not imagem_selecionada and nome_arquivo == "padrao":
                for formato in formatos:
                    caminho = os.path.join(VIDEOS_POS_SINAL_DIR, idioma, f"padrão{formato}")
                    if os.path.exists(caminho):
                        imagem_selecionada = caminho
                        BOT2_LOGGER.info(f"[{horario_atual}] Encontrada imagem com acento: {caminho}")
                        break
            
            # Se ainda não encontrou, tentar usar português como fallback
            if not imagem_selecionada and idioma != "pt":
                for formato in formatos:
                    fallback_path = os.path.join(VIDEOS_POS_SINAL_DIR, "pt", f"{nome_arquivo}{formato}")
                    if os.path.exists(fallback_path):
                        imagem_selecionada = fallback_path
                        BOT2_LOGGER.info(f"[{horario_atual}] Usando fallback em português: {fallback_path}")
                        break
                
                # Tentar com acento também para o fallback
                if not imagem_selecionada and nome_arquivo == "padrao":
                    for formato in formatos:
                        fallback_path = os.path.join(VIDEOS_POS_SINAL_DIR, "pt", f"padrão{formato}")
                        if os.path.exists(fallback_path):
                            imagem_selecionada = fallback_path
                            BOT2_LOGGER.info(f"[{horario_atual}] Usando fallback em português com acento: {fallback_path}")
                            break
            
            # Se não encontrou nenhuma imagem, pular este canal
            if not imagem_selecionada:
                BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Não foi possível encontrar nenhuma imagem para o canal {chat_id}")
                continue
            
            imagem_path = imagem_selecionada
            BOT2_LOGGER.info(f"[{horario_atual}] Enviando imagem pós-sinal para o canal {chat_id} no idioma {idioma}: {imagem_path}")
            
            # Verificar o tipo de arquivo
            is_webp = imagem_path.lower().endswith('.webp')
            is_png = imagem_path.lower().endswith('.png')
            is_transparent = is_webp or is_png  # Webp e PNG podem ter transparência
            
            # Parâmetros básicos para todos os envios
            params = {
                'chat_id': chat_id,
                'disable_notification': False
            }
            
            envio_sucesso = False
            
            # Primeiro tentar enviar como sticker se for webp ou png (para preservar transparência)
            if is_transparent and pil_available:
                BOT2_LOGGER.info(f"[{horario_atual}] Detectada imagem com possível transparência, tentando enviar como sticker")
                
                # Tentar enviar como sticker
                with open(imagem_path, 'rb') as sticker_file:
                    try:
                        url_sticker = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendSticker"
                        files = {'sticker': sticker_file}
                        sticker_response = requests.post(url_sticker, data=params, files=files)
                        
                        if sticker_response.status_code == 200:
                            BOT2_LOGGER.info(f"[{horario_atual}] IMAGEM ENVIADA COMO STICKER com transparência preservada")
                            envio_sucesso = True
                        else:
                            BOT2_LOGGER.warning(f"[{horario_atual}] Não foi possível enviar como sticker: {sticker_response.text}")
                    except Exception as sticker_error:
                        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao tentar enviar como sticker: {str(sticker_error)}")
            
            # Se não conseguiu enviar como sticker, tentar como documento
            if not envio_sucesso and is_transparent and pil_available:
                with open(imagem_path, 'rb') as doc_file:
                    try:
                        url_doc = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendDocument"
                        files = {'document': doc_file}
                        doc_response = requests.post(url_doc, data=params, files=files)
                        
                        if doc_response.status_code == 200:
                            BOT2_LOGGER.info(f"[{horario_atual}] IMAGEM ENVIADA COMO DOCUMENTO para preservar transparência")
                            envio_sucesso = True
                        else:
                            BOT2_LOGGER.warning(f"[{horario_atual}] Não foi possível enviar como documento: {doc_response.text}")
                    except Exception as doc_error:
                        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao tentar enviar como documento: {str(doc_error)}")
            
            # Método padrão: enviar como foto
            if not envio_sucesso:
                with open(imagem_path, 'rb') as img_file:
                    try:
                        url_photo = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendPhoto"
                        files = {'photo': img_file}
                        photo_response = requests.post(url_photo, data=params, files=files)
                        
                        if photo_response.status_code == 200:
                            BOT2_LOGGER.info(f"[{horario_atual}] IMAGEM ENVIADA COMO FOTO com sucesso")
                            envio_sucesso = True
                        else:
                            BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar como foto: {photo_response.text}")
                    except Exception as photo_error:
                        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao processar envio como foto: {str(photo_error)}")
    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar imagem pós-sinal: {str(e)}")
        traceback.print_exc()

# Função para enviar mensagem promocional antes do sinal
def bot2_enviar_promo_pre_sinal():
    """
    Envia um vídeo promocional 10 minutos antes do sinal.
    É seguido de uma mensagem com link da corretora.
    """
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PRÉ-SINAL...")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal.get("idioma", "pt")  # Usar português como padrão
            link_corretora = config_canal.get("link_corretora", XXBROKER_URL)
            
            # Determinar qual vídeo enviar com base no idioma
            if idioma in VIDEOS_PROMO:
                video_path = VIDEOS_PROMO[idioma]
                if not os.path.exists(video_path):
                    BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Arquivo de vídeo promo não encontrado para {idioma}: {video_path}")
                    # Tentar usar português como fallback
                    video_path = VIDEOS_PROMO.get("pt", "")
                    if not os.path.exists(video_path):
                        BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Arquivo de vídeo promo fallback também não encontrado: {video_path}")
                        continue
            else:
                # Usar português como padrão
                video_path = VIDEOS_PROMO.get("pt", "")
                if not os.path.exists(video_path):
                    BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Arquivo de vídeo promo não encontrado: {video_path}")
                    continue
            
            # Verificar se é a primeira mensagem do dia para este canal
            hora_atual = agora.replace(minute=0, second=0, microsecond=0)
            key_contagem = f"{chat_id}_{hora_atual.strftime('%Y%m%d%H')}"
            
            BOT2_LOGGER.info(f"[{horario_atual}] Enviando vídeo pré-sinal para o canal {chat_id} em {idioma}...")
            
            # Enviar o vídeo promocional
            try:
                url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendVideo"
                
                # Parâmetros para envio do vídeo (sem definição de tamanho)
                params = {
                    'chat_id': chat_id,
                    'supports_streaming': True,
                    'disable_notification': False
                }
                
                with open(video_path, 'rb') as video_file:
                    files = {'video': video_file}
                    
                    resposta = requests.post(url_base, data=params, files=files)
                    
                    if resposta.status_code != 200:
                        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo pré-sinal para o canal {chat_id}: {resposta.text}")
                    else:
                        BOT2_LOGGER.info(f"[{horario_atual}] VÍDEO PRÉ-SINAL ENVIADO COM SUCESSO para o canal {chat_id}")
                
                # Texto da mensagem promocional
                if idioma == "pt":
                    mensagem = "⚠️ IMPORTANTE! Se você ainda não é nosso parceiro, clique no botão abaixo e abra sua conta na corretora. Aproveite os sinais! 💰"
                elif idioma == "en":
                    mensagem = "⚠️ IMPORTANT! If you are not yet our partner, click the button below and open your broker account. Enjoy the signals! 💰"
                elif idioma == "es":
                    mensagem = "⚠️ ¡IMPORTANTE! Si aún no eres nuestro socio, haz clic en el botón de abajo y abre tu cuenta de corredor. ¡Disfruta de las señales! 💰"
                else:
                    mensagem = "⚠️ IMPORTANTE! Se você ainda não é nosso parceiro, clique no botão abaixo e abra sua conta na corretora. Aproveite os sinais! 💰"
                
                # Texto do botão de acordo com o idioma
                if idioma == "pt":
                    texto_botao = "🔗 Abrir corretora"
                elif idioma == "en":
                    texto_botao = "🔗 Open broker"
                elif idioma == "es":
                    texto_botao = "🔗 Abrir corredor"
                else:
                    texto_botao = "🔗 Abrir corretora"
                
                # Configurar teclado inline com o link da corretora
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
                
                # Enviar a mensagem com o botão para a corretora
                url_msg = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
                
                payload = {
                    'chat_id': chat_id,
                    'text': mensagem,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': True,
                    'reply_markup': json.dumps(teclado_inline)
                }
                
                resposta_msg = requests.post(url_msg, data=payload)
                
                if resposta_msg.status_code != 200:
                    BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal para o canal {chat_id}: {resposta_msg.text}")
                else:
                    BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM PRÉ-SINAL ENVIADA COM SUCESSO para o canal {chat_id}")
                
            except Exception as e:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo e mensagem pré-sinal: {str(e)}")
        
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal: {str(e)}")
        traceback.print_exc()

# Função para enviar mensagem promocional a cada 3 sinais
def bot2_enviar_promo_especial():
    """
    Envia uma mensagem promocional especial a cada 3 sinais enviados.
    Para todos os canais: envia o vídeo específico do idioma e depois a mensagem.
    """
    try:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PROMOCIONAL ESPECIAL (A CADA 3 SINAIS) - Contador: {bot2_contador_sinais}...")
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            
            # Preparar textos baseados no idioma com links diretamente no texto
            if idioma == "pt":
                texto_mensagem = (
                    "Seguimos com as operações ✅\n\n"
                    "Mantenham a corretora aberta!!\n\n\n"
                    "Pra quem ainda não começou a ganhar dinheiro com a gente👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">CLIQUE AQUI E ASSISTA O VÍDEO</a>\n\n"
                    "🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n"
                    f"➡️ <a href=\"{XXBROKER_URL}\">CLICANDO AQUI</a>"
                )
            elif idioma == "en":
                texto_mensagem = (
                    "We continue with operations ✅\n\n"
                    "Keep the broker open!!\n\n\n"
                    "For those who haven't started making money with us yet👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">CLICK HERE AND WATCH THE VIDEO</a>\n\n"
                    "🔥Register on XXBROKER right now🔥\n\n"
                    f"➡️ <a href=\"{XXBROKER_URL}\">CLICK HERE</a>"
                )
            elif idioma == "es":
                texto_mensagem = (
                    "Continuamos con las operaciones ✅\n\n"
                    "¡Mantengan el corredor abierto!\n\n\n"
                    "Para quienes aún no han comenzado a ganar dinero con nosotros👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">HAZ CLIC AQUÍ Y MIRA EL VIDEO</a>\n\n"
                    "🔥Regístrese en XXBROKER ahora mismo🔥\n\n"
                    f"➡️ <a href=\"{XXBROKER_URL}\">CLIC AQUÍ</a>"
                )
            else:
                texto_mensagem = (
                    "Seguimos com as operações ✅\n\n"
                    "Mantenham a corretora aberta!!\n\n\n"
                    "Pra quem ainda não começou a ganhar dinheiro com a gente👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">CLIQUE AQUI E ASSISTA O VÍDEO</a>\n\n"
                    "🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n"
                    f"➡️ <a href=\"{XXBROKER_URL}\">CLICANDO AQUI</a>"
                )
            
            # Obter o caminho do vídeo especial específico para este idioma
            if idioma in VIDEOS_ESPECIAIS:
                video_path = VIDEOS_ESPECIAIS[idioma]
            else:
                video_path = VIDEOS_ESPECIAIS["pt"]  # Fallback para português
                
            # Verificar se o arquivo existe
            if not os.path.exists(video_path):
                BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de vídeo especial não encontrado: {video_path}")
                # Tentar usar o vídeo em português como backup se o idioma não for PT
                if idioma != "pt":
                    video_path = VIDEOS_ESPECIAIS["pt"]
                    BOT2_LOGGER.info(f"[{horario_atual}] Tentando usar vídeo especial em português como backup: {video_path}")
                    if not os.path.exists(video_path):
                        BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Arquivo de vídeo especial backup também não encontrado: {video_path}")
                        # Prosseguir para enviar apenas a mensagem de texto
                    else:
                        # Enviar vídeo
                        BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO VÍDEO ESPECIAL (A CADA 3 SINAIS) em português para o canal {chat_id}...")
                        bot2_enviar_video_especial(video_path, chat_id, horario_atual)
                else:
                    # Prosseguir para enviar apenas a mensagem de texto
                    pass
            else:
                # Enviar vídeo
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO VÍDEO ESPECIAL (A CADA 3 SINAIS) em {idioma} para o canal {chat_id}...")
                bot2_enviar_video_especial(video_path, chat_id, horario_atual)
            
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

# Função auxiliar para enviar o vídeo especial
def bot2_enviar_video_especial(video_path, chat_id, horario_atual):
    """
    Função auxiliar para enviar o vídeo especial.
    """
    try:
        url_base_video = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendVideo"
        
        with open(video_path, 'rb') as video_file:
            files = {
                'video': video_file
            }
            
            payload_video = {
                'chat_id': chat_id,
                'parse_mode': 'HTML'
            }
            
            resposta_video = requests.post(url_base_video, data=payload_video, files=files)
            if resposta_video.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar vídeo especial para o canal {chat_id}: {resposta_video.text}")
                return False
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] VÍDEO ESPECIAL (A CADA 3 SINAIS) ENVIADO COM SUCESSO para o canal {chat_id}")
                return True
    except Exception as e:
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao abrir ou enviar arquivo de vídeo especial: {str(e)}")
        return False

# Função para enviar o GIF especial a cada 3 sinais (apenas para o canal português)
def bot2_enviar_gif_especial_pt():
    """
    Envia um GIF especial apenas para o canal PT.
    Esta função deve ser chamada 30 segundos após o vídeo pós-sinal.
    """
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO GIF ESPECIAL PT...")
        
        # Verificar se a pasta de vídeos especiais existe, se não, criar
        if not os.path.exists(VIDEOS_ESPECIAL_DIR):
            os.makedirs(VIDEOS_ESPECIAL_DIR, exist_ok=True)
            BOT2_LOGGER.info(f"[{horario_atual}] Criada pasta para GIFs especiais: {VIDEOS_ESPECIAL_DIR}")
        
        if not os.path.exists(VIDEOS_ESPECIAL_PT_DIR):
            os.makedirs(VIDEOS_ESPECIAL_PT_DIR, exist_ok=True)
            BOT2_LOGGER.info(f"[{horario_atual}] Criada pasta PT para GIFs especiais: {VIDEOS_ESPECIAL_PT_DIR}")
        
        # Verificar se o arquivo do GIF especial existe
        BOT2_LOGGER.info(f"[{horario_atual}] Procurando GIF especial em: {VIDEO_GIF_ESPECIAL_PT}")
        if not os.path.exists(VIDEO_GIF_ESPECIAL_PT):
            BOT2_LOGGER.error(f"[{horario_atual}] Arquivo de GIF especial não encontrado: {VIDEO_GIF_ESPECIAL_PT}")
            
            # Tentar encontrar arquivos semelhantes
            if os.path.exists(VIDEOS_ESPECIAL_PT_DIR):
                arquivos_pt = os.listdir(VIDEOS_ESPECIAL_PT_DIR)
                BOT2_LOGGER.info(f"[{horario_atual}] Arquivos na pasta {VIDEOS_ESPECIAL_PT_DIR}: {arquivos_pt}")
                
                # Se encontrar algum arquivo na pasta PT, usar o primeiro
                if arquivos_pt:
                    primeiro_arquivo = os.path.join(VIDEOS_ESPECIAL_PT_DIR, arquivos_pt[0])
                    BOT2_LOGGER.info(f"[{horario_atual}] Usando arquivo alternativo: {primeiro_arquivo}")
                    arquivo_gif = primeiro_arquivo
                else:
                    BOT2_LOGGER.error(f"[{horario_atual}] Pasta PT existe mas está vazia: {VIDEOS_ESPECIAL_PT_DIR}")
                    return
            else:
                BOT2_LOGGER.error(f"[{horario_atual}] Pasta PT para GIFs especiais não existe: {VIDEOS_ESPECIAL_PT_DIR}")
                
                # Tentar listar o conteúdo da pasta pai
                if os.path.exists(VIDEOS_ESPECIAL_DIR):
                    BOT2_LOGGER.info(f"[{horario_atual}] Conteúdo da pasta {VIDEOS_ESPECIAL_DIR}: {os.listdir(VIDEOS_ESPECIAL_DIR)}")
                
                # Listar o conteúdo da pasta videos
                if os.path.exists(VIDEOS_DIR):
                    BOT2_LOGGER.info(f"[{horario_atual}] Conteúdo da pasta {VIDEOS_DIR}: {os.listdir(VIDEOS_DIR)}")
                
                return
        else:
            BOT2_LOGGER.info(f"[{horario_atual}] Arquivo GIF encontrado: {VIDEO_GIF_ESPECIAL_PT}")
            arquivo_gif = VIDEO_GIF_ESPECIAL_PT
            
        # Enviar o GIF para o canal PT
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            
            # Enviar apenas para o canal em português
            if idioma != "pt":
                continue
                
            try:
                # Enviar o arquivo para o canal PT
                BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO GIF ESPECIAL para o canal PT {chat_id}...")
                
                url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendAnimation"
                
                # Parâmetros para envio do GIF (sem definição de tamanho)
                params = {
                    'chat_id': chat_id,
                    'disable_notification': False
                }
                
                with open(arquivo_gif, 'rb') as gif_file:
                    files = {'animation': gif_file}
                    
                    resposta = requests.post(url_base, data=params, files=files)
                    
                    if resposta.status_code != 200:
                        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial para o canal {chat_id}: {resposta.text}")
                    else:
                        BOT2_LOGGER.info(f"[{horario_atual}] GIF ESPECIAL PT ENVIADO COM SUCESSO para o canal {chat_id}")
            except Exception as e:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial para o canal {chat_id}: {str(e)}")
                # Tentar enviar como vídeo se falhar como animação
                try:
                    url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendVideo"
                    
                    # Parâmetros para vídeo (sem definição de tamanho)
                    params_video = {
                        'chat_id': chat_id,
                        'supports_streaming': True,
                        'disable_notification': False
                    }
                    
                    with open(arquivo_gif, 'rb') as alt_file:
                        files = {'video': alt_file}
                        
                        resposta = requests.post(url_base, data=params_video, files=files)
                        
                        if resposta.status_code != 200:
                            BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial como vídeo para o canal {chat_id}: {resposta.text}")
                        else:
                            BOT2_LOGGER.info(f"[{horario_atual}] GIF ESPECIAL PT ENVIADO COMO VÍDEO com sucesso para o canal {chat_id}")
                except Exception as e2:
                    BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial como vídeo: {str(e2)}")
                    
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial PT: {str(e)}")
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

        # Loop para enviar aos canais configurados com base no idioma
        for chat_id in BOT2_CHAT_IDS:
            # Pegar configuração do canal
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            link_corretora = config_canal["link_corretora"]

            # Enviar apenas no idioma configurado para este canal
            mensagem = bot2_formatar_mensagem(sinal, hora_formatada, idioma)
            
            # IMPORTANTE: Log detalhado do conteúdo exato da mensagem para debug
            BOT2_LOGGER.info(f"[{horario_atual}] CONTEÚDO EXATO DA MENSAGEM DO SINAL: {mensagem}")

            # Texto do botão de acordo com o idioma
            texto_botao = "🔗 Abrir corretora"  # Padrão em português

            if idioma == "en":
                texto_botao = "🔗 Open broker"
            elif idioma == "es":
                texto_botao = "🔗 Abrir corredor"

            # Configura o teclado inline com o link da corretora
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

            # Envia a mensagem para o canal específico
            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"

            payload = {
                'chat_id': chat_id,
                'text': mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
                'reply_markup': json.dumps(teclado_inline)
            }

            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM DO SINAL em {idioma} para o canal {chat_id}...")
            resposta = requests.post(url_base, data=payload)

            if resposta.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar sinal para o canal {chat_id}: {resposta.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM DO SINAL ENVIADA COM SUCESSO para o canal {chat_id} no idioma {idioma}")

        # Registra estatísticas de envio
        bot2_registrar_envio(ativo, direcao, categoria)
        
        # Incrementa o contador global de sinais
        bot2_contador_sinais += 1
        BOT2_LOGGER.info(f"[{horario_atual}] Contador de sinais incrementado: {bot2_contador_sinais}")
        
        # Agendar o envio do vídeo pós-sinal para 5 minutos depois (acontece em TODOS os sinais)
        BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio do vídeo pós-sinal para daqui a 5 minutos...")
        import threading
        timer_pos_sinal = threading.Timer(300.0, bot2_enviar_gif_pos_sinal)  # 300 segundos = 5 minutos
        timer_pos_sinal.start()
        
        # Verifica se é o terceiro sinal para enviar a sequência especial
        if bot2_contador_sinais % 3 == 0:
            BOT2_LOGGER.info(f"[{horario_atual}] Terceiro sinal detectado! Agendando sequência especial...")
            
            # Função para agendar o envio sequencial
            def agendar_sequencia_especial():
                # 1. O vídeo pós-sinal já está agendado para 5 minutos após o sinal
                
                # 2. GIF especial PT (30 segundos após o vídeo pós-sinal = 5 minutos e 30 segundos após o sinal)
                timer_gif_especial = threading.Timer(330.0, bot2_enviar_gif_especial_pt)
                timer_gif_especial.start()
                BOT2_LOGGER.info(f"[{horario_atual}] Agendando GIF especial PT para daqui a 5 minutos e 30 segundos...")
                
                # 3. Mensagem promocional especial (3 segundos após o GIF especial PT = 5 minutos e 33 segundos após o sinal)
                timer_promo_especial = threading.Timer(333.0, bot2_enviar_promo_especial)
                timer_promo_especial.start()
                BOT2_LOGGER.info(f"[{horario_atual}] Agendando mensagem promocional especial para daqui a 5 minutos e 33 segundos...")
                
                # 4. Vídeo pré-sinal (5 minutos após a mensagem promocional = 10 minutos e 33 segundos após o sinal)
                timer_pre_sinal = threading.Timer(633.0, bot2_enviar_promo_pre_sinal)
                timer_pre_sinal.start()
                BOT2_LOGGER.info(f"[{horario_atual}] Agendando vídeo pré-sinal para daqui a 10 minutos e 33 segundos...")
                
                # 5. Mensagem pré-sinal (3 segundos após o vídeo pré-sinal = 10 minutos e 36 segundos após o sinal)
                timer_msg_pre_sinal = threading.Timer(636.0, bot2_enviar_mensagem_pre_sinal)
                timer_msg_pre_sinal.start()
                BOT2_LOGGER.info(f"[{horario_atual}] Agendando mensagem pré-sinal para daqui a 10 minutos e 36 segundos...")
            
            # Inicia o agendamento da sequência especial
            agendar_sequencia_especial()

    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem: {str(e)}")
        traceback.print_exc()

# Inicializações para a função bot2_send_message
bot2_send_message.ultimo_envio_timestamp = bot2_obter_hora_brasilia()
bot2_send_message.contagem_por_hora = {bot2_obter_hora_brasilia().replace(minute=0, second=0, microsecond=0): 0}

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

def bot2_schedule_messages():
    """Agenda o envio de mensagens para o Bot 2."""
    try:
        # Verificar se já existe agendamento
        if hasattr(bot2_schedule_messages, 'scheduled'):
            BOT2_LOGGER.info("Agendamentos já existentes. Pulando...")
            return

        BOT2_LOGGER.info("Iniciando agendamento de mensagens para o Bot 2")

        # Agendar envio de sinais a cada hora
        for hora in range(24):
            # Primeiro sinal
            schedule.every().day.at(f"{hora:02d}:13:02").do(bot2_send_message)

            # Segundo sinal
            schedule.every().day.at(f"{hora:02d}:37:02").do(bot2_send_message)

            # Terceiro sinal
            schedule.every().day.at(f"{hora:02d}:53:02").do(bot2_send_message)

        # Marcar como agendado
        bot2_schedule_messages.scheduled = True

        BOT2_LOGGER.info("Agendamento de mensagens do Bot 2 concluído com sucesso")
        BOT2_LOGGER.info("Horários configurados:")
        BOT2_LOGGER.info("Sinais: XX:13:02, XX:37:02, XX:53:02")
        BOT2_LOGGER.info("Para TODOS os sinais:")
        BOT2_LOGGER.info("- Vídeo pós-sinal: 5 minutos após o sinal")
        BOT2_LOGGER.info("Apenas para o terceiro sinal (ou múltiplos de 3):")
        BOT2_LOGGER.info("- GIF especial PT: 5 minutos e 30 segundos após o sinal (30 segundos após o vídeo pós-sinal)")
        BOT2_LOGGER.info("- Mensagem promocional especial: 5 minutos e 33 segundos após o sinal (3 segundos após o GIF especial)")
        BOT2_LOGGER.info("- Vídeo pré-sinal: 10 minutos e 33 segundos após o sinal (5 minutos após a mensagem promocional)")
        BOT2_LOGGER.info("- Mensagem pré-sinal: 10 minutos e 36 segundos após o sinal (3 segundos após o vídeo pré-sinal)")

    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao agendar mensagens do Bot 2: {str(e)}")
        traceback.print_exc()

def iniciar_ambos_bots():
    """
    Inicializa ambos os bots quando executado como script principal.
    """
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

def bot2_enviar_mensagem_pre_sinal():
    """
    Envia uma mensagem promocional antes do sinal.
    Esta função é chamada após o envio do vídeo pré-sinal.
    """
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PRÉ-SINAL...")

        # Mensagens pré-definidas por idioma
        mensagens_pre_sinal = {
            "pt": "⚠️ ATENÇÃO! Um novo sinal será enviado em breve! Prepare-se para lucrar! 💰",
            "en": "⚠️ ATTENTION! A new signal will be sent soon! Get ready to profit! 💰",
            "es": "⚠️ ¡ATENCIÓN! ¡Una nueva señal será enviada pronto! ¡Prepárate para ganar! 💰"
        }

        # Loop para enviar a mensagem para cada canal configurado
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            link_corretora = config_canal["link_corretora"]
            
            # Texto do botão de acordo com o idioma
            texto_botao = "🔗 Abrir corretora"  # Padrão em português
            if idioma == "en":
                texto_botao = "🔗 Open broker"
            elif idioma == "es":
                texto_botao = "🔗 Abrir corredor"

            # Mensagem específica para o idioma
            mensagem = mensagens_pre_sinal.get(idioma, mensagens_pre_sinal["pt"])
            
            # Configurar teclado inline com o link da corretora
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
            
            # Enviar a mensagem para o canal específico
            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
                'reply_markup': json.dumps(teclado_inline)
            }
            
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM PRÉ-SINAL em {idioma} para o canal {chat_id}...")
            resposta = requests.post(url_base, data=payload)
            
            if resposta.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal para o canal {chat_id}: {resposta.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM PRÉ-SINAL ENVIADA COM SUCESSO para o canal {chat_id} no idioma {idioma}")
                
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal: {str(e)}")
        traceback.print_exc()

# Executar se este arquivo for o script principal
if __name__ == "__main__":
    try:
        print("=== INICIANDO O BOT TELEGRAM ===")
        print(f"Diretório base: {BASE_DIR}")
        print(f"Diretório de vídeos: {VIDEOS_DIR}")
        print(f"Diretório de GIFs especiais: {VIDEOS_ESPECIAL_DIR}")
        print(f"Arquivo GIF especial PT: {VIDEO_GIF_ESPECIAL_PT}")
        
        # Exibir caminhos das imagens pós-sinal
        print(f"Caminho da imagem pós-sinal padrão (PT): {os.path.join(VIDEOS_POS_SINAL_DIR, 'pt', 'padrao.jpg')}")
        print(f"Caminho da imagem pós-sinal especial (PT): {os.path.join(VIDEOS_POS_SINAL_DIR, 'pt', 'especial.jpg')}")
        print(f"Caminho da imagem pós-sinal padrão (EN): {os.path.join(VIDEOS_POS_SINAL_DIR, 'en', 'padrao.jpg')}")
        print(f"Caminho da imagem pós-sinal especial (EN): {os.path.join(VIDEOS_POS_SINAL_DIR, 'en', 'especial.jpg')}")
        print(f"Caminho da imagem pós-sinal padrão (ES): {os.path.join(VIDEOS_POS_SINAL_DIR, 'es', 'padrao.jpg')}")
        print(f"Caminho da imagem pós-sinal especial (ES): {os.path.join(VIDEOS_POS_SINAL_DIR, 'es', 'especial.jpg')}")
        
        # Verificar se os diretórios existem
        print(f"Verificando pastas:")
        print(f"VIDEOS_DIR existe: {os.path.exists(VIDEOS_DIR)}")
        print(f"VIDEOS_POS_SINAL_DIR existe: {os.path.exists(VIDEOS_POS_SINAL_DIR)}")
        print(f"VIDEOS_POS_SINAL_PT_DIR existe: {os.path.exists(VIDEOS_POS_SINAL_PT_DIR)}")
        print(f"VIDEOS_ESPECIAL_DIR existe: {os.path.exists(VIDEOS_ESPECIAL_DIR)}")
        print(f"VIDEOS_ESPECIAL_PT_DIR existe: {os.path.exists(VIDEOS_ESPECIAL_PT_DIR)}")
        
        # Criar pastas se não existirem
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        os.makedirs(VIDEOS_ESPECIAL_DIR, exist_ok=True)
        os.makedirs(VIDEOS_ESPECIAL_PT_DIR, exist_ok=True)
        os.makedirs(VIDEOS_POS_SINAL_DIR, exist_ok=True)
        os.makedirs(VIDEOS_POS_SINAL_PT_DIR, exist_ok=True)
        os.makedirs(VIDEOS_POS_SINAL_EN_DIR, exist_ok=True)
        os.makedirs(VIDEOS_POS_SINAL_ES_DIR, exist_ok=True)
        
        # Iniciar os bots
        iniciar_ambos_bots()
    except Exception as e:
        print(f"Erro ao iniciar bots: {str(e)}")
        traceback.print_exc()
