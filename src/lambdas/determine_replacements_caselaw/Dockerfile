
FROM public.ecr.aws/lambda/python:3.14@sha256:1d0cad71b5395890e26f9db490af5414ad208f49ea1f7c54241ecc4a22d9f30a

COPY index.py ${LAMBDA_TASK_ROOT}
# Set the timezone
# ENV TZ=Europe/London
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering out standard
# output stream, which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files, which are unnecessary in this case
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY database/ ${LAMBDA_TASK_ROOT}/database/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY caselaw_extraction/ ${LAMBDA_TASK_ROOT}/caselaw_extraction/
# COPY caselaw_extraction/rules/citation_patterns.jsonl ${LAMBDA_TASK_ROOT}/caselaw_extraction/rules/citation_patterns.jsonl
COPY citation_patterns.jsonl ${LAMBDA_TASK_ROOT}

# COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
# COPY requirements.txt .

RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# RUN pip install psycopg2-binary==2.9.2 --target "${LAMBDA_TASK_ROOT}"
# RUN wget https://github.com/jkehler/awslambda-psycopg2/archive/refs/heads/master.zip

# RUN pip install aws-psycopg2 --target "${LAMBDA_TASK_ROOT}"

# RUN ls -la ${LAMBDA_TASK_ROOT}/*

CMD [ "index.handler" ]
# CMD [ "index.lambda_handler" ]
