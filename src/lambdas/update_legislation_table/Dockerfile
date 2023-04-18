FROM public.ecr.aws/lambda/python:3.8

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8


RUN yum update -y && \
    rm -Rf /var/cache/yum

COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD [ "index.lambda_handler" ]
