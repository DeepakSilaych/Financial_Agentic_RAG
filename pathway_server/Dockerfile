FROM python:3.11-slim

WORKDIR /app

# Setup env
ENV LANG C.UTF-8 \
  LC_ALL C.UTF-8 \
  PYTHONDONTWRITEBYTECODE 1 \
  PYTHONFAULTHANDLER 1 \
  PYTHONUNBUFFERED 1 \
  PYTHONHASHSEED random \
  PIP_NO_CACHE_DIR on \
  PIP_DISABLE_PIP_VERSION_CHECK on

# Install system dependencies
RUN apt update && apt install -y --no-install-recommends \
  tesseract-ocr-eng \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt ./
# Install the dependencies (use cpu version of pytorch as we are not using GPU)
RUN pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Install application into container
COPY . .

EXPOSE 7000

# Run the application
CMD ["python", "-m", "vector_store"]
