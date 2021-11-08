#!/bin/bash
cd /home/ec2-user/
mkdir debu
sudo cp -r /home/ec2-user/mhe-backend/mhe-api-backend/logs /home/ec2-user/mhe-backend/mhenv/
cd /home/ec2-user/mhe-backend/
sudo rm -rf mhe-api-backend

