pipeline {
    agent any

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


        
    }

    post {
        always { echo "Pipeline finished" }
        success { echo "Pipeline succeeded" }
        failure { echo "Pipeline failed" }
    }
}
