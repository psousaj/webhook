import os
import socket
from celery import Celery
from dotenv import load_dotenv
from django.conf import settings

def is_local_machine() -> bool:
    def handle_env_file(is_localhost:bool):
        with open('.env', 'r') as f:
            lines = f.readlines()
        with open('.env', 'w') as file:
            for line in lines:
                if line.startswith("IS_LOCALHOST"):
                    file.write(f"IS_LOCALHOST={is_localhost}\n")
                else:
                    file.write(line)

    host_name = socket.gethostname()
    is_localhost = host_name in ("localhost", "127.0.0.1", "docker", "servidor")
    if is_localhost:
        handle_env_file(True)
    else:
        handle_env_file(False)

    print("IS_LOCALHOST", is_localhost, f"from host: {host_name}")


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webhook.settings')
load_dotenv()

app = Celery('webhook')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configurando a URL do broker
app.conf.broker_url = os.environ.get(
    'CLOUDAMQP_URL', os.getenv('CLOUDAMQP_URL'))
# broker_url = os.getenv('CLOUDAMQP_URL_ADDON')
broker_pool_limit = 1  # Will decrease connection usage
broker_heartbeat = None  # We're using TCP keep-alive instead
# May require a long timeout due to Linux DNS timeouts etc
broker_connection_timeout = 30
# AMQP is not recommended as result backend as it creates thousands of queues
result_backend = None
# Will delete all celeryev. queues without consumers after 1 minute.
event_queue_expires = 60
# Disable prefetching, it's causes problems and doesn't help performance
worker_prefetch_multiplier = 1
# If you tasks are CPU bound, then limit to the number of cores, otherwise increase substainally
worker_concurrency = 4

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

#Verifica se a máquina é local
is_local_machine()