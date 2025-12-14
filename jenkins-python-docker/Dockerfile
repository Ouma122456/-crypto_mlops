# Use official Jenkins LTS image
FROM jenkins/jenkins:lts

# Switch to root to install packages
USER root

# Install system dependencies, Python3, Git, curl, and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        libgomp1 \
        build-essential \
        lsb-release \
        gnupg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Docker CLI and Docker Compose
RUN mkdir -p /usr/share/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | \
        gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose-plugin && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Jenkins user to Docker group to allow Docker commands
RUN groupadd -f docker && usermod -aG docker jenkins

# Create a global Python virtual environment and install DVC
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip dvc && \
    chown -R jenkins:jenkins /opt/venv

# Make 'python' command point to 'python3'
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Add virtual environment to PATH for Jenkins
ENV PATH="/opt/venv/bin:$PATH"

# Switch back to Jenkins user
USER jenkins
