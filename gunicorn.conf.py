import os
import multiprocessing

bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8080)}"
workers = multiprocessing.cpu_count()
worker_class = "gevent"
timeout = 120
keepalive = 180
