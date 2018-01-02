FROM ubuntu:16.04

# Update packages
RUN apt-get update -y

# Install Python Setuptools
RUN apt-get install -y setuptools

# Install pip
RUN easy_install pip

# Add and install Python modules
ADD requirements.txt /src/requirements.txt
RUN cd /src; pip install -r requirements.txt

# Bundle app source
ADD . /src

# Expose
EXPOSE  5000

# Run
CMD ["python", "/src/application.py"]
