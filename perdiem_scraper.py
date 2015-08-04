from pyquery import PyQuery as pq
import urllib
from urllib.parse import urljoin
import datetime
import re
import shutil
from zipfile import ZipFile
from fnmatch import fnmatch
import csv
from tinydb import TinyDB
import itertools
import os

perdiem_url = "http://www.defensetravel.dod.mil/site/perdiemFiles.cfm"
perdiem_dateformat = "%d %B %Y"


def perdiem_query():
    return pq(perdiem_url)


def conus_files(q, base_url):
    """
    Find dates and URLs for the most recent conus and oconus files;
    Ideally, we want a list of dates/files so we can pick the most
    recent one
    """
    result = []
    # it's a poorly-constructed webpage.  This is the first ul after
    # a paragraph containing the phrase "CONUS Locations"
    conus_locations_list = q(
        'p b:contains("CONUS Locations")'
        ).parent().next().children('li')
    for i in range(0, len(conus_locations_list)):
        item = conus_locations_list.eq(i)

        date = item('b:contains("Effective")').text()
        date_text = re.search(r"(\d+\s\w+\s\d+)", date).group(0)

        file_url = item('a:contains("Relational")').attr("href")
        result.append((date_text, urljoin(base_url, file_url)))
    return result


def oconus_files(q, base_url):
    result = []
    oconus_locations_list = q(
        'p b:contains("OCONUS and Foreign")'
        ).parent().next().children('li')
    for i in range(0, len(oconus_locations_list)):
        item = oconus_locations_list.eq(i)

        date = item('b:contains("Effective")').text()
        date_text = re.search(r"(\d+\s\w+\s\d+)", date).group(0)

        file_url = item('a:contains("Relational")').attr("href")
        result.append((date_text, urljoin(base_url, file_url)))
    return result


def retrieve_file(url, filename):
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response,\
      open(filename, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def file_from_zip(zipfile, filepattern):
    """
    Retrieve a file-like object from a zipfile
    """
    z = ZipFile(zipfile)
    files = [x for x in z.namelist() if fnmatch(x, filepattern)]
    assert len(files) == 1
    result = z.read(files[0]).decode('utf-8')
    z.close()
    return result


# Build a searchable data structure from the XML files
# unfortunately the text version is clunky and space-delimited
def row_from_record(r):
    def field(name):
        fields = r(name)
        if len(fields) == 0:
            return None
        else:
            return r(name).text()

    def locstrings(row):
        result = []
        if row['country_code'] == 'USA':
            result.append(", ".join([row["location"], row["state_name"]]))
            result.append(", ".join([row["location"], row["state_alpha"]]))
        else:
            result.append(", ".join([row["location"], row["country_code"]]))
            result.append(", ".join([row["location"], row["country"]]))
        return result
    fieldmap = dict(
        location="location_name",
        country="country_name",
        country_code="country_code",
        eff_date="eff_date",
        exp_date="exp_date",
        lodging="lodging_rate",
        meals="local_meals",
        prop_meals="proportional_meals_rate",
        incidentals="incidentals",
        state_alpha="state_alpha",
        state_name="state_name"
        )
    result = {}
    for k, v in fieldmap.items():
        result[k] = field(v)
    if result['country'] is None and result['country_code'] is None:
        result['country'] = 'UNITED STATES'
        result['country_code'] = 'USA'
    result['locstrings'] = locstrings(result)
    return result


# now build the full data structure.  We return a dict simply because
# each location key may have different entries for dates, times, etc.
# To make it better we could have a more defined structure.
def dict_from_query(q):
    result = {}

    def key(row):
        if row['state_alpha'] is not None:
            return ", ".join((row['location'],
                              row['state_alpha'],
                              row['country_code']))
        else:
            return ", ".join((row['location'],
                              row['country_code']))

    def season_from_row(row):
        return dict(
            eff_date=row['eff_date'],
            exp_date=row['exp_date'],
            lodging=row['lodging'],
            meals=row['meals'],
            prop_meals=row['prop_meals'],
            incidentals=row['incidentals']
        )

    def loc_record_from_row(row):
        return dict(
            location=row['location'],
            country=row['country'],
            country_code=row['country_code'],
            state_alpha=row['state_alpha'],
            state_name=row['state_name'],
            seasons=[season_from_row(row)],
            locstrings=row['locstrings']
        )

    def add_record(index, node):
        row = row_from_record(pq(node))
        this_key = key(row)
        if this_key not in result:
            result[this_key] = loc_record_from_row(row)
        else:
            result[this_key]['seasons'].append(season_from_row(row))
    records = q("record")
    records.each(add_record)
    return result


def create_database_from_dict(filename, record_dict):
    def record_from_item(item):
        result = dict(item[1])
        result['key'] = item[0]
        return result

    db = TinyDB(filename)
    db.purge()
    db.purge_tables()
    table = db.table("records")
    table.insert_multiple((record_from_item(x) for x in record_dict.items()))


def update_database_metadata(database_filename,
                             last_conus_entry,
                             last_oconus_entry,
                             download_date):
    db = TinyDB(database_filename)
    table = db.table("metadata")
    table.insert(dict(conus_url=last_conus_entry[1],
                      conus_date=last_conus_entry[0],
                      oconus_url=last_oconus_entry[1],
                      oconus_date=last_oconus_entry[0],
                      download_date=download_date))


def create_locstrings_from_dict(filename, record_dict):
    with open(filename, "w") as csvfile:
        w = csv.writer(csvfile)
        for row in itertools.chain.from_iterable(
                ((l, x[0]) for l in x[1]['locstrings'])
                for x in record_dict.items()
                ):
            w.writerow(row)


def build_perdiem_database(locstrings_filename,
                           database_filename,
                           working_directory):
    # download the urls from the per diem site
    q = perdiem_query()
    conus_urls = conus_files(q, perdiem_url)
    oconus_urls = oconus_files(q, perdiem_url)
    # download the files
    latest_conus_url = conus_urls[0][1]
    latest_conus_fn = os.path.join(working_directory, "conus.zip")
    latest_oconus_url = oconus_urls[0][1]
    latest_oconus_fn = os.path.join(working_directory, "oconus.zip")
    retrieve_file(latest_conus_url, latest_conus_fn)
    retrieve_file(latest_oconus_url, latest_oconus_fn)
    # get the zipped xml data
    conusdata = file_from_zip(latest_conus_fn, "conusallhist*xml")
    oconusdata = file_from_zip(latest_oconus_fn, "ocallhist*xml")
    conusq = pq(conusdata)
    oconusq = pq(oconusdata)
    conusdict = dict_from_query(conusq)
    oconusdict = dict_from_query(oconusq)
    alldict = dict(conusdict, **oconusdict)
    # now create the database and locstrings
    create_database_from_dict(database_filename, alldict)
    today = datetime.date.today().strftime(perdiem_dateformat)
    update_database_metadata(database_filename,
                             conus_urls[0],
                             oconus_urls[0],
                             today)
    create_locstrings_from_dict(locstrings_filename, alldict)
