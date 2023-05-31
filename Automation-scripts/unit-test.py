# Import required libraries and modules
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from project_destroyer import fetch_bank_holidays, is_project_ignored, is_project_stale, should_reap_based_on_labels, calculate_non_working_days

# Define the TestMain class which inherits from unittest.TestCase
class TestMain(unittest.TestCase):

    # Test the fetch_bank_holidays function
    def test_fetch_bank_holidays(self):
        # Mock the requests.get function
        with patch("requests.get") as mock_get:
            # Create a mock response object
            mock_response = MagicMock()
            # Set the return value for the json method of the mock response
            mock_response.json.return_value = {
                "england-and-wales": {
                    "events": [
                        {"title": "Test holiday", "date": "2023-01-01"}
                    ]
                }
            }
            # Set the return value for the mock_get function
            mock_get.return_value = mock_response
            # Call the fetch_bank_holidays function and store the result
            bank_holidays = fetch_bank_holidays()
            # Assert that the length of the bank_holidays list is 1
            self.assertEqual(len(bank_holidays), 1)
            # Assert that the title of the first bank holiday is "Test holiday"
            self.assertEqual(bank_holidays[0]["title"], "Test holiday")

    # Test the is_project_ignored function
    def test_is_project_ignored(self):
        # Create a mock project object
        project = MagicMock()
        # Set the labels attribute of the mock project
        project.labels = {"destroyer_behaviour": "ignore"}
        # Assert that the project is ignored
        self.assertTrue(is_project_ignored(project))

        # Change the labels attribute of the mock project
        project.labels = {"destroyer_behaviour": "reap"}
        # Assert that the project is not ignored
        self.assertFalse(is_project_ignored(project))

    # Test the should_reap_based_on_labels function
    def test_should_reap_based_on_labels(self):
        # Create a mock project object
        project = MagicMock()
        project.display_name = "Test project"
        # Test different cases for the should_reap_based_on_labels function
        self.assertFalse(should_reap_based_on_labels(project, None, None))
        self.assertFalse(should_reap_based_on_labels(project, "ignore", "2022-01-01"))
        self.assertTrue(should_reap_based_on_labels(project, "reap", "2022-01-01"))

    # Test the calculate_non_working_days function
    def test_calculate_non_working_days(self):
        # Define the modified_date and now variables
        modified_date = datetime.strptime("2022-01-01", "%Y-%m-%d")
        now = datetime.strptime("2022-01-10", "%Y-%m-%d")
        # Define the bank_holidays list
        bank_holidays = [
            {"title": "Test holiday", "date": "2022-01-03"}
        ]
        # Call the calculate_non_working_days function and store the result
        non_working_days = calculate_non_working_days(modified_date, bank_holidays, now)
        # Assert that the number of non_working_days is 5
        self.assertEqual(non_working_days, 5)

    # Test the is_project_stale function
    def test_is_project_stale(self):
        # Create a mock project object
        project = MagicMock()
        project.display_name = "Test project"
        # Set the labels attribute of the mock project
        project.labels = {
            "destroyer_behaviour": "reap",
            "modified_date": "2022-01-01"
        }
        # Define the bank_holidays list
        bank_holidays = [
            {"title": "Test holiday", "date": "2022-01-03"}
        ]
        # Assert that the project is stale when inactive_days_for_reaping is set to 2
        self.assertTrue(is_project_stale(project, bank_holidays, inactive_days_for_reaping=2))

# Run the unittest main function
if __name__ == "__main__":
    unittest.main()