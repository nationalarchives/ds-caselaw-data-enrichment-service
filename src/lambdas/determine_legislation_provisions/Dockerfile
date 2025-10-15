FROM public.ecr.aws/lambda/python:3.12@sha256:ef0bbcc9a1cd6cd92be0bb9f0cb28005f0552027f8bbd47de301d48a11742001
# FROM public.ecr.aws/lambda/python:3.12
# Using AWS lambda image for Python 3.6 that can use the pre-built postgress driver library
# FROM lambci/lambda:build-python3.6
# FROM public.ecr.aws/lambda/python:3.6

COPY index.py ${LAMBDA_TASK_ROOT}
# Set the timezone
# ENV TZ=Europe/London
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering out standard
# output stream, which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files, which are unnecessary in this case
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY legislation_provisions_extraction/ ${LAMBDA_TASK_ROOT}/legislation_provisions_extraction/

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# RUN pip install psycopg2-binary==2.9.2 --target "${LAMBDA_TASK_ROOT}"
# RUN wget https://github.com/jkehler/awslambda-psycopg2/archive/refs/heads/master.zip

# RUN pip install aws-psycopg2 --target "${LAMBDA_TASK_ROOT}"

# RUN ls -la ${LAMBDA_TASK_ROOT}/*

CMD [ "index.handler" ]
# CMD [ "index.lambda_handler" ]
