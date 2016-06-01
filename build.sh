#!/bin/bash
source /etc/profile

if [[ -s ~/.bash_profile ]] ; then
  source ~/.bash_profile
fi

ANSI_RED="\033[31;1m"
ANSI_GREEN="\033[32;1m"
ANSI_RESET="\033[0m"
ANSI_CLEAR="\033[0K"

TRAVIS_TEST_RESULT=
TRAVIS_CMD=

function travis_cmd() {
  local assert output display retry timing cmd result

  cmd=$1
  TRAVIS_CMD=$cmd
  shift

  while true; do
    case "$1" in
      --assert)  assert=true; shift ;;
      --echo)    output=true; shift ;;
      --display) display=$2;  shift 2;;
      --retry)   retry=true;  shift ;;
      --timing)  timing=true; shift ;;
      *) break ;;
    esac
  done

  if [[ -n "$timing" ]]; then
    travis_time_start
  fi

  if [[ -n "$output" ]]; then
    echo "\$ ${display:-$cmd}"
  fi

  if [[ -n "$retry" ]]; then
    travis_retry eval "$cmd"
  else
    eval "$cmd"
  fi
  result=$?

  if [[ -n "$timing" ]]; then
    travis_time_finish
  fi

  if [[ -n "$assert" ]]; then
    travis_assert $result
  fi

  return $result
}

travis_time_start() {
  travis_timer_id=$(printf %08x $(( RANDOM * RANDOM )))
  travis_start_time=$(travis_nanoseconds)
  echo -en "travis_time:start:$travis_timer_id\r${ANSI_CLEAR}"
}

travis_time_finish() {
  local result=$?
  travis_end_time=$(travis_nanoseconds)
  local duration=$(($travis_end_time-$travis_start_time))
  echo -en "\ntravis_time:end:$travis_timer_id:start=$travis_start_time,finish=$travis_end_time,duration=$duration\r${ANSI_CLEAR}"
  return $result
}

function travis_nanoseconds() {
  local cmd="date"
  local format="+%s%N"
  local os=$(uname)

  if hash gdate > /dev/null 2>&1; then
    cmd="gdate" # use gdate if available
  elif [[ "$os" = Darwin ]]; then
    format="+%s000000000" # fallback to second precision on darwin (does not support %N)
  fi

  $cmd -u $format
}

travis_assert() {
  local result=${1:-$?}
  if [ $result -ne 0 ]; then
    echo -e "\n${ANSI_RED}The command \"$TRAVIS_CMD\" failed and exited with $result during $TRAVIS_STAGE.${ANSI_RESET}\n\nYour build has been stopped."
    travis_terminate 2
  fi
}

travis_result() {
  local result=$1
  export TRAVIS_TEST_RESULT=$(( ${TRAVIS_TEST_RESULT:-0} | $(($result != 0)) ))

  if [ $result -eq 0 ]; then
    echo -e "\n${ANSI_GREEN}The command \"$TRAVIS_CMD\" exited with $result.${ANSI_RESET}"
  else
    echo -e "\n${ANSI_RED}The command \"$TRAVIS_CMD\" exited with $result.${ANSI_RESET}"
  fi
}

travis_terminate() {
  pkill -9 -P $$ &> /dev/null || true
  exit $1
}

travis_wait() {
  local timeout=$1

  if [[ $timeout =~ ^[0-9]+$ ]]; then
    # looks like an integer, so we assume it's a timeout
    shift
  else
    # default value
    timeout=20
  fi

  local cmd="$@"
  local log_file=travis_wait_$$.log

  $cmd &>$log_file &
  local cmd_pid=$!

  travis_jigger $! $timeout $cmd &
  local jigger_pid=$!
  local result

  {
    wait $cmd_pid 2>/dev/null
    result=$?
    ps -p$jigger_pid &>/dev/null && kill $jigger_pid
  }

  if [ $result -eq 0 ]; then
    echo -e "\n${ANSI_GREEN}The command $cmd exited with $result.${ANSI_RESET}"
  else
    echo -e "\n${ANSI_RED}The command $cmd exited with $result.${ANSI_RESET}"
  fi

  echo -e "\n${ANSI_GREEN}Log:${ANSI_RESET}\n"
  cat $log_file

  return $result
}

travis_jigger() {
  # helper method for travis_wait()
  local cmd_pid=$1
  shift
  local timeout=$1 # in minutes
  shift
  local count=0

  # clear the line
  echo -e "\n"

  while [ $count -lt $timeout ]; do
    count=$(($count + 1))
    echo -ne "Still running ($count of $timeout): $@\r"
    sleep 60
  done

  echo -e "\n${ANSI_RED}Timeout (${timeout} minutes) reached. Terminating \"$@\"${ANSI_RESET}\n"
  kill -9 $cmd_pid
}

travis_retry() {
  local result=0
  local count=1
  while [ $count -le 3 ]; do
    [ $result -ne 0 ] && {
      echo -e "\n${ANSI_RED}The command \"$@\" failed. Retrying, $count of 3.${ANSI_RESET}\n" >&2
    }
    "$@"
    result=$?
    [ $result -eq 0 ] && break
    count=$(($count + 1))
    sleep 1
  done

  [ $count -gt 3 ] && {
    echo -e "\n${ANSI_RED}The command \"$@\" failed 3 times.${ANSI_RESET}\n" >&2
  }

  return $result
}

travis_fold() {
  local action=$1
  local name=$2
  echo -en "travis_fold:${action}:${name}\r${ANSI_CLEAR}"
}

decrypt() {
  echo $1 | base64 -d | openssl rsautl -decrypt -inkey ~/.ssh/id_rsa.repo
}

# XXX Forcefully removing rabbitmq source until next build env update
# See http://www.traviscistatus.com/incidents/6xtkpm1zglg3
if [[ -f /etc/apt/sources.list.d/rabbitmq-source.list ]] ; then
  sudo rm -f /etc/apt/sources.list.d/rabbitmq-source.list
fi

mkdir -p $HOME/build
cd       $HOME/build


travis_fold start system_info
  echo -e "\033[33;1mBuild system information\033[0m"
  echo -e "Build language: python"
  echo -e "Build dist: trusty"
  if [[ -f /usr/share/travis/system_info ]]; then
    cat /usr/share/travis/system_info
  fi
travis_fold end system_info

echo

travis_fold start fix.CVE-2015-7547
  if [[ `hostname` == testing-gce-* ]]; then
    sudo sed -i 's%us-central1.gce.archive.ubuntu.com/ubuntu%us.archive.ubuntu.com/ubuntu%' /etc/apt/sources.list
  fi
  travis_cmd export\ DEBIAN_FRONTEND\=noninteractive --echo
  if [ ! $(uname|grep Darwin) ]; then
    sudo -E apt-get -yq update 2>&1 >> ~/apt-get-update.log
    sudo -E apt-get -yq --no-install-suggests --no-install-recommends --force-yes install libc6
  fi
travis_fold end fix.CVE-2015-7547

echo "options rotate
options timeout:1

nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 208.67.222.222
nameserver 208.67.220.220
" | sudo tee /etc/resolv.conf &> /dev/null
sudo sed -e 's/^\(127\.0\.0\.1.*\)$/\1 '`hostname`'/' -i'.bak' /etc/hosts
test -f /etc/mavenrc && sudo sed -e 's/M2_HOME=\(.\+\)$/M2_HOME=${M2_HOME:-\1}/' -i'.bak' /etc/mavenrc
if [ $(command -v sw_vers) ]; then
  echo "Fix WWDRCA Certificate"
  sudo security delete-certificate -Z 0950B6CD3D2F37EA246A1AAA20DFAADBD6FE1F75 /Library/Keychains/System.keychain
  wget -q https://developer.apple.com/certificationauthority/AppleWWDRCA.cer
  sudo security add-certificates -k /Library/Keychains/System.keychain AppleWWDRCA.cer
fi

sudo sed -e 's/^127\.0\.0\.1\(.*\) localhost \(.*\)$/127.0.0.1 localhost \1 \2/' -i'.bak' /etc/hosts 2>/dev/null
# apply :home_paths
for path_entry in $HOME/.local/bin $HOME/bin ; do
  if [[ ${PATH%%:*} != $path_entry ]] ; then
    export PATH="$path_entry:$PATH"
  fi
done

mkdir -p $HOME/.ssh
chmod 0700 $HOME/.ssh
touch $HOME/.ssh/config
echo -e "Host *
  UseRoaming no
" | cat - $HOME/.ssh/config > $HOME/.ssh/config.tmp && mv $HOME/.ssh/config.tmp $HOME/.ssh/config
function travis_debug() {
echo -e "\033[31;1mThe debug environment is not available. Please contact support.\033[0m"
false
}

if [[ ! -f ~/virtualenv/python2.7/bin/activate ]]; then
  echo -e "\033[33;1m2.7 is not installed; attempting download\033[0m"
  if [[ $(uname) = 'Linux' ]]; then
    travis_host_os=$(lsb_release -is | tr 'A-Z' 'a-z')
    travis_rel_version=$(lsb_release -rs)
  elif [[ $(uname) = 'Darwin' ]]; then
    travis_host_os=osx
    travis_rel=$(sw_vers -productVersion)
    travis_rel_version=${travis_rel%*.*}
  fi
  archive_url=https://s3.amazonaws.com/travis-python-archives/binaries/${travis_host_os}/${travis_rel_version}/$(uname -m)/python-2.7.tar.bz2
  travis_cmd curl\ -s\ -o\ python-2.7.tar.bz2\ \$\{archive_url\} --assert
  travis_cmd sudo\ tar\ xjf\ python-2.7.tar.bz2\ --directory\ / --assert
  rm python-2.7.tar.bz2
  sed -e 's|export PATH=\(.*\)$|export PATH=/opt/python/2.7/bin:\1|' /etc/profile.d/pyenv.sh > /tmp/pyenv.sh
  cat /tmp/pyenv.sh | sudo tee /etc/profile.d/pyenv.sh > /dev/null
fi

export GIT_ASKPASS=echo

travis_fold start git.checkout
  if [[ ! -d neurodata/ndstore/.git ]]; then
    travis_cmd git\ clone\ --depth\=50\ --branch\=\'microns\'\ https://github.com/neurodata/ndstore.git\ neurodata/ndstore --assert --echo --retry --timing
  else
    travis_cmd git\ -C\ neurodata/ndstore\ fetch\ origin --assert --echo --retry --timing
    travis_cmd git\ -C\ neurodata/ndstore\ reset\ --hard --assert --echo
  fi
  travis_cmd cd\ neurodata/ndstore --echo
  travis_cmd git\ checkout\ -qf\  --assert --echo
travis_fold end git.checkout

if [[ -f .gitmodules ]]; then
  travis_fold start git.submodule
    echo Host\ github.com'
    '\	StrictHostKeyChecking\ no'
    ' >> ~/.ssh/config
    travis_cmd git\ submodule\ update\ --init\ --recursive --assert --echo --retry --timing
  travis_fold end git.submodule
fi

rm -f ~/.ssh/source_rsa

travis_fold start services
  travis_cmd sudo\ service\ mysql\ start --echo --timing
  travis_cmd sudo\ service\ memcached\ start --echo --timing
  travis_cmd sudo\ service\ rabbitmq-server\ start --echo --timing
  travis_cmd sudo\ service\ supervisor\ start --echo --timing
  travis_cmd sudo\ service\ nginx\ start --echo --timing
  travis_cmd sudo\ service\ redis-server\ start --echo --timing
  sleep 3
travis_fold end services

export PS4=+
export TRAVIS=true
export CI=true
export CONTINUOUS_INTEGRATION=true
export HAS_JOSH_K_SEAL_OF_APPROVAL=true
export TRAVIS_EVENT_TYPE=''
export TRAVIS_PULL_REQUEST=false
export TRAVIS_SECURE_ENV_VARS=false
export TRAVIS_BUILD_ID=''
export TRAVIS_BUILD_NUMBER=''
export TRAVIS_BUILD_DIR=$HOME/build/neurodata/ndstore
export TRAVIS_JOB_ID=''
export TRAVIS_JOB_NUMBER=''
export TRAVIS_BRANCH=''
export TRAVIS_COMMIT=''
export TRAVIS_COMMIT_RANGE=''
export TRAVIS_REPO_SLUG=neurodata/ndstore
export TRAVIS_OS_NAME=''
export TRAVIS_LANGUAGE=python
export TRAVIS_TAG=''
export TRAVIS_PYTHON_VERSION=2.7
#travis_cmd source\ \~/virtualenv/python2.7/bin/activate --assert --echo --timing

travis_fold start cache.1
  echo -e "Setting up build cache"
  rvm use $(rvm current >&/dev/null) >&/dev/null
  travis_cmd export\ CASHER_DIR\=\$HOME/.casher --echo
  mkdir -p $CASHER_DIR/bin
  travis_cmd curl\ https://raw.githubusercontent.com/travis-ci/casher/production/bin/casher\ \ -L\ -o\ \$CASHER_DIR/bin/casher\ -s\ --fail --assert --echo --display Installing\ caching\ utilities --retry --timing
  [ $? -ne 0 ] && echo 'Failed to fetch casher from GitHub, disabling cache.' && echo > $CASHER_DIR/bin/casher
  if [[ -f $CASHER_DIR/bin/casher ]]; then
    chmod +x $CASHER_DIR/bin/casher
  fi
  if [[ -f $CASHER_DIR/bin/casher ]]; then
    travis_cmd type\ rvm\ \&\>/dev/null\ \|\|\ source\ \~/.rvm/scripts/rvm --timing
    travis_cmd rvm\ 1.9.3\ --fuzzy\ do\ \$CASHER_DIR/bin/casher\ fetch\ https://cache_bucket.s3.amazonaws.com/1234567890//cache-trusty-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855--python-2.7.tgz\\\?X-Amz-Algorithm\\\=AWS4-HMAC-SHA256\\\&X-Amz-Credential\\\=abcdef0123456789\\\%2F20160601\\\%2Fus-east-1\\\%2Fs3\\\%2Faws4_request\\\&X-Amz-Date\\\=20160601T163105Z\\\&X-Amz-Expires\\\=60\\\&X-Amz-Signature\\\=429039597ba84d66e25f5e0fa5fc38eba2f703cb352d4540f545c040e212df24\\\&X-Amz-SignedHeaders\\\=host\ https://cache_bucket.s3.amazonaws.com/1234567890//cache--python-2.7.tgz\\\?X-Amz-Algorithm\\\=AWS4-HMAC-SHA256\\\&X-Amz-Credential\\\=abcdef0123456789\\\%2F20160601\\\%2Fus-east-1\\\%2Fs3\\\%2Faws4_request\\\&X-Amz-Date\\\=20160601T163105Z\\\&X-Amz-Expires\\\=60\\\&X-Amz-Signature\\\=981fcbafadd622fc171970f91f1dba3be0192436cb64351aaa59b955aca7c8dd\\\&X-Amz-SignedHeaders\\\=host\ https://cache_bucket.s3.amazonaws.com/1234567890/master/cache-trusty-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855--python-2.7.tgz\\\?X-Amz-Algorithm\\\=AWS4-HMAC-SHA256\\\&X-Amz-Credential\\\=abcdef0123456789\\\%2F20160601\\\%2Fus-east-1\\\%2Fs3\\\%2Faws4_request\\\&X-Amz-Date\\\=20160601T163105Z\\\&X-Amz-Expires\\\=60\\\&X-Amz-Signature\\\=6cb2ff17806416aa19628597b596c3efa6275184a1f477e79538cf1ceca71a2c\\\&X-Amz-SignedHeaders\\\=host\ https://cache_bucket.s3.amazonaws.com/1234567890/master/cache--python-2.7.tgz\\\?X-Amz-Algorithm\\\=AWS4-HMAC-SHA256\\\&X-Amz-Credential\\\=abcdef0123456789\\\%2F20160601\\\%2Fus-east-1\\\%2Fs3\\\%2Faws4_request\\\&X-Amz-Date\\\=20160601T163105Z\\\&X-Amz-Expires\\\=60\\\&X-Amz-Signature\\\=4ea4112aaba1e6c8c2db6900f37e1a8e93a6fb41936f43c97272f71164e39324\\\&X-Amz-SignedHeaders\\\=host --timing
  fi
travis_fold end cache.1

travis_fold start cache.pip
  echo
  if [[ -f $CASHER_DIR/bin/casher ]]; then
    travis_cmd type\ rvm\ \&\>/dev/null\ \|\|\ source\ \~/.rvm/scripts/rvm --timing
    travis_cmd rvm\ 1.9.3\ --fuzzy\ do\ \$CASHER_DIR/bin/casher\ add\ \$HOME/.cache/pip --timing
  fi
travis_fold end cache.pip

travis_cmd python\ --version --echo
travis_cmd pip\ --version --echo
export PIP_DISABLE_PIP_VERSION_CHECK=1

travis_fold start before_install.1
  travis_cmd sudo\ mkdir\ /var/log/neurodata --assert --echo --timing
travis_fold end before_install.1

travis_fold start before_install.2
  travis_cmd sudo\ touch\ /var/log/neurodata/nd.log --assert --echo --timing
travis_fold end before_install.2

travis_fold start before_install.3
  travis_cmd sudo\ chown\ -R\ www-data:www-data\ /var/log/neurodata --assert --echo --timing
travis_fold end before_install.3

travis_fold start before_install.4
  travis_cmd sudo\ chmod\ -R\ 777\ /var/log/neurodata/ --assert --echo --timing
travis_fold end before_install.4

travis_fold start install.1
  travis_cmd sudo\ apt-get\ -y\ install\ uwsgi\ uwsgi-plugin-python --assert --echo --timing
travis_fold end install.1

travis_fold start install.2
  travis_cmd sudo pip\ install\ cython\ numpy --assert --echo --timing
travis_fold end install.2

travis_fold start install.3
  travis_cmd sudo pip\ install\ -r\ ./setup/requirements.txt --assert --echo --timing
travis_fold end install.3

travis_fold start install.4
  travis_cmd make\ -f\ /home/ubuntu/build/neurodata/ndstore/ndlib/c_version/makefile_LINUX\ -C\ ./ndlib/c_version/ --assert --echo --timing
travis_fold end install.4

travis_fold start install.5
  travis_cmd mysql\ -u\ root\ -i\ -e\ \"create\ user\ \'neurodata\'@\'localhost\'\ identified\ by\ \'neur0data\'\;\"\ \&\&\ mysql\ -u\ root\ -i\ -e\ \"grant\ all\ privileges\ on\ \*.\*\ to\ \'neurodata\'@\'localhost\'\ with\ grant\ option\;\"\ \&\&\ mysql\ -u\ neurodata\ -pneur0data\ -i\ -e\ \"CREATE\ DATABASE\ neurodjango\;\" --assert --echo --timing
travis_fold end install.5

travis_fold start install.6
  travis_cmd cp\ ./django/ND/settings.py.example\ ./django/ND/settings.py --assert --echo --timing
travis_fold end install.6

travis_fold start install.7
  travis_cmd ln\ -s\ /home/ubuntu/build/neurodata/ndstore/setup/docker_config/django/docker_settings_secret.py\ /home/ubuntu/build/neurodata/ndstore/django/ND/settings_secret.py --assert --echo --timing
travis_fold end install.7

travis_fold start install.8
  travis_cmd python\ ./django/manage.py\ migrate --assert --echo --timing
travis_fold end install.8

travis_fold start install.9
  travis_cmd echo\ \"from\ django.contrib.auth.models\ import\ User\;\ User.objects.create_superuser\(\'neurodata\',\ \'abc@xyz.com\',\ \'neur0data\'\)\"\ \|\ python\ ./django/manage.py\ shell --assert --echo --timing
travis_fold end install.9

travis_fold start install.10
  travis_cmd python\ ./django/manage.py\ collectstatic\ --noinput --assert --echo --timing
travis_fold end install.10

travis_fold start install.11
  travis_cmd sudo\ rm\ /etc/nginx/sites-enabled/default --assert --echo --timing
travis_fold end install.11

travis_fold start install.12
  travis_cmd sudo\ rm\ /etc/nginx/sites-available/default --assert --echo --timing
travis_fold end install.12

travis_fold start install.13
  travis_cmd sudo\ cp\ ./setup/docker_config/nginx/ndstore.conf\ /etc/nginx/sites-available/default --assert --echo --timing
travis_fold end install.13

travis_fold start install.14
  travis_cmd sudo\ ln\ -s\ /etc/nginx/sites-available/default\ /etc/nginx/sites-enabled/default --assert --echo --timing
travis_fold end install.14

travis_fold start install.15
  travis_cmd sudo\ chown\ -R\ www-data:www-data\ /tmp/ --assert --echo --timing
travis_fold end install.15

travis_fold start install.16
  travis_cmd sudo\ cp\ ./setup/docker_config/uwsgi/ndstore.ini\ /etc/uwsgi/apps-available/ndstore.ini --assert --echo --timing
travis_fold end install.16

travis_fold start install.17
  travis_cmd sudo\ cp\ ./setup/docker_config/uwsgi/ndstore.ini\ /etc/uwsgi/apps-enabled/ndstore.ini --assert --echo --timing
travis_fold end install.17

travis_fold start install.18
  travis_cmd sudo\ ln\ -s\ ./setup/docker_config/celery/propagate.conf\ /etc/supervisor/conf.d/propagate.conf --assert --echo --timing
travis_fold end install.18

travis_fold start install.19
  travis_cmd sudo\ ln\ -s\ ./setup/docker_config/celery/ingest.conf\ /etc/supervisor/conf.d/ingest.conf --assert --echo --timing
travis_fold end install.19

travis_fold start install.20
  travis_cmd sudo\ service\ nginx\ restart --assert --echo --timing
travis_fold end install.20

travis_fold start install.21
  travis_cmd sudo\ service\ uwsgi\ restart --assert --echo --timing
travis_fold end install.21

travis_fold start install.22
  travis_cmd sudo\ service\ supervisor\ restart --assert --echo --timing
travis_fold end install.22

travis_fold start install.23
  travis_cmd sudo\ service\ rabbitmq-server\ restart --assert --echo --timing
travis_fold end install.23

travis_fold start install.24
  travis_cmd sudo\ service\ memcached\ restart --assert --echo --timing
travis_fold end install.24

travis_fold start install.25
  travis_cmd '' --assert --echo --timing
travis_fold end install.25

travis_cmd wget\ localhost --echo --timing
travis_result $?
travis_cmd wget\ localhost/nd/accounts/login --echo --timing
travis_result $?
travis_cmd ls\ -la\ /tmp/ --echo --timing
travis_result $?
travis_cmd cd\ ./test/ --echo --timing
travis_result $?
travis_cmd py.test\ test_info.py --echo --timing
travis_result $?
travis_cmd cat\ /var/log/uwsgi/app/\*.log --echo --timing
travis_result $?
travis_cmd cat\ /var/log/neurodata/ndstore.log --echo --timing
travis_result $?

travis_fold start cache.2
  echo -e "store build cache"
  if [[ -f $CASHER_DIR/bin/casher ]]; then
    travis_cmd type\ rvm\ \&\>/dev/null\ \|\|\ source\ \~/.rvm/scripts/rvm --timing
    travis_cmd rvm\ 1.9.3\ --fuzzy\ do\ \$CASHER_DIR/bin/casher\ push\ https://cache_bucket.s3.amazonaws.com/1234567890//cache-trusty-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855--python-2.7.tgz\\\?X-Amz-Algorithm\\\=AWS4-HMAC-SHA256\\\&X-Amz-Credential\\\=abcdef0123456789\\\%2F20160601\\\%2Fus-east-1\\\%2Fs3\\\%2Faws4_request\\\&X-Amz-Date\\\=20160601T163105Z\\\&X-Amz-Expires\\\=60\\\&X-Amz-Signature\\\=30cfc5e47a92539cb439c7a6adefd5ae0e7782b2a5c015ee1498e158c086edb6\\\&X-Amz-SignedHeaders\\\=host --timing
  fi
travis_fold end cache.2

echo -e "\nDone. Your build exited with $TRAVIS_TEST_RESULT."

travis_terminate $TRAVIS_TEST_RESULT
