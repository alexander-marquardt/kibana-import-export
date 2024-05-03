#!/usr/bin/env python3

import argparse
import requests
import logging
import os
from getpass import getpass

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_spaces(session, url):
    """List all spaces from Kibana."""
    response = session.get(f"{url}/api/spaces/space")
    response.raise_for_status()
    return [space['id'] for space in response.json()]

def export_objects(session, url, export_dir, space_id):
    """Export objects from a given Kibana space."""
    export_url = f"{url}/s/{space_id}/api/saved_objects/_export"
    params = {"type": ["dashboard", "visualization", "search", "index-pattern"]}
    response = session.post(export_url, json=params)
    response.raise_for_status()
    file_path = os.path.join(export_dir, f"{space_id}.ndjson")
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Export successful for space {space_id}: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Export all objects from all spaces in Kibana.",
                                     epilog="Example: export_kibana.py http://localhost:5601 username /path/to/export")
    parser.add_argument('kibana_url', help="Kibana URL, e.g., http://localhost:5601")
    parser.add_argument('username', help="Username for Kibana")
    parser.add_argument('export_dir', help="Directory to save the NDJSON files")
    args = parser.parse_args()

    password = getpass("Enter your password: ")
    session = requests.Session()
    session.auth = (args.username, password)
    session.headers.update({'kbn-xsrf': 'true'})

    if not os.path.exists(args.export_dir):
        os.makedirs(args.export_dir)

    spaces = list_spaces(session, args.kibana_url)
    for space_id in spaces:
        export_objects(session, args.kibana_url, args.export_dir, space_id)

if __name__ == "__main__":
    main()
