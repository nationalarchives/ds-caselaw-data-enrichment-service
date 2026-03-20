FROM public.ecr.aws/lambda/python:3.14@sha256:67ed6888e49f2dcd3f4aee9ed70c6d08628dab49cbcf2a3d83db08d6df7ab9ae

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8

# Copy only the requirements file first and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY database/ ${LAMBDA_TASK_ROOT}/database/

CMD [ "index.lambda_handler" ]
