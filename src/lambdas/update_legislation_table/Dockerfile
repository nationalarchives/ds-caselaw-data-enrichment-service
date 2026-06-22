FROM public.ecr.aws/lambda/python:3.13@sha256:759c0bc7c7f9b6b68f2e8e28590815585b3073f500d2831f58c24c0e54401ae5

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install poetry
RUN pip install poetry

# Copy root pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies with legislation-lambda group
RUN cd ${LAMBDA_TASK_ROOT} && poetry config virtualenvs.create false && poetry install --with legislation-lambda --no-root

# Copy lambda code and shared utils/database modules (assembled by make)
COPY src/lambdas/update_legislation_table/index.py ${LAMBDA_TASK_ROOT}/
COPY src/lambdas/update_legislation_table/utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY src/lambdas/update_legislation_table/database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
