import multiprocessing
import os

os.environ.setdefault("PORT", "8081")
bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8080)}"
workers = multiprocessing.cpu_count()
# worker_class = "gevent"
timeout = 120
keepalive = 180
