# sys_monitor.py
import psutil
import time
from datetime import datetime


# monitor result to graph
def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    mem = psutil.virtual_memory()
    return mem.percent, mem.used / (1024 ** 3), mem.total / (1024 ** 3)  # in GB

def get_disk_usage():
    disk = psutil.disk_usage('/')
    return disk.percent, disk.used / (1024 ** 3), disk.total / (1024 ** 3)  # in GB

def get_network_io():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent / (1024 ** 2), net_io.bytes_recv / (1024 ** 2)  # in MB

def get_system_status():
    print("----- System Status -----")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # CPU Usage
    cpu_usage = get_cpu_usage()
    print(f"CPU Usage: {cpu_usage}%")

    # Memory Usage
    mem_usage, mem_used, mem_total = get_memory_usage()
    print(f"Memory Usage: {mem_usage}% ({mem_used:.2f} GB / {mem_total:.2f} GB)")

    # Disk Usage
    disk_usage, disk_used, disk_total = get_disk_usage()
    print(f"Disk Usage: {disk_usage}% ({disk_used:.2f} GB / {disk_total:.2f} GB)")

    # Network I/O
    net_sent, net_recv = get_network_io()
    print(f"Network Sent: {net_sent:.2f} MB, Received: {net_recv:.2f} MB")

    print("------------------------" * 5)

def monitor_system(interval=5):
    try:
        while True:
            get_system_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")

if __name__ == "__main__":
    monitor_interval = 5  # Set the interval in seconds
    monitor_system(monitor_interval)
