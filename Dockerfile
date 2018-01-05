FROM python:alpine3.6

# Update packages
#RUN apk add --update git build-essential git-core libbz2-dev libreadline-dev libsqlite3-dev libssl-dev llvm make zlib1g-dev curl
RUN apk add --update build-base jpeg-dev zlib-dev git redis
ENV LIBRARY_PATH=/lib:/usr/lib

#ENV PYENV_ROOT /root/.pyenv
#ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

#ENV PYTHONDONTWRITEBYTECODE true
#RUN git clone https://github.com/yyuu/pyenv.git /root/.pyenv && \
#cd /root/.pyenv && \
#git checkout `git describe --abbrev=0 --tags`
#RUN pyenv install -v 3.6.3
#RUN pyenv global 3.6.3

# Add and install Python modules
RUN python --version
ADD requirements.txt /src/requirements.txt
RUN cd /src; pip install -r requirements.txt

# Bundle app source
ADD . /src
WORKDIR /src

EXPOSE 5000

CMD ["honcho", "start"]
