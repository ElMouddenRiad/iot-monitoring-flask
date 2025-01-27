import psutil as ps

ps.cpu_percent()
ps.virtual_memory()
ps.disk_usage('/')
ps.disk_partitions()
ps.sensors_temperatures()