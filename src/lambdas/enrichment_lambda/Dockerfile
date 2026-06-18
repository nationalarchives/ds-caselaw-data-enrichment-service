FROM public.ecr.aws/lambda/python:3.13@sha256:6b29a28261b892afb364d5246f1d9c6c87e46afc4c99af91635dc4fad6c227f9

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Install dependencies first for layer caching
COPY src/lambdas/enrichment_lambda/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the full src tree so shared packages resolve without a generated copy tree
COPY src/ ${LAMBDA_TASK_ROOT}/

CMD ["lambdas.enrichment_lambda.index.handler"]
