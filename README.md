bluelinks
=========

This is the source code running [bluelinks.co](https://bluelinks.co). It is 
a Python webapplication written with Flask. Setup should be roughly as follows:

``` bash
mkvirtualenv bluelinks
git clone https://github.com/icook/bluelinks.git
cd bluelinks
pip install -r requirements.txt
python manage.py init_db
python manage.py runserver
```
