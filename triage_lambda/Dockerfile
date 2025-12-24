# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first for better caching
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/ ${LAMBDA_TASK_ROOT}/agent/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY triage_processor.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "lambda_handler.lambda_handler" ]

