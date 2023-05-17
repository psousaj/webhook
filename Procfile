web: gunicorn webhook.wsgi
worker: celery -A webhook.celery --broker=$CLOUDAMQP_IVORY_URL worker -l info
 

