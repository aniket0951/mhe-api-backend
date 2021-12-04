#!/bin/bash
sudo cp /home/ec2-user/mhe-backend/mhenv/.env /home/ec2-user/mhe-backend/mhe-api-backend/
sudo cp -r /home/ec2-user/mhe-backend/mhenv/logs /home/ec2-user/mhe-backend/mhe-api-backend/
cd /home/ec2-user/mhe-backend/mhe-api-backend/
sudo chmod 777 -R .
source ../mhenv/bin/activate
python manage.py migrate
python manage.py loaddata apps/master_data/fixtures/hospitals.json
sudo service gunicorn restart
sudo service celery restart 