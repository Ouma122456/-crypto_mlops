# Use official Jenkins LTS image
FROM jenkins/jenkins:lts

# Switch to root to install packages
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        git \
        curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a global virtual environment for Python packages
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip dvc

# Make venv binaries available in PATH for Jenkins user
ENV PATH="/opt/venv/bin:$PATH"

# Switch back to Jenkins user
USER jenkins

