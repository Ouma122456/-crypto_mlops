pipeline {
    agent any

    environment {
        AWS_ACCESS_KEY_ID     = credentials('dagshub-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('dagshub-secret-key')
    }

    stages {

        stage('Checkout') {
            steps {
                deleteDir()
                git branch: 'main',
                    url: 'https://dagshub.com/Ouma122456/crypto_mlops',
                    credentialsId: 'dagshub-cred'
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                    python --version
                    python -m venv venv_local
                    . venv_local/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    dvc version
                '''
            }
        }

        stage('Pull Data with DVC') {
            steps {
                sh '''
                    . venv_local/bin/activate
                    dvc pull
                    ls -lh data || true
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    . venv_local/bin/activate
                    export PYTHONPATH=$PYTHONPATH:$WORKSPACE/src
                    python src/models/train1.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    . venv_local/bin/activate
                    python evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv_local/bin/activate
                    export PYTHONPATH=$PYTHONPATH:$WORKSPACE/src
                    pytest -v tests/test_app.py
                '''
            }
        }
    }

    post {
        always  { echo "Pipeline finished" }
        success { echo "Pipeline succeeded" }
        failure { echo "Pipeline failed" }
    }
}
