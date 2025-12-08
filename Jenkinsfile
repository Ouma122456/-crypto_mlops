pipeline {
    agent any  // Utilise le conteneur Jenkins lui-même

    environment {
        PATH = "/opt/venv/bin:$PATH"  // Utilise le venv global de ton Dockerfile
    }

    stages {

        stage('Setup Python Env') {
            steps {
                sh '''
                    python3 --version
                    pip install --upgrade pip
                    pip install -r requirements.txt || echo "Dependencies already installed"
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                sh '''
                    python src/models/train1.py
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                sh '''
                    python evaluate.py || echo "No evaluation script found"
                '''
            }
        }

        stage('DVC Pull & Push') {
            steps {
                sh '''
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
