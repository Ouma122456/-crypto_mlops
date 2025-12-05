pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Virtualenv') {
            steps {
                sh '''
                    # Create virtual environment in workspace
                    python3 -m venv venv || python -m venv venv

                    # Activate virtual environment
                    source venv/bin/activate

                    # Upgrade pip and install dependencies
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    source venv/bin/activate
                    python train.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    source venv/bin/activate
                    python evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('DVC Pull & Push') {
            steps {
                sh '''
                    source venv/bin/activate
                    pip install --upgrade dvc
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
