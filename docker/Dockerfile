FROM python:3.6.5-alpine3.7

RUN apk add --update ffmpeg

# Add and install Python modules
ADD requirements.txt /src/requirements.txt
RUN cd /src; pip install -r requirements.txt
