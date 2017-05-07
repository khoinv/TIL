### ref:
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-14-04

### install git
```bash
apt-get install git
```

### install python, postgresql, nginx
```bash
apt-get update
apt-get -y upgrade
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib nginx
```
### create new user for web user
- create new user for web user (*first time only*)
```bash
adduser django
gpasswd -a django sudo
```
- Loggin with created user(django)
```bash
ssh django@ip
```

### Create new virtualenv
- install virtualenv tool(*first time only*)
```bash
virtualenv my-env
```

```bash
virtualenv my-env
```

- Active created Virtualenv
```bash
source ~/my-env/bin/activate
```

### Clone project
```bash
git clone git_repo_url
```

### Install project pakage
```bash
cd my_project
pip install -r requirements.txt
```

### Migrate the database:
```bash
python manage.py migrate
```

### Collect the static files:
```bash
python manage.py collectstatic
```

### Test if everything is okay:
```bash
python manage.py runserver 0.0.0.0:8000
```

*this is just a TEST. We won’t be using the run server to run our application. We will be using a proper application server to securely serve our application
Hit Control-C to quit the development server and let's keep moving forward*

### Install Gunicorn and PostgreSQL adaptor
```bash
pip install django gunicorn psycopg2
```

#### Testing gunicorn that is ok?

```bash
cd ~/my_project
gunicorn --bind 0.0.0.0:8000 tutorial.wsgi:application
```
**Hit Control-C to stop it**
- install super command
```bash
sudo apt-get install super
```

### Create a Gunicorn Upstart file

```bash
sudo vi /etc/init/gunicorn.conf
```
**content as the below**
```bash
description "Gunicorn application server handling my_project"

start on runlevel [2345]
stop on runlevel [!2345]

respawn
setuid django
setgid django
chdir /home/django/my_project

exec /home/django/my-env/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 tutorial.wsgi:application
```
**Check syntax**
```bash
init-checkconf  /etc/init/gunicorn.conf
```
**show log**
```bash
cat /var/log/upstart/gunicorn.log
```

- Start| Stop | Restart  service
```bash
sudo service gunicorn start
sudo service gunicorn stop
sudo service gunicorn restart
```
**show log**
```bash
cat /var/log/upstart/gunicorn.log
```


### updating code
```bash
git pull origin master
sudo service  gunicorn restart
```
