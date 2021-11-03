#!/bin/bash
cd /home/ec2-user/mhe-backend/mhe-api-backend
source ../mhenv/bin/activate
python manage.py migrate
#python manage.py loaddata apps/master_data/fixtures/component_fixture.json
service gunicorn restart
service celery restart 
