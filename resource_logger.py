#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 20:57:53 2025
@author: master-yug
"""

import os
import shutil
import psutil
import getpass
import sys
import datetime
import csv
import statistics as st
import sqlite3
import logging

# === Setup Paths ===
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

LOG_FILE = os.path.join(log_dir, "system_metrics.log")
DB_FILE = os.path.join(log_dir, "system_metrics.db")

# === Configure Logging ===
logger = logging.getLogger("ResourceLogger")
logger.setLevel(logging.INFO)
log_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)

# === Database Setup ===
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            timestamp TEXT,
            disk_used REAL,
            disk_free REAL,
            cpu_usage REAL,
            cpu_freq REAL,
            avg_cpu_temp REAL,
            mem_total REAL,
            mem_used REAL,
            mem_free REAL,
            swp_total REAL,
            swp_used REAL,
            swp_free REAL,
            net_bytes_sent INTEGER,
            net_bytes_recv INTEGER,
            net_packets_sent INTEGER,
            net_packets_recv INTEGER,
            net_errors_out INTEGER,
            net_errors_in INTEGER,
            net_packetdrop_out INTEGER,
            net_packetdrop_in INTEGER
        )
    """)
    conn.commit()
    conn.close()

setup_db()

# === Metric Functions ===
def check_disk_data(disk):
    logger.info("disk log:")
    usage = shutil.disk_usage(disk)
    used = round(usage.used / 1073741824, 2)
    free = round(usage.free / 1073741824, 2)
    logger.info(f"used = {used} GB")
    logger.info(f"free = {free} GB\n")
    return used, free

def virtual_memory_data():
    vmd = psutil.virtual_memory()
    total = round(vmd.total / 1073741824, 2)
    used = round(vmd.used / 1073741824, 2)
    free = round(vmd.available / 1073741824, 2)
    logger.info("virtual memory log:")
    logger.info(f"total = {total} GB")
    logger.info(f"used = {used} GB")
    logger.info(f"free = {free} GB")
    logger.info(f"percent = {vmd.percent}%\n")
    return total, used, free

def swap_memory_data():
    smd = psutil.swap_memory()
    total = round(smd.total / 1073741824, 2)
    used = round(smd.used / 1073741824, 2)
    free = round(smd.free / 1073741824, 2)
    logger.info("swap memory log:")
    logger.info(f"total = {total} GB")
    logger.info(f"used = {used} GB")
    logger.info(f"free = {free} GB")
    logger.info(f"percent = {smd.percent}%\n")
    return total, used, free

def cpu_usage_data():
    usage = psutil.cpu_percent(interval=1)
    freq = round(psutil.cpu_freq().current / 1000, 2)
    cores = psutil.cpu_count()
    logger.info("cpu log:")
    logger.info(f"usage = {usage}%")
    logger.info(f"logical cpu's = {cores}")
    logger.info(f"frequency = {freq} GHz\n")
    return usage, freq, cores

def netword_usage_data():
    nud = psutil.net_io_counters()
    logger.info("network log:")
    logger.info(f"bytes sent = {nud.bytes_sent}")
    logger.info(f"bytes received = {nud.bytes_recv}")
    logger.info(f"packets sent = {nud.packets_sent}")
    logger.info(f"packets received = {nud.packets_recv}")
    logger.info(f"errors while sending = {nud.errout}")
    logger.info(f"errors while receiving = {nud.errin}")
    logger.info(f"outgoing packets dropped = {nud.dropout}")
    logger.info(f"incoming packets dropped = {nud.dropin}\n")
    return (
        nud.bytes_sent, nud.bytes_recv, nud.packets_sent, nud.packets_recv,
        nud.errout, nud.errin, nud.dropout, nud.dropin
    )

def temperature_sensors_data():
    tsd = psutil.sensors_temperatures()
    temp_data = {}
    logger.info("temperature log:")
    for category, entries in tsd.items():
        logger.info(f"{category}:")
        temp_data[category] = {}
        for entry in entries:
            label = entry.label or category
            temp_data[category][label] = round(entry.current, 2)
            logger.info(f"  {label} = {entry.current}°C")
    logger.info("")
    return temp_data

def insert_metrics_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

# === Main ===
if __name__ == "__main__":
    try:
        user_name = getpass.getuser()
        now = datetime.datetime.now()
        logger.info(f"USER: {user_name}")
        logger.info(f"Timestamp: {now.isoformat()}")

        disk_data = check_disk_data("/")
        cpu_data = cpu_usage_data()
        mem_data = virtual_memory_data()
        swp_data = swap_memory_data()
        net_data = netword_usage_data()
        temp_data = temperature_sensors_data()

        avg_temp = st.mean(temp_data.get("coretemp", {}).values()) if "coretemp" in temp_data else None

        insert_metrics_to_db((
            now.isoformat(),
            disk_data[0], disk_data[1],
            cpu_data[0], cpu_data[1], avg_temp,
            mem_data[0], mem_data[1], mem_data[2],
            swp_data[0], swp_data[1], swp_data[2],
            *net_data
        ))

        logger.info("Metrics inserted into database successfully.\n")
        print("[✓] Metrics logged successfully.")
    except Exception as e:
        logger.exception("Failed to log metrics.")
        print("[✗] Failed to log metrics. See system_metrics.log for details.")

