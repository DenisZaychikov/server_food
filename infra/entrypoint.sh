#!/bin/sh

python manage.py collectstatic --no-input
cp -r collected_static/. static/
python manage.py migrate
gunicorn foodgram.wsgi:application --bind 0:8000
