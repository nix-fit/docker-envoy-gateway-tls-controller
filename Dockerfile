# Use UBI 9.6 as the base image
FROM nix-docker.registry.twcstorage.ru/base/redhat/ubi10-minimal:10.1000-1766033715@sha256:05edf453b46e8f615ddad5bbeb3acebc4fbe3d467e2642d14cf43defd2b9465d
# Include python3.13-devel if Python headers are needed for some packages
# This step assumes python3.13 is available via dnf. If not, you need to install Python 3.13 first (e.g., compile from source).
COPY epel.repo /etc/yum.repos.d/
RUN microdnf update -y && \
    # Example: Install Python 3.13 if available via dnf. Replace with actual package name if different.
    microdnf install -y python3.13 python3.13-devel python3.13-pip \
    # Or, if Python 3.13 was compiled/installed manually in a previous step, ensure it's accessible.
    # For this example, let's assume 'python3.13' is the command and 'pip3.13' is available.
    # Install other common build tools needed by pip install
    # dnf install -y \
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
ENV APP_CONFIG_DIR=/config
ENV APP_CONFIG_NAME=config

# Create a directory for your application and set it as the working directory
WORKDIR /app

# Copy your requirements.txt file into the image
COPY requirements.txt .

# Create a virtual environment using Python 3.13
# Replace 'python3.13' with the correct command if your Python 3.13 installation differs
RUN python3.13 -m venv /app/venv

# Make sure we use the virtual environment's pip
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip within the virtual environment (recommended)
RUN pip install --upgrade pip

# Install dependencies from requirements.txt using the virtual environment's pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code into the image
# Adjust the source path ('.') as needed
COPY . .
ENV FILE_PATH="/app/src/certificate/certificate.py"
# Set the default command to activate the virtual environment and run your app
# Option 1: Run a specific Python script
# CMD ["python", "your_main_script.py"]
# Option 2: Start a bash shell with the virtual environment activated (for testing)
# CMD ["/bin/bash"]
# Option 3: Run Python interactively
CMD ["sh", "-c", "python -m kopf run $FILE_PATH"]