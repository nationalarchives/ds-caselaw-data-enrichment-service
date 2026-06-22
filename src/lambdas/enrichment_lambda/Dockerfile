FROM public.ecr.aws/lambda/python:3.13@sha256:6b29a28261b892afb364d5246f1d9c6c87e46afc4c99af91635dc4fad6c227f9

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install poetry
RUN pip install poetry

# Copy root pyproject.toml and poetry.lock for dependency resolution
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install dependencies with enrichment-lambda group
RUN cd ${LAMBDA_TASK_ROOT} && poetry config virtualenvs.create false && poetry install --with enrichment-lambda --no-root

# Copy lambda code and shared utils/database modules (assembled by make)
COPY src/lambdas/enrichment_lambda/index.py ${LAMBDA_TASK_ROOT}/
COPY src/lambdas/enrichment_lambda/utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY src/lambdas/enrichment_lambda/database/ ${LAMBDA_TASK_ROOT}/database/
COPY src/lambdas/enrichment_lambda/steps.py ${LAMBDA_TASK_ROOT}/
COPY src/lambdas/enrichment_lambda/api.py ${LAMBDA_TASK_ROOT}/

CMD ["index.handler"]
