### Skeleton

A skeleton Flask project. Fairly opinionated in how I setup projects. Uses:

* Gunicorn as the WSGI server
* Flask-Assets to compile SCSS
* A YAML config file
* Flask-Security to handle login/registration/forgot password etc
* Bootstrap + FontAwesome for styling

### Setup

``` bash
$ sudo apt-get install ruby-sass
$ mkvirtualenv skeleton --python /usr/bin/python3.4
$ pip install -r requirements.txt
$ python manage.py runserver
```
