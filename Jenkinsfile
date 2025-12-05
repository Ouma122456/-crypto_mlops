pipeline {
    agent any

    environment {
        DOCKER_IMAGE_API = "crypto-api:latest"
        DOCKER_IMAGE_FRONT = "crypto-mlops-front:latest"
    }

    stages {
        stage('Checkout du code') {
            steps {
                git url: 'https://dagshub.com/Ouma122456/crypto_mlops.git',
                branch: 'main',
                credentialsId: 'dagshub-credentials'

            }
        }

        stage('Build des images Docker') {
            steps {
                sh 'docker-compose build'
            }
        }

        //stage('Tests') {
            //steps {
                //sh 'pytest tests/'  // remplace par ton script de validation des modèles
            //}
        //}

        stage('Déploiement Kubernetes') {
            steps {
                sh 'kubectl apply -f crypto-api-deployment.yaml'
                sh 'kubectl apply -f crypto-dashboard-deployment.yaml'
                sh 'kubectl apply -f prometheus-deployment.yaml'
                sh 'kubectl apply -f grafana-deployment.yaml'

        }

        stage('Vérification') {
            steps {
                sh 'kubectl get pods'  // vérifie que les pods sont en Running
            }
        }
    }

    post {
        success {
            echo 'Pipeline terminé avec succès !'
        }
        failure {
            echo 'Échec du pipeline.'
        }
    }
}
