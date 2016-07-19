### Configuration Information for NeuroData

### Ubuntu Installation

##### Git Submodules

* Fresh Clone
```sh
git clone --recursive git@github.com:neurodata/ndstore.git
```
* Existing Repository
```sh
git submodule update --init --recursive
```

##### Ubuntu Packages

```sh
sudo apt-get install uwsgi-plugin-python
```

##### Python dependencies 

```sh
pip install numpy scipy django django-registration-redux django-celery mysql-python pytest pillow pylibmc posix_ipc networkx nibabel lxml boto3 requests h5py blosc redis
```

##### Configuration files

You need to create the following files from the example files in the same directories.
  * ndstore/django/ND/settings.py
  * ndstore/django/ND/settings_secret.py

##### MySQL 

List of commands needed to configure the database for mysql

  * Create brain user as MySQL root
    
    ```sql
    create user 'brain'@'localhost' identified by 'password_here';
    grant all privileges on *.* to 'brain'@'localhost' with grant option;

    create user 'brain'@'%' identified by 'password_here';
    grant all privileges on *.* to 'brain'@'%' with grant option;
    ```

  * Create the database neurodjango
    
    ```sql
    create database neurodjango;
    ```

##### Nginx

  * default
    ND configuration for /etc/nginx/sites-enabled/default
  
  * ocp.ini
    uWSGI configuration file in /etc/uwsgi/apps-enabled/

##### Celery
  
  * ingest.conf
    ND configuration for /etc/supervisor/
  
  * propagate.conf 
    ND configuration for /etc/supervisor

  * stats.conf
    ND configuration for /etc/supervisor


### MACOS Installation

##### clone the repository and make a virtual env if you want
  ```sh
  git clone git@github.com:neurodata/ndstore.git
  mkvirtualenv ocp
  ```

##### install and configure mysql & memcache. Follow the instructions as ubuntu
  ```sh
  cd ~/ndstore/setup/mysql
  ```

##### Install python packages using pip
  ```sh
  pip install numpy scipy h5py django django-registration-redux django-celery mysql-python pytest pillow posix_ipc
  pip install --force-reinstall --upgrade --no-cache-dir --compile blosc  
  pip install pylibmc --install-option="--with-libmemcached=/usr/local/Cellar/libmemcached/1.0.18_1/"

  ```
  * Note: MACOSX note: had to follow weird library linking instructions on http://www.strangedata.ninja/2014/08/07/how-to-install-mysql-server-mac-and-python-mysqldb-library/ to get "import MySQLdb" to work

##### Django Settings
  
  * Migrate the databases, collect static files,
    ```sh
    cd ~/ndstore/django
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py collectstatic
    ```

  * configure settings
    ```sh
    cd ~/ndstore/django/OCP
    cp settings.py.example settings.py
    cp settings_secret.py.example settings_secret.py
    ```

  * Change the following fields in settings.py
    * STATIC_ROOT
    * STATICFILES_DIRS
    * TEMPLATE_DIRS
    * FORCE_SCRIPT_NAME *for the dev server set to ""*

  * edited the fields in settings_secret.py
    * USER
    * PASSWORD
    * SECRET_KEY
    * BACKUP_PATH

##### make the logfile directory and make it readable
  ```sh
  sudo mkdir /var/log/ocp
  sudo chown XXX:YYY /var/log/ocp
  ```

##### Build ocplib
  ```sh
  cd ~/ndstore/ocplib
  make -f makefile_MAC
  ```

##### Dev Server and tests
  * In one window, start the dev server
    ```sh
    cd ~/ndstore/django
    python manage.py runserver
    ```

  * in another window
    ```sh
    cd ~/ndstore/test
    py.test
    ```

##### More advanced stuff

  * onto nginx
    ```sh
    brew install nginx
    ```

  * add clause to nginx for ocp and upstream server (see setup/nginx/default)
  * edit uswgi file ocp.ini
  * change all paths for local system
  * configure uswgi at ~/ndstore/setup/ocp.ini
  * run uwsgi in foreground
    ```sh
    uwsgi ocp.ini
    ```

  * Create paths for sockets
    ```sh
    mkdir /usr/local/var/run/uwsgi
    mkdir /usr/local/var/run/uwsgi/app
    mkdir /usr/local/var/run/uwsgi/app/ocp
    ```

  * Create path for logs
    ```sh
    mkdir /usr/local/var/log/uwsgi/
    ```

  * run nginx (as user)
    ```sh
    nginx
    ```

  * stop nginx
    ```sh
    nginx -s stop
    ```

  * run uwsgi as user
    ```sh
    workon XXX
    uwsgi ocp.ini
    ```

  * right now nothing is daemonized
