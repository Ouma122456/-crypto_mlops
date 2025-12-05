pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    #!/bin/bash

                    # Check if python3 exists
                    if ! command -v python3 &> /dev/null
                    then
                        echo "Python3 not found. Installing..."
                        sudo apt-get update
                        sudo apt-get install -y python3 python3-pip
                    else
                        echo "Python3 found"
                    fi

                    python3 --version
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    echo "Running model training..."
                    python3 train.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    echo "Running evaluation..."
                    python3 evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('DVC Pull & Push') {
            steps {
                sh '''
                    echo "Sync with DVC storage..."
                    pip3 install --upgrade dvc
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
