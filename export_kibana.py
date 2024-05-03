#!/usr/bin/env python3

import argparse
import requests
import logging
import os
import json
from getpass import getpass

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_spaces(session, url):
    """Retrieve all spaces."""
    response = session.get(f"{url}/api/spaces/space")
    response.raise_for_status()
    return response.json()

def export_space_details(spaces, export_dir):
    """Save space details to a JSON file."""
    with open(os.path.join(export_dir, 'spaces_details.json'), 'w') as file:
        json.dump(spaces, file)
    logging.info("Exported space details.")

def export_objects(session, url, export_dir, space):
    """Export objects from a given space and save space details."""
    space_id = space['id']
    export_url = f"{url}/s/{space_id}/api/saved_objects/_export"
    params = {"type": ["dashboard", "visualization", "search", "index-pattern"]}
    response = session.post(export_url, json=params)
    response.raise_for_status()
    file_path = os.path.join(export_dir, f"{space_id}.ndjson")
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Export successful for space {space_id}: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Export all objects and details from all spaces in Kibana.",
                                     epilog="Example: export_kibana.py http://localhost:5601 username /path/to/export")
    parser.add_argument('kibana_url', help="Kibana URL, e.g., http://localhost:5601")
    parser.add_argument('username', help="Username for Kibana")
    parser.add_argument('export_dir', help="Directory to save the NDJSON files and space details")
    args = parser.parse_args()

    password = getpass("Enter your password: ")
    session = requests.Session()
    session.auth = (args.username, password)
    session.headers.update({'kbn-xsrf': 'true'})

    if not os.path.exists(args.export_dir):
        os.makedirs(args.export_dir)

    spaces = get_spaces(session, args.kibana_url)
    export_space_details(spaces, args.export_dir)
    for space in spaces:
        export_objects(session, args.kibana_url, args.export_dir, space)

if __name__ == "__main__":
    main()
