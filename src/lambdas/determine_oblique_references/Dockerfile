FROM public.ecr.aws/lambda/python:3.14@sha256:2c82ed8cd633a5b4613016f1dc422109e6cd06998a33671f2a4fc5c3a8d13100

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY oblique_references/ ${LAMBDA_TASK_ROOT}/oblique_references/

CMD [ "index.handler" ]
