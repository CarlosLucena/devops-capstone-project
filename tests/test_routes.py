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
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
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

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertIsNotNone(new_account["id"], account.id)
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

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
        self.assertEqual(response.status_code,
                         status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    #
    def test_read_account(self):
        """It should read an Account"""
        # account = AccountFactory()
        # response = self.client.post(
        #     BASE_URL,
        #     json=account.serialize(),
        #     content_type="application/json"
        # )
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # url = (BASE_URL + "/" + str(account.id))
        # response = self.client.get(
        #     url,
        #     content_type="application/json"
        # )
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # data = response.get_json()
        # self.assertEqual(data["id"], account.id)
        # self.assertEqual(data["name"], account.name)

        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    #
    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    #
    def test_list_accounts(self):
        """It should get a list of all Account"""

        self._create_accounts(5)
        response = self.client.get(
            BASE_URL,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEquals(len(data), 5)

    #
    def test_update_non_existance_account(self):
        """Update should raise an exception for non-existance account"""
        account = AccountFactory()

        url = BASE_URL + "/" + str(account.id)
        response = self.client.put(url, json=account.serialize(), content_type="application/json")
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    #
    def test_update_account(self):
        """It should update an Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()

        account.id = data["id"]
        account.name = "Carlos"
        account.email = "new@email.com"
        account.address = "new address"
        account.phone_number = "999 999 9999"

        url = (BASE_URL + "/" + str(account.id))
        response = self.client.put(
            url,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["id"], account.id)
        self.assertEqual(data["name"], "Carlos")
        self.assertEqual(data["email"], "new@email.com")
        self.assertEqual(data["address"], "new address")
        self.assertEqual(data["phone_number"], "999 999 9999")

    #
    def test_delete_account(self):
        """It should delete an Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()

        account_id = str(data["id"])
        url = BASE_URL + "/" + account_id
        response = self.client.delete(url, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.get_data()), 0)

        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# def test_method_not_allowed(self):
#         """It should not allow an illegal method call"""
#         resp = self.client.delete(BASE_URL)
#         self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    ######################################################################
    #  Security test cases
    ######################################################################

    def test_security_headers(self):
        """It should contain security headers."""
        response = self.client.get(environ_overrides=HTTPS_ENVIRON)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEquals(response.headers['X-XSS-Protection'], '1; mode=block')
        self.assertEquals(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEquals(response.headers['Content-Security-Policy'], 'default-src \'self\'; object-src \'none\'')
        self.assertEquals(response.headers['Referrer-Policy'], 'strict-origin-when-cross-origin')

    # cors
    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check for the CORS header
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
