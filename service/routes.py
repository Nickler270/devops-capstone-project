"""
Account Service

This microservice handles the lifecycle of Accounts
"""

# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an
    Account based on the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url =
    # url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# LIST ALL ACCOUNTS
######################################################################
@app.route("/accounts", methods=["GET"])
def list_accounts():
    """List all accounts"""
    accounts = Account.all()
    account_list = [account.serialize() for account in accounts]
    return jsonify(account_list), 200


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route('/accounts/<int:id>', methods=['GET'])
def get_account(id):
    """Fetch an account by ID"""
    account = Account.query.get(id)
    if account:
        return jsonify(account.serialize()), 200
    else:
        # Change error message to match test expectation
        return jsonify({"error": "Account not found"}), 404


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################
@app.route('/accounts/<int:id>', methods=['PUT'])
def update_account(id):
    """Update an Account"""
    account = Account.query.get(id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    # Deserialize the incoming request data
    data = request.get_json()
    account.name = data.get("name", account.name)
    account.email = data.get("email", account.email)
    account.address = data.get("address", account.address)
    account.phone_number = data.get("phone_number", account.phone_number)
    account.date_joined = data.get("date_joined", account.date_joined)

    account.update()  # Save changes to the database
    return jsonify(account.serialize()), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """Delete an account by ID"""
    account = Account.find(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    account.delete()
    return jsonify({"message": "Account deleted successfully"}), 200


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
