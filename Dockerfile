# Base image ubi10
FROM nix-docker.registry.twcstorage.ru/base/redhat/ubi10-minimal:10.1000-1766033715@sha256:05edf453b46e8f615ddad5bbeb3acebc4fbe3d467e2642d14cf43defd2b9465d
# Add extra packages repo
COPY epel.repo /etc/yum.repos.d/
# Install python and necesary libs
RUN microdnf update -y && \
    microdnf install -y && \
    python3.13 \
    python3.13-devel \
    python3.13-pip \
    gcc \
    gcc-c++ \
    make \
    zlib-devel \
    bzip2-devel \
    openssl-devel \
    ncurses-devel \
    sqlite-devel \
    tk-devel \
    libpcap-devel \
    xz-devel \
    libffi-devel \
    wget \
    tar \
    && microdnf clean all

# Set the HOME environment variable to /app
ENV HOME=/app
# Set the config folder (relative to HOME)
ARG APP_CONFIG_DIR
ENV APP_CONFIG_DIR=${APP_CONFIG_DIR}
# Set the name of config file (without extension)
ARG APP_CONFIG_NAME
ENV APP_CONFIG_NAME=${APP_CONFIG_NAME}

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Create venv with Python 3.13
RUN python3.13 -m venv /app/venv

# Set the PATH to venv
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip==25.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the FILE_PATH env to specify which operator to run
ARG FILE_PATH
ENV FILE_PATH=${FILE_PATH}

# Set the namespace
ARG NAMESPACE
ENV NAMESPACE=${NAMESPACE}

# Run specified operator
CMD ["sh", "-c", "python -m kopf run -n $NAMESPACE $FILE_PATH"]