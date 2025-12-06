pipeline {
    agent any

    stages {
        stage('Setup Python Env') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv venv
                    source venv/bin/activate
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
