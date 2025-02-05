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
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


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
        talisman.force_https = False

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(
                BASE_URL, json=account.serialize()
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

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
            "date_joined": "2025-01-01"
        }

        resp = self.client.post(
            BASE_URL, json=account_data, content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return resp.get_json()

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(
            BASE_URL, json={"name": "not enough data"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="text/html"
        )
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    def test_read_an_account(self):
        """It should Read a single Account"""
        account = self._create_account()
        self.assertIsNotNone(
            account.get("id"), "Account creation failed, no ID returned."
        )

        resp = self.client.get(
            f"/accounts/{account['id']}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], account["id"])

    def test_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data["error"], "Account not found")

    def test_update_account(self):
        """It should Update an Account"""
        account = self._create_account()  # Creates a new account
        updated_data = {
            "name": "John Updated",
            "email": "john.updated@example.com",
            "address": "456 Updated St",
            "phone_number": "555-5678",
            "date_joined": "2025-02-01"  # Correct format for the date
        }

        resp = self.client.put(
            f"/accounts/{account['id']}",
            json=updated_data,
            content_type="application/json"
        )

        print(resp.data)  # Debugging step: Inspect the response data

        # Ensure the response status is OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        data = resp.get_json()
        print(data)  # Debugging step: Check the returned data

        # Ensure the updated data matches the response
        self.assertEqual(data["name"], updated_data["name"])
        self.assertEqual(data["email"], updated_data["email"])
        self.assertEqual(data["address"], updated_data["address"])
        self.assertEqual(data["phone_number"], updated_data["phone_number"])
        self.assertEqual(data["date_joined"], updated_data["date_joined"])

    def test_delete_account(self):
        """It should Delete an Accountttttttttttttttttttttttt"""
        account = self._create_account()
        resp = self.client.delete(f"/accounts/{account['id']}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data["message"], "Account deleted successfully")

        resp = self.client.get(f"/accounts/{account['id']}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


    def test_list_accounts(self):
        """It should List all Accounts"""
        self._create_accounts(3)
        resp = self.client.get("/accounts", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; object-src 'none'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.headers.get('Access-Control-Allow-Origin'), '*')
