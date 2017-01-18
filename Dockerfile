FROM python:2-onbuild

RUN PBR_VERSION=0.0.0 pip install .

EXPOSE 22
CMD fake-switches ${SWITCH_MODEL:-cisco_generic} 0.0.0.0 22
