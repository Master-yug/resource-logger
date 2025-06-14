import psutil
import getpass
import datetime
import sqlite3
import os
import time
import statistics as st
import traceback

# --- Configuration
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "system_metrics.log")
DB_FILE = os.path.join(LOG_DIR, "system_metrics.db")
INTERVAL = 30  # seconds

os.makedirs(LOG_DIR, exist_ok=True)


def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
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
            swap_total REAL,
            swap_used REAL,
            swap_free REAL,
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
    return conn


def check_disk_data():
    usage = psutil.disk_usage("/")
    return round(usage.used / 1e9, 2), round(usage.free / 1e9, 2)


def cpu_data():
    return psutil.cpu_percent(), round(psutil.cpu_freq().current / 1000, 2)


def memory_data():
    mem = psutil.virtual_memory()
    return round(mem.total / 1e9, 2), round(mem.used / 1e9, 2), round(mem.available / 1e9, 2)


def swap_data():
    swp = psutil.swap_memory()
    return round(swp.total / 1e9, 2), round(swp.used / 1e9, 2), round(swp.free / 1e9, 2)


def network_data():
    net = psutil.net_io_counters()
    return (net.bytes_sent, net.bytes_recv, net.packets_sent, net.packets_recv,
            net.errout, net.errin, net.dropout, net.dropin)


def temperature_data():
    temps = psutil.sensors_temperatures()
    if "coretemp" in temps:
        readings = [round(t.current, 2) for t in temps["coretemp"] if t.current is not None]
        return round(st.mean(readings), 2) if readings else None
    return None


def log_and_store_metrics(conn):
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()

    disk_used, disk_free = check_disk_data()
    cpu_usage, cpu_freq = cpu_data()
    mem_total, mem_used, mem_free = memory_data()
    swap_total, swap_used, swap_free = swap_data()
    net_stats = network_data()
    avg_cpu_temp = temperature_data()

    # Write to human-readable log file (old style)
    with open(LOG_FILE, "a") as log:
        log.write(f"USER: {getpass.getuser()}\n")
        log.write(f"{timestamp.isoformat()}\n")
        log.write(f"timestamp: {timestamp.timestamp()}\n\n")

        log.write("disk log:\n")
        log.write(f"used = {disk_used} GB\n")
        log.write(f"free = {disk_free} GB\n\n")

        log.write("cpu log:\n")
        log.write(f"usage = {cpu_usage} %\n")
        log.write(f"logical cpu's = {psutil.cpu_count()}\n")
        log.write(f"frequency = {cpu_freq} GHz\n\n")

        log.write("virtual memory log:\n")
        log.write(f"total = {mem_total} GB\n")
        log.write(f"used = {mem_used} GB\n")
        log.write(f"free = {mem_free} GB\n\n")

        log.write("swap memory log:\n")
        log.write(f"total = {swap_total} GB\n")
        log.write(f"used = {swap_used} GB\n")
        log.write(f"free = {swap_free} GB\n\n")

        log.write("network log:\n")
        log.write(f"bytes sent = {net_stats[0]}\n")
        log.write(f"bytes received = {net_stats[1]}\n")
        log.write(f"packets sent = {net_stats[2]}\n")
        log.write(f"packets received = {net_stats[3]}\n")
        log.write(f"errors while sending = {net_stats[4]}\n")
        log.write(f"errors while receiving = {net_stats[5]}\n")
        log.write(f"outgoing packets dropped = {net_stats[6]}\n")
        log.write(f"incoming packets dropped = {net_stats[7]}\n\n")

        log.write("temperature log:\n")
        if avg_cpu_temp is not None:
            log.write(f"average cpu temp = {avg_cpu_temp} °C\n\n")
        else:
            log.write("temperature data not available\n\n")

        log.write("Executed successfully!\n")
        log.write("-" * 50 + "\n\n")

    # Insert into database
    cursor.execute('''
        INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp.isoformat(), disk_used, disk_free, cpu_usage, cpu_freq, avg_cpu_temp,
        mem_total, mem_used, mem_free, swap_total, swap_used, swap_free, *net_stats
    ))
    conn.commit()


# Entry point
if __name__ == "__main__":
    conn = init_database()
    print("Logging system metrics every 30 seconds... Press Ctrl+C to stop.")
    try:
        while True:
            try:
                log_and_store_metrics(conn)
            except Exception as e:
                with open(LOG_FILE, "a") as log:
                    log.write("ERROR GETTING METRICS!\n")
                    log.write(traceback.format_exc())
                    log.write("-" * 50 + "\n\n")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Logging stopped by user.")
        conn.close()

