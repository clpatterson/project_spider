#!bin/bash
sudo yum update -y

# Install python 3.6
sudo yum install python36 -y

# Create virtualenv directory and create new venv
mkdir venv
cd venv
virtualenv -p /usr/bin/python3.6 python36 -y

# Activate virtual environment
source /home/ec2-user/venv/python36/bin/activate

# For taking it down
deactivate

sudo yum install git -y

sudo pip install mtools --upgrade -y
sudo yum install python-devel -y
sudo pip install pymongo -y
sudo yum install python36-devel -y

# And then there was successful installation! 

# Install docker
sudo yum install docker -y
sudo service docker start
