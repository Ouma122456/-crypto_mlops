# Use official Jenkins LTS image
FROM jenkins/jenkins:lts

# Switch to root to install packages
USER root

# Install system dependencies with Python (default python)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python \
        python-venv \
        python-pip \
        git \
        curl \
        libgomp1 \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a global Python venv and install DVC as root
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip dvc && \
    chown -R jenkins:jenkins /opt/venv

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Switch back to Jenkins user
USER jenkins
