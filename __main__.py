import argparse
import json
from importlib.machinery import SourceFileLoader
from cary_perdiemcommand.perdiem_scraper import build_perdiem_database
from cary_perdiemcommand.perdiem_database import PerdiemDatabase


def make_parser():
    parser = argparse.ArgumentParser(
        description="PerDiem scraper for Cary; either rebuild or "
        "query a perdiem database"
        )
    parser.add_argument(
        "command", type=str, choices=['rebuild', 'query'],
        help="command (either 'rebuild' or 'query')")
    parser.add_argument(
        '--settings', type=str,
        help="name of local settings module to get PERDIEM_CONFIG from")
    parser.add_argument(
        '--locstrings', type=str,
        help="locstrings file (usually from config)")
    parser.add_argument(
        '--workdir', type=str,
        help="working directory (default: /tmp)",
        default="/tmp")
    parser.add_argument(
        '--database', type=str,
        help="JSON file (usually from config)")
    parser.add_argument(
        '--location', type=str,
        help="location (mandatory for 'query' command)")
    return parser


def filenames_from_args(args):
    if args.settings is not None:
        config = SourceFileLoader('local_conf', args.settings).load_module()
        locstrings = config.PERDIEM_CONFIG['LOCSTRING_FILENAME']
        database = config.PERDIEM_CONFIG['DB_FILENAME']
    else:
        locstrings = args.locstrings
        database = args.database
    if locstrings is None or database is None:
        raise ValueError
    return locstrings, database


def rebuild(locstrings, database, working_dir):
    build_perdiem_database(locstrings, database, working_dir)


def query(locstrings, database, location):
    db = PerdiemDatabase(locstrings, database)
    print(json.dumps(db.perdiem_query(location),
                     indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    try:
        (locstrings, database) = filenames_from_args(args)
    except ValueError:
        print("\nERROR: you must specify the location strings and database\n"
              "file, either directly with --locstrings and --database or\n"
              "using the --settings argument\n")
        locstrings = None
        database = None
    if locstrings is not None and database is not None:
        if args.command == 'rebuild':
            rebuild(locstrings, database, args.workdir)
        elif args.command == 'query':
            if args.location is None:
                print("\nERROR: Query must have a --location\n")
            else:
                query(locstrings, database, args.location)
