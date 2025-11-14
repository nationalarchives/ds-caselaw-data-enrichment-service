FROM public.ecr.aws/lambda/python:3.14@sha256:e78bf9180c4f3356cd7a1a056e6a8a841196ccbad1cb8090c2a9e0a6ad6bfd1c

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY replacer/ ${LAMBDA_TASK_ROOT}/replacer/
COPY oblique_references/ ${LAMBDA_TASK_ROOT}/oblique_references/

CMD [ "index.handler" ]
