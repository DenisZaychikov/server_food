#!/bin/sh

python manage.py collectstatic --no-input

python manage.py migrate
gunicorn foodgram.wsgi:application --bind 0:8000
