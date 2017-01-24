FROM python:2.7-alpine

RUN apk update && apk add --no-cache python-dev gcc git g++ make libffi-dev openssl-dev libxml2 libxml2-dev libxslt libxslt-dev

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
CMD fake-switches --model ${SWITCH_MODEL:-cisco_generic} \
                  --hostname ${SWITCH_HOSTNAME:-switch} \
                  --username ${SWITCH_USERNAME:-root} \
                  --password ${SWITCH_PASSWORD:-root} \
                  --listen-host ${LISTEN_HOST:-0.0.0.0} \
                  --listen-port ${LISTEN_PORT:-22}
