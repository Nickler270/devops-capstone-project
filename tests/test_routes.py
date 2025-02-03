"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def _create_account(self, name="John Doe", email="john.doe@example.com"):
        """Helper method to create a single account for testing"""
        account_data = {
            "name": name,
            "email": email,
            "address": "123 Main St",
            "phone_number": "555-1234",
            "date_joined": "2025-01-01"  # Example date format
        }

        # POST request to create the account
        resp = self.client.post(
            BASE_URL,
            json=account_data,
            content_type="application/json"
        )

        # Ensure account creation was successful
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Return the created account's JSON data (including the ID assigned by the DB)
        return resp.get_json()  # Return the created account's data


    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_read_an_account(self):
        """It should Read a single Account"""
        
        # Create a new account via the helper function
        account = self._create_account()  # This will create and return the account data
        
        # Check if the account has been created
        self.assertIsNotNone(account.get("id"), "Account creation failed, no ID returned.")
        
        # Send a GET request to read the account by id
        resp = self.client.get(f"/accounts/{account['id']}", content_type="application/json")
        
        # Assert that the response status code is HTTP_200_OK (successful retrieval)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # Get the JSON response data
        data = resp.get_json()

        # Assert that the returned account data matches the data that was sent
        self.assertEqual(data["id"], account["id"])
        self.assertEqual(data["name"], account["name"])
        self.assertEqual(data["email"], account["email"])
        self.assertEqual(data["address"], account["address"])
        self.assertEqual(data["phone_number"], account["phone_number"])
        self.assertEqual(data["date_joined"], account["date_joined"])

    def test_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")  # Use an ID that does not exist
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data["error"], "Account not found")
