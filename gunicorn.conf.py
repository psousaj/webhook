import os
import multiprocessing

bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8000)}"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 4
timeout = 120
keepalive = 180
max_requests = 1000
worker_class = 'sync'
