pipeline {
    agent {
        docker { image 'python:3.11-slim' }
    }

    stages {

        stage('Install System Dependencies') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y git gcc build-essential curl
                    pip install --upgrade pip
                    pip install dvc dvc[s3]  # adapte selon ton remote
                '''
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    . venv/bin/activate
                    python train.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    . venv/bin/activate
                    python evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('DVC Pull & Push') {
            steps {
                sh '''
                    . venv/bin/activate
                    dvc pull || echo "No remote data"
                    dvc push || echo "Nothing to push"
                '''
            }
        }
    }

    post {
        always { echo "Pipeline finished" }
    }
}
