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
    params = {"type": object_types or ["*"]}
    logging.info(f"Requesting URL: {export_url} with params: {json.dumps(params)}")
    response = session.post(export_url, json=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to export objects for space {space_id}: {e}")
        logging.error(f"Response was: {response.text}")
        return
    file_path = os.path.join(export_dir, f"{space_id}.ndjson")
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Export successful for space {space_id}: {file_path}")

def validate_spaces_and_types(spaces, types, all_spaces, all_types):
    valid_spaces = [space['id'] for space in all_spaces]
    invalid_spaces = [space for space in spaces if space not in valid_spaces] if spaces else []
    invalid_types = [t for t in types if t not in all_types] if types else []

    if invalid_spaces:
        logging.error("The following specified spaces do not exist: " + ", ".join(invalid_spaces))
    if invalid_types:
        logging.error("The following specified types do not exist: " + ", ".join(invalid_types))

    if invalid_spaces or invalid_types:
        logging.error("Exiting due to invalid input.")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Export objects and details from specified spaces in Kibana, or all spaces if none are specified.",
                                     epilog="Example: export_kibana.py http://localhost:5601 username /path/to/export --spaces space1 space2 --types dashboard visualization")
    parser.add_argument('kibana_url', help="Kibana URL, e.g., http://localhost:5601")
    parser.add_argument('username', help="Username for Kibana")
    parser.add_argument('export_dir', help="Directory to save the NDJSON files and space details")
    parser.add_argument('--types', nargs='+', help="Specify types of objects to export, separated by spaces (e.g., dashboard, visualization). If omitted, all types are exported.")
    parser.add_argument('--spaces', nargs='+', help="Specify space IDs to export, separated by spaces (e.g., space1, space2). If omitted, all spaces are exported.")

    args = parser.parse_args()

    password = getpass("Enter your password: ")
    session = requests.Session()
    session.auth = (args.username, password)
    session.headers.update({'kbn-xsrf': 'true'})

    if not os.path.exists(args.export_dir):
        os.makedirs(args.export_dir)

    all_spaces = get_spaces(session, args.kibana_url)
    all_types = ["dashboard", "visualization", "search", "index-pattern"]  # Example types, adjust as needed

    # Validate the specified spaces and types before proceeding
    validate_spaces_and_types(args.spaces, args.types, all_spaces, all_types)

    spaces_to_export = all_spaces if not args.spaces else [space for space in all_spaces if space['id'] in args.spaces]
    export_space_details(spaces_to_export, args.export_dir)
    for space in spaces_to_export:
        export_objects(session, args.kibana_url, args.export_dir, space, args.types)

if __name__ == "__main__":
    main()
