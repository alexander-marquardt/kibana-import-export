#!/usr/bin/env python3

import argparse
import requests
import logging
import os
import json
from getpass import getpass

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_space_if_not_exists(session, url, space_details):
    """Create a space if it does not already exist, using detailed metadata."""
    space_id = space_details['id']
    check_url = f"{url}/api/spaces/space/{space_id}"
    res = session.get(check_url)
    if res.status_code == 404:  # Space does not exist
        create_res = session.post(f"{url}/api/spaces/space", json=space_details)
        create_res.raise_for_status()
        logging.info(f"Space '{space_id}' created successfully.")
    elif res.status_code != 200:
        res.raise_for_status()


def import_objects(session, url, file_path, params, space_id):
    """Import objects into a Kibana space."""
    # Construct the URL with query parameters
    import_url = f"{url}/s/{space_id}/api/saved_objects/_import"
    query_params = {}
    if params.get('overwrite'):
        query_params['overwrite'] = 'true'
    if params.get('createNewCopies'):
        query_params['createNewCopies'] = 'true'
    if params.get('compatibilityMode'):
        query_params['compatibilityMode'] = 'true'

    # Prepare headers
    headers = {'kbn-xsrf': 'true'}

    # Log the action
    logging.info(f"Posting to {import_url} headers={headers} query_params={query_params}")

    # Open the file and prepare it for sending
    with open(file_path, 'rb') as file:
        files = {'file': ('export.ndjson', file, 'application/ndjson')}
        # Send the POST request with the file and query parameters
        response = session.post(import_url, headers=headers, files=files, params=query_params)

        try:
            response.raise_for_status()
            logging.info(f"Import successful to {url} for space {space_id}")
        except requests.exceptions.HTTPError as e:
            logging.error(f"Failed to import objects for space {space_id}: {e}")
            logging.error(f"Response was: {response.text}")
            if "conflict" in response.text:
                logging.error(
                    "There are conflicts with existing objects. Consider using the 'overwrite' or 'createNewCopies' options.")
            raise

        # Optionally log the response content for debugging
        logging.debug(f"Response Content: {response.text}")


def main():
    parser = argparse.ArgumentParser(description="Import objects to Kibana from NDJSON files for all spaces.",
                                     epilog="Example: import_kibana.py https://your-kibana-url.com username /path/to/imports")
    parser.add_argument('kibana_url', help="Kibana URL, e.g., https://your-kibana-url.com")
    parser.add_argument('username', help="Username for Kibana")
    parser.add_argument('import_dir', help="Directory containing NDJSON files")
    parser.add_argument('--noOverwrite', action='store_true', help="Don't overwrite existing objects. Must be specified if you define --createNewCopies")
    parser.add_argument('--createNewCopies', action='store_true', help="Create new copies of the objects, avoiding conflicts")
    parser.add_argument('--compatibilityMode', action='store_true', help="Enable compatibility mode, cannot be used with --createNewCopies")

    args = parser.parse_args()



    password = getpass("Enter your password: ")
    session = requests.Session()
    session.auth = (args.username, password)
    session.headers.update({'kbn-xsrf': 'true'})

    params = {}
    # set overwrite to true by default
    if args.noOverwrite:
        params['overwrite'] = False
    else:
        params['overwrite'] = True

    # Other params are false, unless specified
    if args.createNewCopies:
        params['createNewCopies'] = True
    else:
        params['createNewCopies'] = False

    if args.compatibilityMode:
        params['compatibilityMode'] = True
    else:
        params['compatibilityMode'] = False

    # Enforce mutual exclusivity
    if params['createNewCopies'] and (params['overwrite'] or params['compatibilityMode']):
        parser.error("""The createNewCopies option cannot be used with overwrite or compatibilityMode.
        See: https://www.elastic.co/guide/en/kibana/current/saved-objects-api-import.html""")
        exit()

    space_details_path = os.path.join(args.import_dir, 'spaces_details.json')
    with open(space_details_path, 'r') as file:
        spaces_details = json.load(file)

    print("About to import the following spaces with the specified modes:")
    for space_detail in spaces_details:
        print(f"- {space_detail['id']} (New Copies: {params['createNewCopies']}, Overwrite: {params['overwrite']}, "
              f"Compatibility Mode: {params['compatibilityMode']})")
    if input("Proceed with import? (yes/no) ") != "yes":
        print("Import canceled.")
        return

    for space_detail in spaces_details:
        space_id = space_detail['id']
        create_space_if_not_exists(session, args.kibana_url, space_detail)
        file_path = os.path.join(args.import_dir, f"{space_id}.ndjson")
        import_objects(session, args.kibana_url, file_path, params, space_id)

if __name__ == "__main__":
    main()
