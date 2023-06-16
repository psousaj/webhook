import os
import multiprocessing
from dynoscale.hooks.gunicorn import pre_request  # noqa # pylint: disable=unused-import

bind = "0.0.0.0:" + f"{os.environ.get('PORT', 8000)}"
workers = multiprocessing.cpu_count()
worker_class = "gevent"
timeout = 120
keepalive = 180
