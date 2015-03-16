#!/bin/sh

cp kuaileticao.com /etc/nginx/site-available/
ln -s /etc/nginx/site-available/kuaileticao.com /etc/nginx/site-enable/

mkdir /var/log/nginx
mkdir /var/log/nginx/kuaileticao.com
mkdir /var/log/celery
mkdir /var/run/celery
chown -R kltc:kltc /var/log/celery
chown -R kltc:kltc /var/run/celery

cp celery /etc/sysconfig/
cp celerybeat /etc/sysconfig/
cp uwsgi.ini /etc/uwsgi/kuaileticao.uwsgi.ini
cp kuaileticao.service /etc/systemd/system/
cp celery.service /etc/systemd/system/
cp celerybeat.service /etc/systemd/system/

systemctl restart kuaileticao
systemctl enable kuaileticao
systemctl restart nginx
systemctl restart celery
systemctl enable celery
systemctl restart celerybeat
systemctl enable celerybeat
