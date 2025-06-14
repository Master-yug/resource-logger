import shutil
import psutil
import getpass
import datetime
import traceback
import csv
import statistics as st
import os
import logging

# Configure logging
logging.basicConfig(
    filename="system_metrics.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if not os.path.exists("system_metrics.csv"):
    with open("system_metrics.csv", "w") as f:
        f.write("time,disk_used,disk_free,cpu_usage,cpu_freq,avg_cpu_temp,mem_total,mem_used,mem_free,swp_total,swp_used,swp_free,net_bytes_sent,net_bytes_recv,net_packets_sent,net_packets_recv,net_errors_out,net_errors_in,net_packetdrop_out,net_packetdrop_in\n")

csv_file = open("system_metrics.csv", "a")
csv_w = csv.writer(csv_file)

def check_disk_data(disk):
    cdd = shutil.disk_usage(disk)
    free = round(cdd.free / 1073741824, 2)
    used = round(cdd.used / 1073741824, 2)
    logging.info(f"""Disk log:
  Used = {used} GB
  Free = {free} GB
""")
    return used, free

def virtual_memory_data():
    vmd = psutil.virtual_memory()
    total = round(vmd.total / 1073741824, 2)
    free = round(vmd.available / 1073741824, 2)
    used = round(vmd.used / 1073741824, 2)
    logging.info(f"""Virtual memory log:
  Total = {total} GB
  Used = {used} GB
  Free = {free} GB
  Percent = {vmd.percent}%
""")
    return total, used, free

def swap_memory_data():
    smd = psutil.swap_memory()
    total = round(smd.total / 1073741824, 2)
    used = round(smd.used / 1073741824, 2)
    free = round(smd.free / 1073741824, 2)
    logging.info(f"""Swap memory log:
  Total = {total} GB
  Used = {used} GB
  Free = {free} GB
  Percent = {smd.percent}%
""")
    return total, used, free

def cpu_usage_data():
    usage = psutil.cpu_percent()
    core_count = psutil.cpu_count()
    freq = round(psutil.cpu_freq().current / 1000, 2)
    logging.info(f"""CPU log:
  Usage = {usage}%
  Logical CPUs = {core_count}
  Frequency = {freq} GHz
""")
    return usage, freq, core_count

def network_usage_data():
    nud = psutil.net_io_counters()
    b_sent, b_recv = nud.bytes_sent, nud.bytes_recv
    p_sent, p_recv = nud.packets_sent, nud.packets_recv
    e_sent, e_recv = nud.errout, nud.errin
    pd_out, pd_in = nud.dropout, nud.dropin
    logging.info(f"""Network log:
  Bytes sent = {b_sent}
  Bytes received = {b_recv}
  Packets sent = {p_sent}
  Packets received = {p_recv}
  Errors out = {e_sent}
  Errors in = {e_recv}
  Dropped out = {pd_out}
  Dropped in = {pd_in}
""")
    return b_sent, b_recv, p_sent, p_recv, e_sent, e_recv, pd_out, pd_in

def temperature_sensors_data():
    tsd = psutil.sensors_temperatures()
    temp_data = {}
    lines = ["Temperature log:"]
    for categ in tsd:
        lines.append(f"  {categ}:")
        temp_data[categ] = {}
        for i in tsd[categ]:
            temp = round(i.current, 2)
            label = i.label if i.label else "Unknown"
            temp_data[categ][label] = temp
            lines.append(f"    {label} = {temp}°C")
    logging.info("\n".join(lines) + "\n")
    return temp_data

if __name__ == "__main__":
    try:
        user_name = getpass.getuser()
        curtim = datetime.datetime.now()
        timsta = curtim.timestamp()

        logging.info(f"USER: {user_name}")
        logging.info(f"Timestamp: {curtim.isoformat()}")
        logging.info(f"Unix timestamp: {timsta}")

        disk_data = check_disk_data("/")
        cpu_data = cpu_usage_data()
        mem_data = virtual_memory_data()
        swp_data = swap_memory_data()
        net_data = network_usage_data()
        temp_data = temperature_sensors_data()

        avg_cpu_temp = st.mean(temp_data["coretemp"].values()) if temp_data.get("coretemp") else None

        csv_w.writerow([
            curtim.isoformat(),
            disk_data[0], disk_data[1],
            cpu_data[0], cpu_data[1], avg_cpu_temp,
            mem_data[0], mem_data[1], mem_data[2],
            swp_data[0], swp_data[1], swp_data[2],
            net_data[0], net_data[1], net_data[2], net_data[3],
            net_data[4], net_data[5], net_data[6], net_data[7],
        ])

        logging.info("Executed successfully!")

    except Exception as e:
        logging.error("ERROR GETTING METRICS!")
        logging.error(traceback.format_exc())

    csv_file.close()

