FROM public.ecr.aws/lambda/python:3.13@sha256:5dd3e2c637709e8437ef7b2ea42ebeee9824e62d2f6ba7afe788a4fd6e2a96f0@sha256:5dd3e2c637709e8437ef7b2ea42ebeee9824e62d2f6ba7afe788a4fd6e2a96f0@sha256:5dd3e2c637709e8437ef7b2ea42ebeee9824e62d2f6ba7afe788a4fd6e2a96f0

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
