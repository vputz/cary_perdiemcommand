Cary_perdiemcommand
-------------------

This is a command and support script to do simple per diem
requests via email, to get US government per diem data in a
simple query format.

The motivation behind this is that the data is publicly available
but only easily queriable via the http interface at http://www.defensetravel.dod.mil/site/perdiem.cfm ;
it seemed like a useful thing to make it available via an email
gateway with "fuzzy matching" as a test project.

*Note:* the cary_perdiemcommand package is intended as an example project with no
affiliation with the US government, and its use is not condoned or endorsed by the US DOD.
It is only presented here as an example of how to use various elements of
Python.

Requirements
------------

Cary_perdiemcommand makes use of jinja2, tinydb, pyquery, and fuzzywuzzy with python-Levenshtein.

Configuration
-------------

In your Cary `local_conf.py` file, please include configuration
similar to the following (omitting `TEMPLATE_PATH` uses the default templates
included in the module):

```
PERDIEM_CONFIG=dict(
    LOCSTRING_FILENAME="/path/to/locstrings.csv",
    DB_FILENAME="/path/to/perdiem.json",
    TEMPLATE_PATH="/path/to/perdiem/templates"
	)
	...
from cary_perdiemcommand import PerDiemCommand
COMMANDS.update({
    "perdiem": (PerDiemCommand, PERDIEM_CONFIG),
}

```

The `locstrings.csv` and `perdiem.json` files can be generated by the `perdiem_scraper` class
which can download them from the perdiem website.  The templates `plaintext_template.txt` and
`html_template.html` are jinja2 templates which are placed in the configured directory
(one typical configuration is to have a `plugin_data` directory with subdirectories for
each plugin, such as `plugin_data/perdiem`, etc).

Command
-------

The first line of the email body should be a "city, country" or "city, state, country" such
as "Brugges, Belgium" or "Baltimore, MD, USA" (US cities should include state *and* country).


Command-line tool
-----------------

You can execute the module from the shell command line in order to rebuild the database or
do a manual query.  Use `python -m cary_perdiemcommand`; you will have to either pass
locations for the files manually or use an existing settings file.  For example, to rebuild
the database using a local.conf file for the file locations, use

```
python -m cary_perdiemcommand --settings=/path/to/local_conf.py rebuild
```
