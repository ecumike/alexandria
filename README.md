# Alexandria
Surveys metrics dashboard and user research library. 

**Research library**: Host and catalog all your research findings, along with searchable and filterable meta data.

**Metrics dashboard**:  Create projects and campaigns and import survey responses and view monthly or quarterly quarterly historical NPS scores and all responses.


## Included/installed Features:
- "Switch user" admin feature
- Basic flexible page template
- Custom error pages
- Custom error handling, and email and slack room notifications
- Debugging toolbar
- Django extensions
- Site-wide banner notifications
- Template helpers for preset design components; buttons, icons, header, tabs, etc
- UI framework using Tachyons, select2, tooltip and overlays


## Install Requirements

Python 3.9 ish +

Postgres 14 ish +

## Install

Setup a virtual environment:

```
python3 -m venv /path/to/env/<name>
```

Activate the environment:

```
source /path/to/env/<name>/bin/activate
```

Clone the repo:

```
git clone git@github.com:ecumike/alexandria.git
```

CD to the repo, wherever you just cloned it, and install the dependencies:

```
pip install -r requirements.txt
```

Setup some localhost variables:
They can be set as environment variables, or you can add a `local_settings.py` file alongside the Django default `settings.py` file. 
If you set them as env variables you will only have to do this once and each of our Django app will use those same settings.

You only need to replace the two `___`s with your local Postgres DB user ID and PW. 
`SCRIPT_NAME` is intentionally blank.

```
  export DJANGO_DB_USER=____
  export DJANGO_DB_PASSWORD=____
  export DJANGO_DEBUG_FLAG=True
  export DJANGO_FORCE_SCRIPT_NAME=
```
    
Create a postgres DB called `alexandria`
(Ensure your user account can write to the database)


Have Django setup the database according to the models. From the repo root:

```
./manage.py migrate
```

Create a superuser (follow the prompts):

```
./manage.py createsuperuser
```

## Running and developing

1. Activate your environment:

```
source /path/to/env/<name>/bin/activate
```

2. CD to the repo:

```
cd /some/path/to/repo
```

3. Start Django:

```
./manage.py runserver
```

Go to http://127.0.0.1:8000/ and you should see it.


## Creating sample data
You can run a script that will generate random projects, responses, metrics, and research items. This takes a couple minutes to run.

NOTE: This will remove any existing data every time you run it.

```
./manage.py generate_sample_data
```


### Uploads
For file uploads, you need to setup S3 (Cloud Object Storage) via vars set in `settings.py`


### Pro tip
Create a script alias to do startup Alexandria all this for you:

```
alias startalexandria'source /path/to/this-app-env/bin/activate && cd /some/path/to/repo/ && ./manage.py runserver'
```


## Coding style guidelines
 
We follow the basic Django and Python coding principles and styles:  
https://docs.djangoproject.com/en/4.0/misc/design-philosophies/  
https://docs.djangoproject.com/en/4.0/internals/contributing/writing-code/coding-style/  

 
  &nbsp;
  
