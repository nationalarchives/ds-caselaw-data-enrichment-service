# FROM public.ecr.aws/lambda/python:3.9
FROM public.ecr.aws/lambda/python:3.8
# Using AWS lambda image for Python 3.6 that can use the pre-built postgress driver library
# FROM lambci/lambda:build-python3.6


# Set the timezone
# ENV TZ=Europe/London
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering out standard
# output stream, which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files, which are unnecessary in this case
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8


RUN yum update -y && \
    rm -Rf /var/cache/yum

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# RUN pip install psycopg2-binary==2.9.2 --target "${LAMBDA_TASK_ROOT}"
# RUN wget https://github.com/jkehler/awslambda-psycopg2/archive/refs/heads/master.zip

# RUN pip install aws-psycopg2 --target "${LAMBDA_TASK_ROOT}"

COPY index.py ${LAMBDA_TASK_ROOT}

CMD [ "index.lambda_handler" ]
