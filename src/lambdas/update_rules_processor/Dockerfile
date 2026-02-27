FROM public.ecr.aws/lambda/python:3.14@sha256:1ba8368078c8f9148ecf0d6e6efea21ead88fe49e2ba4c9ea8de102ac8308b12

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
