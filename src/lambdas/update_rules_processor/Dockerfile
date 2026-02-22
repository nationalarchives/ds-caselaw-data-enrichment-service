FROM public.ecr.aws/lambda/python:3.14@sha256:4a260ea82736166accb2cb9fa1b3a180ca1e26cf5f9714e1e382d290ddb4e409

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
