import os
import csv
import time
import psutil
import shutil
import sqlite3
import getpass
import datetime
import statistics as st
import logging
import configparser

def load_config(path='config.ini'):
    config = configparser.ConfigParser()
    config.read(path)
    
    logging_config = {
        'interval': config.getint('logging', 'interval', fallback=30),
        'log_to_file': config.getboolean('logging', 'log_to_file', fallback=True),
        'log_to_csv': config.getboolean('logging', 'log_to_csv', fallback=True),
        'log_to_db': config.getboolean('logging', 'log_to_db', fallback=True)
    }
    
    alerts_config = {
        'enable_alerts': config.getboolean('alerts', 'enable_alerts', fallback=False),
        'cpu_threshold': config.getint('alerts', 'cpu_threshold', fallback=90),
        'mem_threshold': config.getint('alerts', 'mem_threshold', fallback=80)
    }
    
    return logging_config, alerts_config

# Setup Logging
logging.basicConfig(
    filename="system_metrics.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger()

# SQLite setup
db_path = "system_metrics.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        timestamp TEXT,
        disk_used REAL,
        disk_free REAL,
        cpu_usage REAL,
        cpu_freq REAL,
        logical_cpus INTEGER,
        avg_cpu_temp REAL,
        mem_total REAL,
        mem_used REAL,
        mem_free REAL,
        mem_percent REAL,
        swp_total REAL,
        swp_used REAL,
        swp_free REAL,
        swp_percent REAL,
        net_bytes_sent INTEGER,
        net_bytes_recv INTEGER,
        net_packets_sent INTEGER,
        net_packets_recv INTEGER,
        net_errors_out INTEGER,
        net_errors_in INTEGER,
        net_packetdrop_out INTEGER,
        net_packetdrop_in INTEGER
    )
''')
conn.commit()

# CSV setup
if not os.path.exists("system_metrics.csv"):
    with open("system_metrics.csv", "w") as f:
        f.write("time,disk_used,disk_free,cpu_usage,cpu_freq,logical_cpus,avg_cpu_temp,mem_total,mem_used,mem_free,mem_percent,swp_total,swp_used,swp_free,swp_percent,net_bytes_sent,net_bytes_recv,net_packets_sent,net_packets_recv,net_errors_out,net_errors_in,net_packetdrop_out,net_packetdrop_in\n")

csv_file = open("system_metrics.csv", "a")
csv_writer = csv.writer(csv_file)

def collect_and_log(log_to_file=True, log_to_csv=True, log_to_db=True):
    try:
        user = getpass.getuser()
        now = datetime.datetime.now()

        # Disk
        disk = shutil.disk_usage("/")
        disk_used = round(disk.used / 1073741824, 2)
        disk_free = round(disk.free / 1073741824, 2)

        # CPU
        cpu_usage = psutil.cpu_percent()
        cpu_freq = round(psutil.cpu_freq().current / 1000, 2)
        logical_cpus = psutil.cpu_count()

        # Memory
        mem = psutil.virtual_memory()
        mem_total = round(mem.total / 1073741824, 2)
        mem_used = round(mem.used / 1073741824, 2)
        mem_free = round(mem.available / 1073741824, 2)

        # Swap
        swap = psutil.swap_memory()
        swp_total = round(swap.total / 1073741824, 2)
        swp_used = round(swap.used / 1073741824, 2)
        swp_free = round(swap.free / 1073741824, 2)

        # Network
        net = psutil.net_io_counters()

        # Temperature
        temps = psutil.sensors_temperatures()
        cpu_temps = temps.get("coretemp") or temps.get("k10temp") or []
        temp_vals = [round(t.current, 2) for t in cpu_temps if t.current is not None]
        avg_temp = round(st.mean(temp_vals), 2) if temp_vals else None

        # Log to file
        if log_to_file:
            logger.info(f"USER: {user}")
            logger.info(f"Timestamp: {now.isoformat()}")
            logger.info("Disk log:")
            logger.info(f"  Used = {disk_used} GB")
            logger.info(f"  Free = {disk_free} GB")
            logger.info("CPU log:")
            logger.info(f"  Usage = {cpu_usage}%")
            logger.info(f"  Frequency = {cpu_freq} GHz")
            logger.info(f"  Logical CPUs = {logical_cpus}")
            logger.info("Memory log:")
            logger.info(f"  Total = {mem_total} GB")
            logger.info(f"  Used = {mem_used} GB")
            logger.info(f"  Free = {mem_free} GB")
            logger.info(f"  Percent = {mem.percent}%")
            logger.info("Swap log:")
            logger.info(f"  Total = {swp_total} GB")
            logger.info(f"  Used = {swp_used} GB")
            logger.info(f"  Free = {swp_free} GB")
            logger.info(f"  Percent = {swap.percent}%")
            logger.info("Network log:")
            logger.info(f"  Bytes sent = {net.bytes_sent}")
            logger.info(f"  Bytes received = {net.bytes_recv}")
            logger.info(f"  Packets sent = {net.packets_sent}")
            logger.info(f"  Packets received = {net.packets_recv}")
            logger.info(f"  Errors out = {net.errout}")
            logger.info(f"  Errors in = {net.errin}")
            logger.info(f"  Dropped out = {net.dropout}")
            logger.info(f"  Dropped in = {net.dropin}")
            logger.info("Temperature log:")
            for name, sensors in temps.items():
                logger.info(f"  {name}:")
                for s in sensors:
                    logger.info(f"    {s.label or 'N/A'} = {s.current}°C")

        # Write to CSV
        if log_to_csv:
            csv_writer.writerow([
                now.isoformat(), disk_used, disk_free, cpu_usage, cpu_freq, logical_cpus, avg_temp,
                mem_total, mem_used, mem_free, mem.percent,
                swp_total, swp_used, swp_free, swap.percent,
                net.bytes_sent, net.bytes_recv, net.packets_sent, net.packets_recv,
                net.errout, net.errin, net.dropout, net.dropin
            ])

        # Write to DB
        if log_to_db:
            cursor.execute(
                '''INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                [
                    now.isoformat(), disk_used, disk_free, cpu_usage, cpu_freq, logical_cpus, avg_temp,
                    mem_total, mem_used, mem_free, mem.percent,
                    swp_total, swp_used, swp_free, swap.percent,
                    net.bytes_sent, net.bytes_recv, net.packets_sent, net.packets_recv,
                    net.errout, net.errin, net.dropout, net.dropin
                ]
            )
            conn.commit()

        print("Metrics logged successfully.")

    except Exception as e:
        logger.error("Failed to log metrics:", exc_info=True)
        print("Logging failed. Check system_metrics.log.")

if __name__ == "__main__":
    logging_config, alerts_config = load_config()

    interval = logging_config['interval']
    log_to_file = logging_config['log_to_file']
    log_to_csv = logging_config['log_to_csv']
    log_to_db = logging_config['log_to_db']

    print(f"Logging every {interval} seconds: file={log_to_file}, csv={log_to_csv}, db={log_to_db}")
    
    while True:
        collect_and_log(log_to_file, log_to_csv, log_to_db)
        time.sleep(interval)

