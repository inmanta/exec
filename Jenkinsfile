pipeline {
  agent any
  triggers{
    pollSCM '* * * * *'
    cron(BRANCH_NAME == "master" ? "H H(2-5) * * *": "")
  }
  options { disableConcurrentBuilds() }
  parameters {
    string(name: 'pypi_index', defaultValue: 'https://artifacts.internal.inmanta.com/inmanta/stable', description: 'Changes the index used to install pytest-inmanta (And only pytest-inmanta)')
  }
  stages {
    stage("setup"){
      steps{
        script{
          sh'''
          python3 -m venv ${WORKSPACE}/env
          ${WORKSPACE}/env/bin/pip install -r requirements.dev.txt
          # make sure pytest inmanta is the required version
          ${WORKSPACE}/env/bin/pip install -U pytest-inmanta -i pypi_index
          '''
        }
      }
    }
    stage("code linting"){
      steps{
        script{
          sh'''
          ${WORKSPACE}/env/bin/flake8 plugins tests
          '''
        }
      }
    }
    stage("tests"){
      steps{
        script{
          sh'''
          ${WORKSPACE}/env/bin/pytest tests -v --junitxml=junit.xml
          '''
          junit 'junit.xml'
        }
      }
    }
  }
  post{
    always{
      script{
        sh'''
        ${WORKSPACE}/env/bin/pip uninstall -y pytest-inmanta
        '''
      }
    }
  }
}
