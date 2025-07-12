FROM public.ecr.aws/lambda/python:3.12@sha256:d6eeb6f1c2a0dbaa4c7bb743c1c2354d0d32a5e64a0cbdf85d1016f861f9d974

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
