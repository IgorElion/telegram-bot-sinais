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
        "link_corretora": "https://trade.xxbroker.com/register?aff=741613&aff_model=revenue&afftrack=",
        "fuso_horario": "America/Sao_Paulo"  # Brasil (UTC-3)
    },
    "-1002453956387": {  # Canal para mensagens em inglês
        "idioma": "en",
        "link_corretora": "https://trade.xxbroker.com/register?aff=741727&aff_model=revenue&afftrack=",
        "fuso_horario": "America/New_York"  # EUA (UTC-5 ou UTC-4 no horário de verão)
    },
    "-1002446547846": {  # Canal para mensagens em espanhol
        "idioma": "es",
        "link_corretora": "https://trade.xxbroker.com/register?aff=741726&aff_model=revenue&afftrack=",
        "fuso_horario": "Europe/Madrid"  # Espanha (UTC+1 ou UTC+2 no horário de verão)
    }
}

# Lista de IDs dos canais para facilitar iteração
BOT2_CHAT_IDS = list(BOT2_CANAIS_CONFIG.keys())

# ID para compatibilidade com código existente
BOT2_CHAT_ID_CORRETO = BOT2_CHAT_IDS[0]  # Usar o primeiro canal como padrão

# Limite de sinais por hora
BOT2_LIMITE_SINAIS_POR_HORA = 1

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
    "McDonald´s Corporation (OTC)": HORARIOS_PADRAO["McDonalds_Corporation_OTC"],
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
        tempo_expiracao_minutos = random.choice([1, 5])
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

# Função para obter hora no fuso horário específico (a partir da hora de Brasília)
def bot2_converter_fuso_horario(hora_brasilia, fuso_destino):
    """
    Converte uma hora do fuso horário de Brasília para o fuso horário de destino.
    
    Args:
        hora_brasilia (datetime): Hora no fuso horário de Brasília
        fuso_destino (str): Nome do fuso horário de destino (ex: 'America/New_York')
        
    Returns:
        datetime: Hora convertida para o fuso horário de destino
    """
    # Garantir que hora_brasilia tenha informações de fuso horário
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    
    # Se a hora não tiver informação de fuso, adicionar
    if hora_brasilia.tzinfo is None:
        hora_brasilia = fuso_horario_brasilia.localize(hora_brasilia)
    
    # Converter para o fuso horário de destino
    fuso_destino_tz = pytz.timezone(fuso_destino)
    hora_destino = hora_brasilia.astimezone(fuso_destino_tz)
    
    return hora_destino

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
    action_pt = "PUT" if direcao == 'sell' else "CALL"
    action_en = "PUT" if direcao == 'sell' else "CALL"
    action_es = "PUT" if direcao == 'sell' else "CALL"
    emoji = "🟥" if direcao == 'sell' else "🟢"

    # Encontrar o fuso horário adequado para o idioma
    fuso_horario = "America/Sao_Paulo"  # Padrão (Brasil)
    
    # Buscar o fuso horário na configuração dos canais
    for chat_id, config in BOT2_CANAIS_CONFIG.items():
        if config["idioma"] == idioma:
            fuso_horario = config.get("fuso_horario", "America/Sao_Paulo")
            break
    
    # Hora de entrada convertida para datetime no fuso horário de Brasília
    hora_entrada = datetime.strptime(hora_formatada, "%H:%M")
    hora_entrada_br = bot2_obter_hora_brasilia().replace(hour=hora_entrada.hour, minute=hora_entrada.minute, second=0, microsecond=0)
    
    # Converter para o fuso horário do canal
    hora_entrada_local = bot2_converter_fuso_horario(hora_entrada_br, fuso_horario)
    
    # Calcular horário de expiração no fuso horário de Brasília
    hora_expiracao_br = hora_entrada_br + timedelta(minutes=tempo_expiracao_minutos)
    
    # Converter expiração para o fuso horário do canal
    hora_expiracao_local = bot2_converter_fuso_horario(hora_expiracao_br, fuso_horario)
    
    # Calcular horários de gale (reentrada) no fuso horário de Brasília
    # 1º GALE é o horário de expiração + tempo de expiração
    hora_gale1_br = hora_expiracao_br + timedelta(minutes=tempo_expiracao_minutos)
    # 2º GALE é o 1º GALE + tempo de expiração
    hora_gale2_br = hora_gale1_br + timedelta(minutes=tempo_expiracao_minutos)
    # 3º GALE é o 2º GALE + tempo de expiração
    hora_gale3_br = hora_gale2_br + timedelta(minutes=tempo_expiracao_minutos)
    
    # Converter gales para o fuso horário do canal
    hora_gale1_local = bot2_converter_fuso_horario(hora_gale1_br, fuso_horario)
    hora_gale2_local = bot2_converter_fuso_horario(hora_gale2_br, fuso_horario)
    hora_gale3_local = bot2_converter_fuso_horario(hora_gale3_br, fuso_horario)
    
    # Formatar os horários para exibição (no fuso horário local)
    hora_entrada_formatada = hora_entrada_local.strftime("%H:%M")
    hora_expiracao_formatada = hora_expiracao_local.strftime("%H:%M")
    hora_gale1_formatada = hora_gale1_local.strftime("%H:%M")
    hora_gale2_formatada = hora_gale2_local.strftime("%H:%M")
    hora_gale3_formatada = hora_gale3_local.strftime("%H:%M")
    
    # Registrar a conversão de fuso horário
    BOT2_LOGGER.info(f"Horários convertidos para fuso {fuso_horario}: Entrada={hora_entrada_formatada}, " +
                     f"Expiração={hora_expiracao_formatada}, Gale1={hora_gale1_formatada}, " +
                     f"Gale2={hora_gale2_formatada}, Gale3={hora_gale3_formatada}")

    # Formatação para singular ou plural de "minuto" baseado no tempo de expiração
    texto_minutos_pt = "minuto" if tempo_expiracao_minutos == 1 else "minutos"
    texto_minutos_en = "minute" if tempo_expiracao_minutos == 1 else "minutes"
    texto_minutos_es = "minuto" if tempo_expiracao_minutos == 1 else "minutos"

    # Configurar links baseados no idioma
    if idioma == "pt":
        link_corretora = "https://trade.xxbroker.com/register?aff=741613&aff_model=revenue&afftrack="
        link_video = "https://t.me/trendingbrazil/215"
        texto_corretora = "Clique para abrir a corretora"
        texto_video = "Clique aqui"
        texto_tempo = "TEMPO PARA"
        texto_gale1 = "1º GALE — TEMPO PARA"
        texto_gale2 = "2º GALE TEMPO PARA"
        texto_gale3 = "3º GALE TEMPO PARA"
    elif idioma == "en":
        link_corretora = "https://trade.xxbroker.com/register?aff=741727&aff_model=revenue&afftrack="
        link_video = "https://t.me/trendingenglish/226"
        texto_corretora = "Click to open broker"
        texto_video = "Click here"
        texto_tempo = "TIME UNTIL"
        texto_gale1 = "1st GALE — TIME UNTIL"
        texto_gale2 = "2nd GALE TIME UNTIL"
        texto_gale3 = "3rd GALE TIME UNTIL"
    else:  # espanhol
        link_corretora = "https://trade.xxbroker.com/register?aff=741726&aff_model=revenue&afftrack="
        link_video = "https://t.me/trendingespanish/212"
        texto_corretora = "Haga clic para abrir el corredor"
        texto_video = "Haga clic aquí"
        texto_tempo = "TIEMPO HASTA"
        texto_gale1 = "1º GALE — TIEMPO HASTA"
        texto_gale2 = "2º GALE TIEMPO HASTA"
        texto_gale3 = "3º GALE TIEMPO HASTA"
    
    # Mensagem em PT
    mensagem_pt = (f"💰{tempo_expiracao_minutos} {texto_minutos_pt} de expiração\n"
            f"{nome_ativo_exibicao};{hora_entrada_formatada};{action_pt} {emoji} {categoria}\n\n"
            f"🕐{texto_tempo} {hora_expiracao_formatada}\n\n"
            f"{texto_gale1} {hora_gale1_formatada}\n"
            f"{texto_gale2} {hora_gale2_formatada}\n"
            f"{texto_gale3} {hora_gale3_formatada}\n\n"
            f"📲 <a href=\"{link_corretora}\" data-js-focus-visible=\"\">&#8203;{texto_corretora}</a>\n"
            f"🙋‍♂️ Não sabe operar ainda? <a href=\"{link_video}\" data-js-focus-visible=\"\">&#8203;{texto_video}</a>")
            
    # Mensagem em EN
    mensagem_en = (f"💰{tempo_expiracao_minutos} {texto_minutos_en} expiration\n"
            f"{nome_ativo_exibicao};{hora_entrada_formatada};{action_en} {emoji} {categoria}\n\n"
            f"🕐{texto_tempo} {hora_expiracao_formatada}\n\n"
            f"{texto_gale1} {hora_gale1_formatada}\n"
            f"{texto_gale2} {hora_gale2_formatada}\n"
            f"{texto_gale3} {hora_gale3_formatada}\n\n"
            f"📲 <a href=\"{link_corretora}\" data-js-focus-visible=\"\">&#8203;{texto_corretora}</a>\n"
            f"🙋‍♂️ Don't know how to trade yet? <a href=\"{link_video}\" data-js-focus-visible=\"\">&#8203;{texto_video}</a>")
            
    # Mensagem em ES
    mensagem_es = (f"💰{tempo_expiracao_minutos} {texto_minutos_es} de expiración\n"
            f"{nome_ativo_exibicao};{hora_entrada_formatada};{action_es} {emoji} {categoria}\n\n"
            f"🕐{texto_tempo} {hora_expiracao_formatada}\n\n"
            f"{texto_gale1} {hora_gale1_formatada}\n"
            f"{texto_gale2} {hora_gale2_formatada}\n"
            f"{texto_gale3} {hora_gale3_formatada}\n\n"
            f"📲 <a href=\"{link_corretora}\" data-js-focus-visible=\"\">&#8203;{texto_corretora}</a>\n"
            f"🙋‍♂️ ¿No sabe operar todavía? <a href=\"{link_video}\" data-js-focus-visible=\"\">&#8203;{texto_video}</a>")
            
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
XXBROKER_URL = "https://trade.xxbroker.com/register?aff=741613&aff_model=revenue&afftrack="
VIDEO_TELEGRAM_URL = "https://t.me/trendingbrazil/215"
VIDEO_TELEGRAM_ES_URL = "https://t.me/trendingespanish/212"
VIDEO_TELEGRAM_EN_URL = "https://t.me/trendingenglish/226"

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

# Adicionar variáveis para controle da imagem especial diária
import random
horario_especial_diario = None
imagem_especial_ja_enviada_hoje = False

# Função para definir o horário especial diário
def definir_horario_especial_diario():
    global horario_especial_diario, imagem_especial_ja_enviada_hoje
    
    # Reseta o status de envio da imagem especial
    imagem_especial_ja_enviada_hoje = False
    
    # Define um horário aleatório entre 0 e 23 horas
    horas_disponiveis = list(range(0, 24))
    hora_aleatoria = random.choice(horas_disponiveis)
    
    # Definir o mesmo minuto usado para o envio de sinais
    minuto_envio = 13
    
    # Define o horário especial para hoje
    horario_atual = bot2_obter_hora_brasilia()
    horario_especial_diario = horario_atual.replace(
        hour=hora_aleatoria, 
        minute=minuto_envio,  # Mesmo minuto usado para envio de sinais
        second=0, 
        microsecond=0
    )
    
    BOT2_LOGGER.info(f"Horário especial diário definido para: {horario_especial_diario.strftime('%H:%M')}")
    
    # Se o horário já passou hoje, reagenda para amanhã
    if horario_especial_diario < horario_atual:
        horario_especial_diario = horario_especial_diario + timedelta(days=1)
        BOT2_LOGGER.info(f"Horário já passou hoje, reagendado para amanhã: {horario_especial_diario.strftime('%H:%M')}")

# Agendar a redefinição do horário especial diário à meia-noite
def agendar_redefinicao_horario_especial():
    schedule.every().day.at("00:01").do(definir_horario_especial_diario)
    BOT2_LOGGER.info("Agendada redefinição do horário especial diário para meia-noite e um minuto")

# Chamar a função no início para definir o horário especial para hoje
definir_horario_especial_diario()
agendar_redefinicao_horario_especial()

def bot2_enviar_gif_pos_sinal():
    """Envia um GIF ou imagem pós-sinal para todos os canais."""
    try:
        global contador_pos_sinal
        global contador_desde_ultimo_especial
        global imagem_especial_ja_enviada_hoje
        global horario_especial_diario
        
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA IMAGEM PÓS-SINAL...")
        
        # Limpar o próprio agendamento para garantir que este seja executado apenas uma vez por sinal
        schedule.clear('bot2_pos_sinal')
        BOT2_LOGGER.info(f"[{horario_atual}] Agendamento de gif pós-sinal limpo para evitar duplicações.")
        
        # Tentar importar PIL para verificar se uma imagem tem transparência
        try:
            from PIL import Image
            BOT2_LOGGER.info(f"[{horario_atual}] Biblioteca PIL (Pillow) disponível para processamento de imagem")
            pillow_disponivel = True
        except ImportError:
            pillow_disponivel = False
            BOT2_LOGGER.warning(f"[{horario_atual}] Biblioteca PIL (Pillow) não disponível. As imagens serão enviadas sem tratamento.")
        
        # Incrementar o contador de envios pós-sinal
        contador_pos_sinal += 1
        contador_desde_ultimo_especial += 1
        
        BOT2_LOGGER.info(f"[{horario_atual}] Contador pós-sinal: {contador_pos_sinal}, Contador desde último especial: {contador_desde_ultimo_especial}")
        
        # Determinar se devemos enviar a imagem especial
        # Verifica se é o horário especial definido para hoje e se a imagem especial ainda não foi enviada hoje
        horario_especial_agora = False
        if horario_especial_diario and not imagem_especial_ja_enviada_hoje:
            # Compara apenas hora e minuto, ignorando segundos
            if (agora.hour == horario_especial_diario.hour and 
                agora.minute == horario_especial_diario.minute):
                horario_especial_agora = True
                imagem_especial_ja_enviada_hoje = True
                BOT2_LOGGER.info(f"[{horario_atual}] HORÁRIO ESPECIAL DETECTADO! Enviando imagem especial pela única vez no dia")
        
        # Verifica se deve enviar imagem especial (apenas no horário especial do dia)
        if horario_especial_agora:
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO A IMAGEM ESPECIAL (sinal {contador_pos_sinal})")
            deve_enviar_especial = True
            
            # Se foi por causa do horário especial, registra isso
            if horario_especial_agora:
                BOT2_LOGGER.info(f"[{horario_atual}] Envio de imagem especial foi acionado pelo horário especial do dia")
            
            contador_desde_ultimo_especial = 0
        else:
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO A IMAGEM PADRÃO (sinal {contador_pos_sinal})")
            deve_enviar_especial = False
        
        # Loop para enviar aos canais configurados
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            
            # Diretório base para imagens
            dir_base = f"videos/pos_sinal/{idioma}"
            
            # Nomes de arquivos padrão
            nome_padrao = "padrao.webp"
            nome_especial = "especial.webp"
            
            # Determinar qual imagem enviar com base no idioma
            imagem_selecionada = None
            nome_arquivo = nome_especial if deve_enviar_especial else nome_padrao
            
            # Tentar encontrar o arquivo no formato correto
            possiveis_formatos = ['.webp', '.jpg', '.png', '.jpeg', '.gif']
            imagem_path = None
            
            # Primeiro, tenta encontrar o arquivo exato
            for formato in possiveis_formatos:
                # Remove a extensão atual e adiciona o formato sendo testado
                nome_base = nome_arquivo.rsplit('.', 1)[0]
                caminho = f"{dir_base}/{nome_base}{formato}"
                
                if os.path.exists(caminho):
                    imagem_path = caminho
                    BOT2_LOGGER.info(f"[{horario_atual}] Encontrada imagem: {caminho}")
                    break
                    
                # Tenta com acento para compatibilidade
                if nome_base == "padrao":
                    caminho = f"{dir_base}/padrão{formato}"
                    if os.path.exists(caminho):
                        imagem_path = caminho
                        BOT2_LOGGER.info(f"[{horario_atual}] Encontrada imagem com acento: {caminho}")
                        break
            
            # Se não encontrou imagem no idioma específico, usa o fallback em português
            if not imagem_path:
                fallback_dir = f"videos/pos_sinal/pt"
                for formato in possiveis_formatos:
                    nome_base = nome_arquivo.rsplit('.', 1)[0]
                    fallback_path = f"{fallback_dir}/{nome_base}{formato}"
                    
                    if os.path.exists(fallback_path):
                        imagem_path = fallback_path
                        BOT2_LOGGER.info(f"[{horario_atual}] Usando fallback em português: {fallback_path}")
                        break
                        
                    # Tenta com acento para compatibilidade
                    if nome_base == "padrao":
                        fallback_path = f"{fallback_dir}/padrão{formato}"
                        if os.path.exists(fallback_path):
                            imagem_path = fallback_path
                            BOT2_LOGGER.info(f"[{horario_atual}] Usando fallback em português com acento: {fallback_path}")
                            break
            
            # Se ainda não encontrou nenhuma imagem, log de erro e continua para o próximo canal
            if not imagem_path:
                BOT2_LOGGER.error(f"[{horario_atual}] ERRO: Não foi possível encontrar nenhuma imagem para o canal {chat_id}")
                continue
                
            BOT2_LOGGER.info(f"[{horario_atual}] Enviando imagem pós-sinal para o canal {chat_id} no idioma {idioma}: {imagem_path}")
            
            # Verifica se o arquivo tem extensão .webp ou .png (possivelmente tem transparência)
            if imagem_path.lower().endswith(('.webp', '.png')):
                BOT2_LOGGER.info(f"[{horario_atual}] Detectada imagem com transparência (.webp ou .png), enviando como sticker")
                
                try:
                    # Tenta enviar como sticker primeiro
                    with open(imagem_path, 'rb') as sticker_file:
                        url_sticker = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendSticker"
                        files = {'sticker': sticker_file}
                        data = {'chat_id': chat_id}
                        
                        try:
                            sticker_response = requests.post(url_sticker, files=files, data=data)
                            if sticker_response.status_code == 200:
                                BOT2_LOGGER.info(f"[{horario_atual}] ✓ IMAGEM ENVIADA COMO STICKER com transparência preservada")
                                continue  # Envio bem-sucedido, seguir para o próximo canal
                            else:
                                BOT2_LOGGER.warning(f"[{horario_atual}] ✗ Não foi possível enviar como sticker: {sticker_response.text}")
                        except Exception as sticker_error:
                            BOT2_LOGGER.error(f"[{horario_atual}] ✗ Erro ao tentar enviar como sticker: {str(sticker_error)}")
                    
                    # Se falhar como sticker, tenta enviar como documento
                    BOT2_LOGGER.info(f"[{horario_atual}] Tentando enviar imagem com transparência como documento")
                    with open(imagem_path, 'rb') as doc_file:
                        url_doc = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendDocument"
                        files = {'document': doc_file}
                        data = {'chat_id': chat_id}
                        
                        try:
                            doc_response = requests.post(url_doc, files=files, data=data)
                            if doc_response.status_code == 200:
                                BOT2_LOGGER.info(f"[{horario_atual}] ✓ IMAGEM ENVIADA COMO DOCUMENTO com transparência preservada")
                                continue  # Envio bem-sucedido, seguir para o próximo canal
                            else:
                                BOT2_LOGGER.warning(f"[{horario_atual}] ✗ Não foi possível enviar como documento: {doc_response.text}")
                        except Exception as doc_error:
                            BOT2_LOGGER.error(f"[{horario_atual}] ✗ Erro ao tentar enviar como documento: {str(doc_error)}")
                
                except Exception as e:
                    BOT2_LOGGER.error(f"[{horario_atual}] Erro ao processar arquivo webp/png: {str(e)}")
            
            # Se chegou aqui, ainda não conseguiu enviar. Tenta enviar como foto.
            try:
                BOT2_LOGGER.info(f"[{horario_atual}] Enviando imagem como foto (método padrão)")
                with open(imagem_path, 'rb') as photo_file:
                    url_photo = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendPhoto"
                    files = {'photo': photo_file}
                    data = {'chat_id': chat_id}
                    
                    try:
                        photo_response = requests.post(url_photo, files=files, data=data)
                        if photo_response.status_code == 200:
                            BOT2_LOGGER.info(f"[{horario_atual}] ✓ IMAGEM ENVIADA COMO FOTO com sucesso")
                        else:
                            BOT2_LOGGER.error(f"[{horario_atual}] ✗ Erro ao enviar como foto: {photo_response.text}")
                    except Exception as photo_error:
                        BOT2_LOGGER.error(f"[{horario_atual}] ✗ Erro ao processar envio como foto: {str(photo_error)}")
            except Exception as file_error:
                BOT2_LOGGER.error(f"[{horario_atual}] ✗ Erro ao abrir o arquivo: {str(file_error)}")
    
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
                    mensagem = ""
                elif idioma == "en":
                    mensagem = ""
                elif idioma == "es":
                    mensagem = ""
                else:
                    mensagem = ""
                
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
            link_corretora = config_canal["link_corretora"]

            # Preparar textos baseados no idioma com links diretamente no texto
            if idioma == "pt":
                texto_mensagem = (
                    "⚠️⚠️PARA PARTICIPAR DESTA SESSÃO, SIGA O PASSO A PASSO ABAIXO⚠️⚠️\n\n\n"
                    "1º ✅ —>  Crie sua conta na corretora no link abaixo e GANHE $10.000 DE GRAÇA pra começar a operar com a gente sem ter que arriscar seu dinheiro.\n\n"
                    "Você vai poder testar todos nossas\n"
                    "operações com risco ZERO!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{link_corretora}\">CRIE SUA CONTA AQUI E GANHE R$10.000</a>\n\n"
                    "—————————————————————\n\n"
                    "2º ✅ —>  Assista o vídeo abaixo e aprenda como depositar e como entrar com a gente nas nossas operações!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">CLIQUE AQUI E ASSISTA O VÍDEO</a>"
                )
            elif idioma == "en":
                texto_mensagem = (
                    "⚠️⚠️TO PARTICIPATE IN THIS SESSION, FOLLOW THE STEPS BELOW⚠️⚠️\n\n\n"
                    "1st ✅ —> Create your broker account in the link below and GET $10,000 FOR FREE to start trading with us without risking your money.\n\n"
                    "You'll be able to test all our\n"
                    "operations with ZERO RISK!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{link_corretora}\">CREATE YOUR ACCOUNT HERE AND GET $10,000</a>\n\n"
                    "—————————————————————\n\n"
                    "2nd ✅ —> Watch the video below and learn how to deposit and how to join us in our operations!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_EN_URL}\">CLICK HERE AND WATCH THE VIDEO</a>"
                )
            elif idioma == "es":
                texto_mensagem = (
                    "⚠️⚠️PARA PARTICIPAR EN ESTA SESIÓN, SIGA LOS PASOS A CONTINUACIÓN⚠️⚠️\n\n\n"
                    "1º ✅ —> Crea tu cuenta en el corredor en el enlace de abajo y OBTÉN $10,000 GRATIS para comenzar a operar con nosotros sin arriesgar tu dinero.\n\n"
                    "Podrás probar todas nuestras\n"
                    "operaciones con RIESGO CERO!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{link_corretora}\">CREA TU CUENTA AQUÍ Y OBTÉN $10,000</a>\n\n"
                    "—————————————————————\n\n"
                    "2º ✅ —> Mira el video de abajo y aprende cómo depositar y cómo unirte a nosotros en nuestras operaciones!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_ES_URL}\">HAZ CLIC AQUÍ Y MIRA EL VIDEO</a>"
                )
            else:
                texto_mensagem = (
                    "⚠️⚠️PARA PARTICIPAR DESTA SESSÃO, SIGA O PASSO A PASSO ABAIXO⚠️⚠️\n\n\n"
                    "1º ✅ —>  Crie sua conta na corretora no link abaixo e GANHE $10.000 DE GRAÇA pra começar a operar com a gente sem ter que arriscar seu dinheiro.\n\n"
                    "Você vai poder testar todos nossas\n"
                    "operações com risco ZERO!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{link_corretora}\">CRIE SUA CONTA AQUI E GANHE R$10.000</a>\n\n"
                    "—————————————————————\n\n"
                    "2º ✅ —>  Assista o vídeo abaixo e aprenda como depositar e como entrar com a gente nas nossas operações!\n\n"
                    "👇🏻👇🏻👇🏻👇🏻\n\n"
                    f"<a href=\"{VIDEO_TELEGRAM_URL}\">CLIQUE AQUI E ASSISTA O VÍDEO</a>"
                )

            # Enviar mensagem com links (agora incorporados diretamente no texto)
            BOT2_LOGGER.info(f"[{horario_atual}] ENVIANDO MENSAGEM PROMOCIONAL ESPECIAL (A CADA 3 SINAIS) para o canal {chat_id}...")
            url_base_msg = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"

            payload_msg = {
                'chat_id': chat_id,
                'text': texto_mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }

            # Enviar a mensagem
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
            return

        # Configurações específicas para o canal de idioma português
        # Usar apenas o canal português (primeiro canal)
        canal_pt = None
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            if config_canal["idioma"] == "pt":
                canal_pt = chat_id
                break
                
        # Se não encontrou canal PT, usar o primeiro canal
        if canal_pt is None:
            canal_pt = BOT2_CHAT_IDS[0]
            BOT2_LOGGER.warning(f"[{horario_atual}] Não foi encontrado canal PT. Usando primeiro canal: {canal_pt}")

        # Verificar se canal português está habilitado
        if canal_pt == "":
            BOT2_LOGGER.warning(f"[{horario_atual}] Canal PT está desativado. GIF ESPECIAL PT não foi enviado.")
            return

        BOT2_LOGGER.info(f"[{horario_atual}] Enviando GIF ESPECIAL PT para o canal: {canal_pt}")

        try:
            # Enviar o GIF como vídeo diretamente
            BOT2_LOGGER.info(f"[{horario_atual}] Arquivo GIF encontrado: {VIDEO_GIF_ESPECIAL_PT}")
            arquivo_gif = VIDEO_GIF_ESPECIAL_PT

            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendVideo"

            # Parâmetros para vídeo (sem definição de tamanho)
            params = {
                'chat_id': canal_pt,
                'supports_streaming': True,
            }

            with open(arquivo_gif, 'rb') as video_file:
                files = {'video': video_file}
                resposta = requests.post(url_base, data=params, files=files)

                if resposta.status_code != 200:
                    BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial como vídeo para o canal {canal_pt}: {resposta.text}")
                else:
                    BOT2_LOGGER.info(f"[{horario_atual}] GIF ESPECIAL PT ENVIADO COMO VÍDEO com sucesso para o canal {canal_pt}")
        except Exception as e:
            BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial para o canal {canal_pt}: {str(e)}")
            
    except Exception as e:
        horario_atual = bot2_obter_hora_brasilia().strftime("%H:%M:%S")
        BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar GIF especial PT: {str(e)}")
        traceback.print_exc()

# Modificar a função bot2_send_message para alterar os tempos de agendamento
def bot2_send_message(ignorar_anti_duplicacao=False):
    """Envia uma mensagem com sinal para todos os canais configurados."""
    global bot2_contador_sinais
    
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DO SINAL...")
        
        # Verificar se já houve envio recente para evitar flood (mínimo 45 segundos entre mensagens)
        if hasattr(bot2_send_message, 'ultimo_envio_timestamp'):
            diferenca = (agora - bot2_send_message.ultimo_envio_timestamp).total_seconds()
            if diferenca < 45 and not ignorar_anti_duplicacao:
                BOT2_LOGGER.warning(f"[{horario_atual}] Anti-duplicação: último envio foi há {diferenca:.1f} segundos.")
                if diferenca < 10:  # Muito recente, ignorar
                    BOT2_LOGGER.warning(f"[{horario_atual}] Limite anti-duplicação atingido. Ignorando este sinal.")
                    return
        
        bot2_send_message.ultimo_envio_timestamp = agora
        
        # Verificar limite de sinais por hora
        hora_atual = agora.replace(minute=0, second=0, microsecond=0)
        
        # Gerar o sinal aleatório
        sinal = bot2_gerar_sinal_aleatorio()
        if not sinal:
            BOT2_LOGGER.error(f"[{horario_atual}] Não foi possível gerar um sinal válido. Tentando novamente mais tarde.")
            return
            
        # Em vez de desempacotar diretamente, obtenha os valores do dicionário
        ativo = sinal['ativo']
        direcao = sinal['direcao']
        tempo_expiracao_minutos = sinal['tempo_expiracao_minutos']
        categoria = sinal['categoria']
        
        # Calcular os horários que faltam
        hora_entrada = bot2_obter_hora_brasilia()
        
        # Ajustar o horário de entrada para ser exatamente 2 minutos após o envio do sinal
        # E garantir que termine em 0 ou 5
        minuto_atual = hora_entrada.minute
        minuto_entrada = minuto_atual + 2
        
        # Se o minuto não terminar em 0 ou 5, ajustar para o próximo que termine
        ultimo_digito = minuto_entrada % 10
        if ultimo_digito != 0 and ultimo_digito != 5:
            # Calcular quanto falta para o próximo minuto que termine em 0 ou 5
            if ultimo_digito < 5:
                ajuste = 5 - ultimo_digito
            else:
                ajuste = 10 - ultimo_digito
            minuto_entrada += ajuste
        
        # Criar o novo horário de entrada ajustado
        hora_entrada = hora_entrada.replace(minute=minuto_entrada, second=0, microsecond=0)
        BOT2_LOGGER.info(f"[{horario_atual}] Horário de entrada ajustado para {hora_entrada.strftime('%H:%M')} (2 minutos após o sinal + ajuste para terminar em 0 ou 5)")
        
        hora_expiracao = hora_entrada + timedelta(minutes=tempo_expiracao_minutos)
        expiracao_time = hora_expiracao
        
        # Calcular os horários de reentrada (se aplicáveis)
        if tempo_expiracao_minutos >= 15:
            # Reentradas só são relevantes para operações de no mínimo 15 minutos
            hora_reentrada1 = hora_entrada + timedelta(minutes=3)
            hora_reentrada2 = hora_entrada + timedelta(minutes=7)
            hora_reentrada3 = hora_entrada + timedelta(minutes=12)
            
            BOT2_LOGGER.info(f"[{horario_atual}] Horários: Entrada={hora_entrada.strftime('%H:%M:%S')}, Reentrada1={hora_reentrada1.strftime('%H:%M:%S')}, Reentrada2={hora_reentrada2.strftime('%H:%M:%S')}, Reentrada3={hora_reentrada3.strftime('%H:%M:%S')}")
        else:
            BOT2_LOGGER.info(f"[{horario_atual}] Horários: Entrada={hora_entrada.strftime('%H:%M:%S')}, Expiração={hora_expiracao.strftime('%H:%M:%S')}")
        
        BOT2_LOGGER.info(f"[{horario_atual}] SINAL GERADO. Enviando para todos os canais configurados...")
        
        # Formatação da hora para exibição
        hora_formatada = hora_entrada.strftime("%H:%M")
        
        # Enviar para cada canal
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            
            mensagem_formatada = bot2_formatar_mensagem(sinal, hora_formatada, idioma)
            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
            
            # Registrar envio nos logs
            BOT2_LOGGER.info(f"[{horario_atual}] Enviando sinal: Ativo={ativo}, Direção={direcao}, Categoria={categoria}, Tempo={tempo_expiracao_minutos}, Idioma={idioma}")
            
            try:
                resposta = requests.post(url_base, json={
                    "chat_id": chat_id,
                    "text": mensagem_formatada,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }, timeout=10)
                
                if resposta.status_code == 200:
                    BOT2_LOGGER.info(f"[{horario_atual}] ✅ SINAL ENVIADO COM SUCESSO para o canal {chat_id}")
                else:
                    BOT2_LOGGER.error(f"[{horario_atual}] ❌ Erro ao enviar mensagem para o canal {chat_id}: {resposta.text}")
            except Exception as msg_error:
                BOT2_LOGGER.error(f"[{horario_atual}] ❌ Exceção ao enviar mensagem para o canal {chat_id}: {str(msg_error)}")
        
        # Incrementa o contador global de sinais
        bot2_contador_sinais += 1
        BOT2_LOGGER.info(f"[{horario_atual}] Contador de sinais incrementado: {bot2_contador_sinais}")
        
        # Registrar envio no arquivo de registro
        bot2_registrar_envio(ativo, direcao, categoria)
        
        # Cancelar quaisquer agendamentos anteriores para evitar duplicações
        schedule.clear('bot2_pos_sinal')
        schedule.clear('bot2_gif_especial')
        schedule.clear('bot2_promo_especial')
        schedule.clear('bot2_video_pre_sinal')
        schedule.clear('bot2_msg_pre_sinal')
        
        # Ajustar o tempo de agendamento do gif pós-sinal com base no tempo de expiração
        tempo_pos_sinal = 12  # tempo padrão (caso não seja nenhum dos casos específicos)
        
        if categoria == "Blitz":
            # Para Blitz (com expiração em segundos: 5, 10, 15 ou 30), enviar após 4 minutos
            tempo_pos_sinal = 4
            BOT2_LOGGER.info(f"[{horario_atual}] Ativo Blitz com expiração em segundos, agendando gif pós-sinal para daqui a 4 minutos")
        elif tempo_expiracao_minutos == 1:
            tempo_pos_sinal = 5  # 5 minutos após o sinal se expiração for 1 minuto
            BOT2_LOGGER.info(f"[{horario_atual}] Tempo de expiração é 1 minuto, agendando gif pós-sinal para daqui a 5 minutos")
        elif tempo_expiracao_minutos == 2:
            tempo_pos_sinal = 6  # 6 minutos após o sinal se expiração for 2 minutos
            BOT2_LOGGER.info(f"[{horario_atual}] Tempo de expiração é 2 minutos, agendando gif pós-sinal para daqui a 6 minutos")
        elif tempo_expiracao_minutos == 5:
            tempo_pos_sinal = 10  # 10 minutos após o sinal se expiração for 5 minutos
            BOT2_LOGGER.info(f"[{horario_atual}] Tempo de expiração é 5 minutos, agendando gif pós-sinal para daqui a 10 minutos")
        else:
            BOT2_LOGGER.info(f"[{horario_atual}] Tempo de expiração é {tempo_expiracao_minutos} minutos, usando tempo padrão de 12 minutos para gif pós-sinal")
        
        # SEQUÊNCIA DE AGENDAMENTOS:
        # 1. Agendar o gif pós-sinal com o tempo ajustado (enviado para todos os sinais)
        BOT2_LOGGER.info(f"[{horario_atual}] Agendando envio ÚNICO de imagem pós-sinal para daqui a {tempo_pos_sinal} minutos...")
        schedule.every(tempo_pos_sinal).minutes.do(bot2_enviar_gif_pos_sinal).tag('bot2_pos_sinal')
        
        # Se for a cada 3 sinais (múltiplo de 3), agendar sequência completa
        if bot2_contador_sinais % 3 == 0:
            BOT2_LOGGER.info(f"[{horario_atual}] Este é um sinal múltiplo de 3 (contador={bot2_contador_sinais}), agendando sequência completa...")
            
            # Calcular o tempo até o próximo sinal (usado para todos os agendamentos)
            agora = bot2_obter_hora_brasilia()
            proximo_sinal_hora = agora.hour
            proximo_sinal_minuto = 13
            
            # Se já passou do minuto 13 da hora atual, o próximo sinal é na próxima hora
            if agora.minute >= 13:
                proximo_sinal_hora = (agora.hour + 1) % 24
            
            # Calcular o horário do próximo sinal
            proximo_sinal = agora.replace(hour=proximo_sinal_hora, minute=13, second=0, microsecond=0)
            if agora.minute >= 13 and agora.hour == proximo_sinal.hour:
                proximo_sinal = proximo_sinal + timedelta(hours=1)
            
            BOT2_LOGGER.info(f"[{horario_atual}] Próximo sinal será às {proximo_sinal.strftime('%H:%M')}")
            
            # 2. GIF especial PT (apenas para o canal português) - 20 minutos antes do próximo sinal
            tempo_gif_especial = proximo_sinal - timedelta(minutes=20)
            minutos_ate_gif = ((tempo_gif_especial - agora).total_seconds() / 60.0)
            
            # Verificar se é necessário esperar menos de 1 minuto (nesse caso agendar para a próxima hora)
            if minutos_ate_gif < 1:
                tempo_gif_especial = tempo_gif_especial + timedelta(hours=1)
                minutos_ate_gif = ((tempo_gif_especial - agora).total_seconds() / 60.0)
            
            schedule.every(int(minutos_ate_gif)).minutes.do(bot2_enviar_gif_especial_pt).tag('bot2_gif_especial')
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando GIF especial PT para {tempo_gif_especial.strftime('%H:%M')} (20 minutos antes do próximo sinal)")
            
            # 3. Mensagem promocional especial - 19 minutos antes do próximo sinal (1 minuto após o GIF especial)
            tempo_promo = proximo_sinal - timedelta(minutes=19)
            minutos_ate_promo = ((tempo_promo - agora).total_seconds() / 60.0)
            
            # Verificar se é necessário esperar menos de 1 minuto (nesse caso agendar para a próxima hora)
            if minutos_ate_promo < 1:
                tempo_promo = tempo_promo + timedelta(hours=1)
                minutos_ate_promo = ((tempo_promo - agora).total_seconds() / 60.0)
            
            schedule.every(int(minutos_ate_promo)).minutes.do(bot2_enviar_promo_especial).tag('bot2_promo_especial')
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando mensagem promocional especial para {tempo_promo.strftime('%H:%M')} (19 minutos antes do próximo sinal)")
            
            # 4. Vídeo promocional: exatos 15 minutos antes do próximo sinal
            tempo_pre_sinal = proximo_sinal - timedelta(minutes=15)
            minutos_ate_video = ((tempo_pre_sinal - agora).total_seconds() / 60.0)
            
            # Verificar se é necessário esperar menos de 1 minuto (nesse caso agendar para a próxima hora)
            if minutos_ate_video < 1:
                tempo_pre_sinal = tempo_pre_sinal + timedelta(hours=1)
                minutos_ate_video = ((tempo_pre_sinal - agora).total_seconds() / 60.0)
            
            schedule.every(int(minutos_ate_video)).minutes.do(bot2_enviar_promo_pre_sinal).tag('bot2_video_pre_sinal')
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando vídeo promocional para {tempo_pre_sinal.strftime('%H:%M')} (15 minutos antes do próximo sinal)")
            
            # 5. Mensagem pré-sinal: 1 minuto após o vídeo promocional (14 minutos antes do próximo sinal)
            tempo_pre_mensagem = proximo_sinal - timedelta(minutes=14)
            minutos_ate_mensagem = ((tempo_pre_mensagem - agora).total_seconds() / 60.0)
            
            # Verificar se é necessário esperar menos de 1 minuto (nesse caso agendar para a próxima hora)
            if minutos_ate_mensagem < 1:
                tempo_pre_mensagem = tempo_pre_mensagem + timedelta(hours=1)
                minutos_ate_mensagem = ((tempo_pre_mensagem - agora).total_seconds() / 60.0)
            
            schedule.every(int(minutos_ate_mensagem)).minutes.do(bot2_enviar_mensagem_pre_sinal).tag('bot2_msg_pre_sinal')
            BOT2_LOGGER.info(f"[{horario_atual}] Agendando mensagem pré-sinal para {tempo_pre_mensagem.strftime('%H:%M')} (14 minutos antes do próximo sinal)")
    
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
    """Agenda as mensagens do Bot 2 para envio nos intervalos específicos."""
    try:
        if hasattr(bot2_schedule_messages, 'scheduled'):
            BOT2_LOGGER.info("Agendamentos já existentes. Pulando...")
            return

        BOT2_LOGGER.info("Iniciando agendamento de mensagens para o Bot 2")
        
        # Definir o minuto para envio dos sinais (sempre 3 minutos antes de um horário que termina em 0 ou 5)
        # Para terminar em 15, enviar no minuto 13
        minuto_envio = 13
        
        # Agendar 1 sinal por hora, no minuto definido
        for hora in range(0, 24):
            schedule.every().day.at(f"{hora:02d}:{minuto_envio:02d}:02").do(bot2_send_message)
            BOT2_LOGGER.info(f"Sinal agendado: {hora:02d}:{minuto_envio:02d}:02 (horário de entrada: {hora:02d}:15)")

        bot2_schedule_messages.scheduled = True
        BOT2_LOGGER.info("Agendamento de mensagens do Bot 2 concluído com sucesso")
        
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao agendar mensagens: {str(e)}")
        traceback.print_exc()

def iniciar_ambos_bots():
    """Inicializa ambos os bots."""
    try:
        # Configurar logs e inicializar variáveis
        BOT2_LOGGER.info("Iniciando o Bot 2...")
        
        # Definir o horário especial diário para a imagem especial
        definir_horario_especial_diario()
        agendar_redefinicao_horario_especial()
        
        # Remover chamada duplicada que já foi feita no escopo global
        # definir_horario_especial_diario()
        # agendar_redefinicao_horario_especial()
        
        # Inicializar horários ativos
        inicializar_horarios_ativos()

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

    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao inicializar ambos os bots: {str(e)}")
        traceback.print_exc()

def bot2_enviar_mensagem_pre_sinal():
    """
    Envia uma mensagem promocional antes do sinal.
    Esta função é chamada após o envio do vídeo pré-sinal.
    """
    try:
        agora = bot2_obter_hora_brasilia()
        horario_atual = agora.strftime("%H:%M:%S")
        BOT2_LOGGER.info(f"[{horario_atual}] INICIANDO ENVIO DA MENSAGEM PRÉ-SINAL...")

        # Loop para enviar a mensagem para cada canal configurado
        for chat_id in BOT2_CHAT_IDS:
            config_canal = BOT2_CANAIS_CONFIG[chat_id]
            idioma = config_canal["idioma"]
            link_corretora = config_canal["link_corretora"]

            # Mensagem específica para o idioma com o link embutido no texto
            if idioma == "pt":
                mensagem = f"👉🏼Abram a corretora Pessoal\n\n⚠️FIQUEM ATENTOS⚠️\n\n🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n➡️ <a href=\"{link_corretora}\">CLICANDO AQUI</a>"
            elif idioma == "en":
                mensagem = f"👉🏼Open the broker now\n\n⚠️STAY ALERT⚠️\n\n🔥Register on XXBROKER right now🔥\n\n➡️ <a href=\"{link_corretora}\">CLICK HERE</a>"
            elif idioma == "es":
                mensagem = f"👉🏼Abran el corredor ahora\n\n⚠️MANTÉNGANSE ATENTOS⚠️\n\n🔥Regístrese en XXBROKER ahora mismo🔥\n\n➡️ <a href=\"{link_corretora}\">CLIC AQUÍ</a>"
            else:
                mensagem = f"👉🏼Abram a corretora Pessoal\n\n⚠️FIQUEM ATENTOS⚠️\n\n🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n➡️ <a href=\"{link_corretora}\">CLICANDO AQUI</a>"

            # Enviar a mensagem para o canal específico
            url_base = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': mensagem,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }

            resposta = requests.post(url_base, data=payload)

            if resposta.status_code != 200:
                BOT2_LOGGER.error(f"[{horario_atual}] Erro ao enviar mensagem pré-sinal para o canal {chat_id}: {resposta.text}")
            else:
                BOT2_LOGGER.info(f"[{horario_atual}] MENSAGEM PRÉ-SINAL ENVIADA COM SUCESSO para o canal {chat_id}")

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
