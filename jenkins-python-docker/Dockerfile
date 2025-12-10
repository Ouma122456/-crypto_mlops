# Use official Jenkins LTS image
FROM jenkins/jenkins:lts

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        git \
        curl \
        libgomp1 \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a global Python venv and upgrade pip
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip dvc

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Switch back to Jenkins user
USER jenkins
