import requests
import sys
import os
import argparse
import google.auth
from google.cloud.resourcemanager_v3 import ProjectsClient
from datetime import datetime, timedelta

# env variable to set your organisation id on google cloud platform 
ORG_TO_DESTROY = os.getenv("ORG_TO_DESTROY", "organizations/please enter you org id")

def fetch_bank_holidays():
    # Define the URL to fetch bank holidays data
    url = "https://www.gov.uk/bank-holidays.json"

    # Try to fetch the data from the URL
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching bank holidays from gov.uk: {error}")
        sys.exit(1)

    # Check if the response contains JSON data
    try:
        data = response.json()
    except ValueError as error:
        print(f"Error parsing JSON data: {error}")
        sys.exit(1)

    # Check if the JSON data contains the required information
    if "england-and-wales" not in data or "events" not in data["england-and-wales"]:
        print("Error: Required information not found in the JSON data")
        sys.exit(1)

    # Return the list of bank holidays
    return data["england-and-wales"]["events"]

def is_project_ignored(project):
    #ignoring the projects which have set ignore label on them
    destroyer_behaviour = project.labels.get("destroyer_behaviour", "ignore")
    ignore = destroyer_behaviour == "ignore"
    if ignore:
        print(f"{project.display_name} is set to be ignored due to 'destroyer_behaviour' label: {destroyer_behaviour}")

    return ignore

def is_project_stale(project, bank_holidays, inactive_days_for_reaping=2):
    # If the project has no labels, it is considered stale
    if not project.labels.keys():
        print(f"{project.display_name} has no labels and should be reaped")
        return True

    # Get the necessary labels from the project
    destroyer_behaviour = project.labels.get("destroyer_behaviour", None)
    modified_date = project.labels.get("modified_date", None)

    # Check if the project should be reaped based on its labels
    if not should_reap_based_on_labels(project, destroyer_behaviour, modified_date):
        return False

    # Convert the modified_date string to a datetime object, if possible
    if modified_date is not None:
        try:
            modified_date = datetime.strptime(modified_date, "%Y-%m-%d")
        except ValueError:
            print(f"{project.display_name} has an invalid modified_date format, will not be reaped!")
            return False
    else:
        print(f"{project.display_name} is missing modified_date, will not be reaped!")
        return False

    # Calculate the current date and the number of non-working days
    now = datetime.now()
    number_non_working_days = calculate_non_working_days(modified_date, bank_holidays, now)

    # Calculate the number of working days without deployment
    working_days_without_deployment = (now - modified_date).days - number_non_working_days

    # Check if the project is stale based on the number of inactive days
    stale_project = working_days_without_deployment > inactive_days_for_reaping

    # Print a message if the project is stale
    if stale_project:
        print(
            f"{project.display_name} should be reaped. It has not been deployed to for {working_days_without_deployment} days. The last modified date is: {modified_date}. The 'destroyer_behaviour' label is set to '{destroyer_behaviour}'"
        )

    return stale_project

# Function to determine if a project should be reaped based on its labels
def should_reap_based_on_labels(project, destroyer_behaviour, modified_date):
    # If both destroyer_behaviour and modified_date are missing, the project will not be reaped
    if destroyer_behaviour is None and modified_date is None:
        print(f"{project.display_name} has labels {project.labels.keys()} but missing destroyer labels, will not be reaped!")
        return False

    # If the destroyer_behaviour is set to "ignore" or "no-reap", the project will not be reaped
    if destroyer_behaviour in ("ignore", "no-reap"):
        print(f"{project.display_name} is set to {destroyer_behaviour} destroyer behaviour and will not be reaped")
        return False

    return True

# Function to calculate the number of non-working days between the modified_date and the current date
def calculate_non_working_days(modified_date, bank_holidays, now):
    # Function to check if a date is a bank holiday
    def is_bank_holiday(date, bank_holidays):
        for holiday in bank_holidays:
            if date == datetime.strptime(holiday["date"], "%Y-%m-%d"):
                return True
        return False

    # Initialize the count of non-working days
    non_working_days_count = 0

    # Iterate through all days between modified_date and now
    current_date = modified_date
    while current_date <= now:
        # Check if the current date is a weekday and not a bank holiday
        if current_date.weekday() not in (5, 6) and not is_bank_holiday(current_date, bank_holidays):
            non_working_days_count += 1

        # Move to the next day
        current_date += timedelta(days=1)

    return non_working_days_count

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--list-feature-envs",
        action="store_true",
        help="Prints all feature environments, regardless of whether they should be reaped",
        dest="list_feature_envs",
    )
    args = parser.parse_args()

    # Fetch the list of bank holidays
    bank_holidays = fetch_bank_holidays()

    # Authenticate and create a projects client
    credentials, _ = google.auth.default()
    projects_client = ProjectsClient(credentials=credentials)

    # Get the list of projects, filtering out ignored projects
    projects = [
        project
        for project in projects_client.list_projects(parent=ORG_TO_DESTROY)
        if not is_project_ignored(project)
    ]

    # If the list_feature_envs option is set, print all feature environments
    if args.list_feature_envs:
        feature_environments = [
            project.display_name
            for project in projects
            if "development" in project.display_name
        ]
        for project in feature_environments:
            tier = "-".join(project.split("-")[2:])
            print(tier)

        return

    # Get the list of projects that need to be reaped
    projects_to_reap = [p for p in projects if is_project_stale(p, bank_holidays, inactive_days_for_reaping=2)]

    # Print the number of projects that need reaping
    print(f"Out of {len(projects)} projects, {len(projects_to_reap)} need reaping.")
    
    # Iterate through the projects to be reaped
    for project in projects_to_reap:
        # Ignore projects that are not developer deployments
        if "development" not in project.display_name:
            print(f"Ignoring Project {project.display_name} as it does not appear to be a developer environment.")
            continue

        # Extract the tier from the project display name
        tier = "-".join(project.display_name.split("-")[2:])

        # Ignore projects with a tier that starts with "prod" but not "prod-"
        if tier.startswith("production") and not tier.startswith("production-"):
            continue

        # Print the tier of the project to be reaped
        print(tier)

if __name__ == "__main__":
    main()