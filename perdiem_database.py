from tinydb import TinyDB, where
from cary_perdiemcommand.perdiem_scraper import perdiem_url, perdiem_query, conus_files
from cary_perdiemcommand.perdiem_scraper import oconus_files, perdiem_dateformat
import datetime
import csv
from fuzzywuzzy import process


class PerdiemDatabase():

    def __init__(self, locstrings_filename, database_filename):
        self.locstrings_filename = locstrings_filename
        self.db = TinyDB(database_filename)

    def metadata(self):
        return self.db.table("metadata").all()[0]

    def last_conus_date(self):
        return datetime.datetime.strptime(self.metadata()["conus_date"],
                                          perdiem_dateformat)

    def last_oconus_date(self):
        return datetime.datetime.strptime(self.metadata()["oconus_date"],
                                          perdiem_dateformat)

    def latest_conus_date(self):
        conus_urls = conus_files(perdiem_query(), perdiem_url)
        return datetime.datetime.strptime(conus_urls[0][0],
                                          perdiem_dateformat)

    def latest_oconus_date(self):
        oconus_urls = oconus_files(perdiem_query(), perdiem_url)
        return datetime.datetime.strptime(oconus_urls[0][0],
                                          perdiem_dateformat)

    def is_current(self):
        """
        Queries the per diem site to see if files are current
        """
        return self.last_conus_date() >= self.latest_conus_date()\
          and self.last_oconus_date() >= self.latest_oconus_date()

    def currency_check(self):
        dateformat = "%d %B %Y"
        return dict(
            is_current=self.is_current(),
            conus_last=self.last_conus_date().strftime(dateformat),
            conus_latest=self.latest_conus_date().strftime(dateformat),
            oconus_last=self.last_oconus_date().strftime(dateformat),
            oconus_latest=self.latest_oconus_date().strftime(dateformat),
            )

    def closest_locstrings(self, query, threshold=90, max_results=5):
        # list everything matching location
        with open(self.locstrings_filename) as csvfile:
            r = csv.reader(csvfile)
            result = process.extract(query, r,
                                     processor=lambda x: x[0],
                                     limit=max_results)
            return [(x[0][1], x[1]) for x in result if x[1] > threshold]

    def perdiem_from_key(self, key):
        return self.db.table("records").search(where('key') == key)[0]

    def sorted_seasons_from_key(self, key):
        perdiem = self.perdiem_from_key(key)
        seasons = sorted(perdiem['seasons'],
                         key=lambda x: datetime.datetime.strptime(
                             x['eff_date'],
                             "%m/%d/%Y"))
        return seasons

    def punt_location_guess(self, query):
        parts = query.split(",")
        parts[0] = "[other]"
        newquery = ",".join(parts)
        return newquery

    def locstrings_with_punt(self, query, threshold=90, max_results=5):
        result = self.closest_locstrings(query, threshold, max_results)

        if len(result) == 0:
            query = self.punt_location_guess(query)
            result = self.closest_locstrings(query,
                                             threshold, max_results)
        return (query, result)

    def perdiem_query(self, original_location):
        queried_location, ls = self.locstrings_with_punt(original_location)
        found = (len(ls) > 0)
        closest_matches = [dict(score=l[1],
                                location=l[0],
                                seasons=self.sorted_seasons_from_key(l[0]))
                                for l in ls]
        return dict(
            currency_check=self.currency_check(),
            original_search_location=original_location,
            actual_queried_location=queried_location,
            found=found,
            closest_matches=closest_matches,
            conus_url=self.metadata()['conus_url'],
            oconus_url=self.metadata()['oconus_url']
            )
