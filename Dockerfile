FROM python:2.7-alpine

RUN apk update
RUN apk add python-dev gcc g++ make libffi-dev openssl-dev libxml2 libxml2-dev libxslt libxslt-dev

# 
# NOTE(mmitchell): Mimick -onbuild using -alpine image.
#                  ONBUILD statements removed because this is an actual Dockerfile
#
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app
#
# End of -onbuild copied commands.
#

RUN PBR_VERSION=0.0.0 pip install .

EXPOSE 22
CMD fake-switches ${SWITCH_MODEL:-cisco_generic} 0.0.0.0 22
