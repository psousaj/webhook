# import os
# from dotenv import load_dotenv
# from celery import Celery
# from django.conf import settings

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webhook.settings')
# load_dotenv()


# app = Celery('Woz')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# # Configurando a URL do broker
# # app.conf.broker_url = os.getenv('CLOUDAMQP_URL_ADDON')
# app.conf.broker_url = 'amqps://kupfasrh:gNX6KeINaO4yTLJOCDBGXU-O0vCKMN2v@chimpanzee.rmq.cloudamqp.com/kupfasrh'
# # broker_url = os.getenv('CLOUDAMQP_URL_ADDON')
# broker_pool_limit = 1  # Will decrease connection usage
# broker_heartbeat = None  # We're using TCP keep-alive instead
# # May require a long timeout due to Linux DNS timeouts etc
# broker_connection_timeout = 30
# # AMQP is not recommended as result backend as it creates thousands of queues
# result_backend = None
# # Will delete all celeryev. queues without consumers after 1 minute.
# event_queue_expires = 60
# # Disable prefetching, it's causes problems and doesn't help performance
# worker_prefetch_multiplier = 1
# # If you tasks are CPU bound, then limit to the number of cores, otherwise increase substainally
# worker_concurrency = 4


# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')

# # command line:
# # celery -A woz.celery worker --without-heartbeat --without-mingle
# # celery -A woz.celery flower --broker=amqps://ifauiewm:gCoxtoOaOB5bMvPVeBmD6njA6sr8AdIp@gull.rmq.cloudamqp.com/ifauiewm?ssl=true
