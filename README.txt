This code is designed to make it easy to migrate spaces and associated objects such as visualizations and
dashboards from one Kibana instance to another. For example, if migrating from an on-premises Elasticsearch and
Kibana installation to an Elastic Cloud service, you may find these scripts to be helpful.

The preferred manner to migrate is still to use snapshot and restore functionality, but in some instances that
may not be possible, and then exporting/importing objects from Kibana becomes the alternative route. However,
manually doing this through the UI is tedious,and so the two scripts here 'export_kibana.py' and
'import_kibana.py' are designed to automate this process.


To set up this project, please follow these steps:

1. If you don't already have Python, install Python 3 from [https://python.org/](https://python.org/)
2. Download and unzip the project files.
3. Open a command line or terminal in the project directory.
4. Install the required Python libraries with: `pip install -r requirements.txt`
5. Run the script with either 'export_kibana.py' or 'import_kibana.py'

