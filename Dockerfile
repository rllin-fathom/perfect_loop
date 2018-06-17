FROM python:3.6.5-alpine3.7

RUN apk --no-cache add --virtual .builddeps \
    build-base \
    gcc \
    gfortran \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev
ENV LIBRARY_PATH=/lib:/usr/lib
 
RUN pip install \
    numpy

RUN pip install \
    imageio

RUN pip install pytube
RUN python -c 'import imageio; imageio.plugins.ffmpeg.download()'
ADD . /usr/src/app
WORKDIR /usr/src/app
