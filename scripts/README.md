### Scripts to downsample the databases and build hierarchy

* All the outdated scripts are now moved into deprecated. 
* imgstack16 works with the current schema and is an example script. 
* The propagate module has now been replace by the propagate web-service and the code resides in webservices/ndwsingest.py

#### Using the aws_interface script

The aws_interface script will act as an interface to manage data on S3
* Upload existing projects in *ndstore* to S3 
  * Upload a project
  * Upload a channel for a given project
  * Upload a resolution for a given channel
```console
python aws_interface.py kasthuri11 --action upload
python aws_interface.py kasthuri11 --channel image --action upload
python aws_interface.py kasthuri11 --channel image --res 5 --action upload
```
* Delete an existing project in S3
  * Delete a resolution for a given channel
  * Delete a channel for a given project
  * Delete a project
```console
python aws_interface.py kasthuri11 --action delete-project
python aws_interface.py kasthuri11 --channel image --action delete-channel
python aws_interface.py kasthuri11 --channel image --res 4 --action delete-res
```

#### Setup for aws_interface script
* apt-get install git, python-dev, python-pip, libtiff-dev, libmysqlclient-dev
* Install pip packages: numpy, blosc, django, requests, Pillow, boto3, celery==3.1.23, djangorestframework, django-registration, django-celery, django-cors-headers, django-sslserver, django-cors-middleware,  mysql-python, botocore, redis, jsonschema 
* Git clone the ndstore repo. Checkout branch kdevel. init the submodules and update them.
* Copy the django/ND/settings.py.example as django/ND/setting.py and settings_secret.py.example as settings_secret.py
* Copy the ndingest/settings/settings.ini.example into ndingest/settings/settings.ini. Enter the correct credentials here and set the DEV_MODE accordingly.
* Create a log in /var/log/neurodata/ndstore.log. chmod 777 ndstore.log
* Make ndlib.so in ndlib/c_version
