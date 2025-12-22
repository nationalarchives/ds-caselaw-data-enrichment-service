
FROM public.ecr.aws/lambda/python:3.14@sha256:834867e65287508faae9d0706181e3e5c72fe8d9b99319c6ab1096ce1494c4a4

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
COPY abbreviation_extraction/ ${LAMBDA_TASK_ROOT}/abbreviation_extraction/

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# RUN pip install psycopg2-binary==2.9.2 --target "${LAMBDA_TASK_ROOT}"
# RUN wget https://github.com/jkehler/awslambda-psycopg2/archive/refs/heads/master.zip

# RUN pip install aws-psycopg2 --target "${LAMBDA_TASK_ROOT}"

# RUN ls -la ${LAMBDA_TASK_ROOT}/*

CMD [ "index.handler" ]
# CMD [ "index.lambda_handler" ]
