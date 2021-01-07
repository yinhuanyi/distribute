FROM python:3.6
MAINTAINER Robby
WORKDIR /app/fil-distribute
COPY . .
COPY sources.list /etc/apt/
COPY pip.conf /root/.pip/
COPY uwsgi.ini /etc/
COPY ssh_config /etc/ssh/
COPY id_rsa /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa
RUN apt-get update && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
# RUN python manage.py collectstatic --noinput
EXPOSE 8007/tcp
ENTRYPOINT ["bash", "/app/fil-distribute/entrypoint.sh"]