FROM python:3.10-slim-buster

# Instala dependências do sistema operacional
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libmariadb-dev \
        libssl-dev \
        libffi-dev \
        pkg-config \
        # default-libmysqlclient-dev \
        locales \
        supervisor \
        openssh-client \
        nano
        


# Configura a localização para pt_BR.UTF-8
RUN sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

#Configura a chave SSH para o serveo
RUN ssh-keygen -t rsa -b 2048 -N "" -f /root/.ssh/chave_rsa

# Cria e muda para o diretório /woz
RUN mkdir /webhook
WORKDIR /webhook

# Copia o arquivo poetry.lock para o diretório /woz
COPY requirements.txt .

# Copia o código-fonte do projeto para o diretório /woz
COPY . .

# Configura as variáveis de ambiente
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0
ENV LANG pt_BR.UTF-8

# Instalação do servidor Gunicorn e Flower
RUN pip install flower
RUN pip install -r requirements.txt

# Executa as migrações do banco de dados
RUN python manage.py collectstatic --no-input

# Copia o script para iniciar o Celery para dentro da imagem
# COPY celery_entrypoint.sh /celery_entrypoint.sh
COPY celery.conf /etc/supervisor/conf.d/celery.conf

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/celery.conf"]
