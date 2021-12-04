#!/bin/bash
sudo cp /home/ec2-user/mhe-backend/mhe-api-backend/.env /home/ec2-user/mhe-backend/mhenv/
sudo cp -r /home/ec2-user/mhe-backend/mhe-api-backend/logs /home/ec2-user/mhe-backend/mhenv/
cd /home/ec2-user/mhe-backend/
sudo rm -rf mhe-api-backend
