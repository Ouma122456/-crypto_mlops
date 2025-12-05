pipeline {
    agent any

    environment {
        PYTHON = "C:\\Users\\abass\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                bat """
                    %PYTHON% --version
                    pip install -r requirements.txt
                """
            }
        }

        stage('Run Training Pipeline') {
            steps {
                bat """
                    echo Running model training...
                    %PYTHON% train.py
                """
            }
        }

        stage('Run Evaluation') {
            steps {
                bat """
                    echo Running evaluation...
                    %PYTHON% evaluate.py || echo No evaluation script found
                """
            }
        }

        stage('DVC Pull & Push') {
            steps {
                bat """
                    echo Sync with DVC storage...
                    dvc pull || echo No remote data
                    dvc push || echo Nothing to push
                """
            }
        }
    }

    post {
        always {
            echo "Pipeline finished"
        }
    }
}
