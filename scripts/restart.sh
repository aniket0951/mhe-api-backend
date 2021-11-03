#!/bin/bash
sudo cp /home/ec2-user/mhe-backend/mhenv/.env /home/ec2-user/mhe-backend/mhe-api-backend/
cd /home/ec2-user/mhe-backend/mhe-api-backend/
sudo chomd 777 -R .
source ../mhenv/bin/activate
python manage.py migrate
#python manage.py loaddata apps/master_data/fixtures/component_fixture.json
sudo service gunicorn restart
sudo service celery restart 
