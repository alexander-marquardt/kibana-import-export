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

def export_objects(session, url, export_dir, space, object_types):
    space_id = space['id']
    export_url = f"{url}/s/{space_id}/api/saved_objects/_export"
    # Handle types: if no types are provided, use '*' to export all types
    params = {"type": object_types or ["*"]}
    logging.info(f"Requesting URL: {export_url} with params: {json.dumps(params)}")
    response = session.post(export_url, json=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to export objects: {e}")
        logging.error(f"Response was: {response.text}")
        raise
    file_path = os.path.join(export_dir, f"{space_id}.ndjson")
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Export successful for space {space_id}: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Export objects and details from all spaces in Kibana.",
                                     epilog="Example: export_kibana.py http://localhost:5601 username /path/to/export --types dashboard visualization")
    parser.add_argument('kibana_url', help="Kibana URL, e.g., http://localhost:5601")
    parser.add_argument('username', help="Username for Kibana")
    parser.add_argument('export_dir', help="Directory to save the NDJSON files and space details")
    parser.add_argument('--types', nargs='+', help="Specify types of objects to export (e.g., dashboard visualization)")

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
        export_objects(session, args.kibana_url, args.export_dir, space, args.types)

if __name__ == "__main__":
    main()
