pipeline {
  agent any
  triggers {
    pollSCM '* * * * *'
    cron '@midnight'
  }
  options { 
    disableConcurrentBuilds() 
    checkoutToSubdirectory('exec')
  }

  environment {
      INMANTA_MODULE_REPO='https://github.com/inmanta/'
      INMANTA_TEST_ENV="${env.WORKSPACE}/env"
  } 

  stages {
    stage("test"){
      steps{
        script{
          sh 'rm -rf $INMANTA_TEST_ENV; python3 -m venv $INMANTA_TEST_ENV; $INMANTA_TEST_ENV/bin/python3 -m pip install -U  git+https://github.com/inmanta/inmanta.git git+https://github.com/inmanta/pytest-inmanta.git'
          dir('exec'){
            sh '$INMANTA_TEST_ENV/bin/python3 -m pytest --junitxml=junit.xml -vvv tests'
          }
        }
      }
    }
  }
  post {
    always{
      always {
            junit 'exec/junit.xml'
        }
    }
  }

}
