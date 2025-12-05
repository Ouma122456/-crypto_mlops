pipeline {
    agent any

    environment {
        PYTHON = "python"
        VENV = "venv"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                bat '''
                    echo --- Python version ---
                    python --version

                    echo --- Create virtual environment ---
                    python -m venv %VENV%

                    echo --- Activate venv & install dependencies ---
                    call %VENV%\\Scripts\\activate
                    pip install --upgrade pip

                    if exist requirements.txt (
                        pip install -r requirements.txt
                    ) else (
                        echo requirements.txt not found
                    )
                '''
            }
        }

        stage('Run Training Pipeline') {
            steps {
                bat '''
                    echo --- Running Training ---
                    call %VENV%\\Scripts\\activate

                    if exist train.py (
                        python train.py
                    ) else (
                        echo train.py not found
                    )
                '''
            }
        }

        stage('Run Evaluation') {
            steps {
                bat '''
                    echo --- Running Evaluation ---
                    call %VENV%\\Scripts\\activate

                    if exist evaluate.py (
                        python evaluate.py
                    ) else (
                        echo No evaluation script found
                    )
                '''
            }
        }

        stage('DVC Sync') {
            steps {
                bat '''
                    echo --- DVC Sync ---
                    call %VENV%\\Scripts\\activate

                    dvc pull  || echo No remote data
                    dvc push  || echo Nothing to push
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished successfully 🚀"
        }
    }
}
