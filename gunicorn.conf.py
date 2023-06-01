import os


bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8000)}"
workers = 4
timeout = 120
keepalive = 60
