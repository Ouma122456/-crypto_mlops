pipeline {
    agent any

    environment {
        PYTHON = "/usr/bin/python3"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                    python3 --version
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    echo "Running model training..."
                    python train.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    echo "Running evaluation..."
                    python evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('DVC Pull & Push') {
            steps {
                sh '''
                    echo "Sync with DVC storage..."
                    dvc pull || echo "No remote data"
                    dvc push || echo "Nothing to push"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished"
        }
    }
}
