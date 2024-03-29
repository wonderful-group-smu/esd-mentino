# Importing the relevant files
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from os import environ, times
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS

# Instanitating the flask application
app = Flask(__name__)

# When developing, run init.sql inside MAMP / WAMP and use this line instead for SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("dbURL", default="mysql+mysqlconnector://root:root@localhost:3306/esd_db")


# Instanitating the SQLAlchemy DB
db = SQLAlchemy(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# Creating the database object
# Refer to init.sql for table name and the datatypes
# To keep things simple, I only used varchar and integer, which in flask is String and Integer
class BubbleRole(db.Model):
    __tablename__ = "BubbleRole"

    bubble_id = db.Column(db.String(255), primary_key=True)
    email = db.Column(db.String(255), primary_key=True)
    role = db.Column(db.String(255), nullable=False)

    def __init__(self, bubble_id, email, role):
        self.bubble_id = bubble_id
        self.email = email
        self.role = role

    def json(self):
        return {
            "bubble_id": self.bubble_id,
            "email": self.email,
            "role": self.role
        }


@app.route("/bubble_roles/one/<int:bubble_id>",methods=['GET'])
def get_all_participants_of_bubble(bubble_id: int):
    """
    Get all participants associated with one bubble
    No header needed cos does not pass through Kong
    """
    try:
        bubble_roles_records = BubbleRole.query.filter(BubbleRole.bubble_id == bubble_id).all()
        return_dict = {record.json()["email"]:record.json()["role"] for record in bubble_roles_records}
        return jsonify({
            "code": 200,
            "message": "Got all participants of bubble",
            "data": return_dict
        }),200

    except Exception as err:
        return jsonify({
            "code": 404,
            "message": "Failed to retrieve participants of bubble",
            "data": str(err)
        }), 404
    


@app.route("/bubble_roles/person/<email>",methods=['GET'])
def get_bubbles_of_participant(email):
    """
    Get all bubbles associated with one participant
    No header needed cos does not pass through Kong
    """
    try:
        joined_bubbles = BubbleRole.query.filter(BubbleRole.email == email).all()
        return_dict = {record.json()["bubble_id"]:record.json()["role"] for record in joined_bubbles}
        return jsonify({
            "code": 200,
            "message": "Got all bubbles of participant",
            "data": return_dict
        }),200

    except Exception as err:
        return jsonify({
            "code": 404,
            "message": "Failed to retrieve bubbles of participant -"+ str(err),
        }), 404


@app.route('/bubble_roles/one',methods=['POST','PUT','DELETE'])
def write_bubble_role():
    """
    Add, update and delete bubble roles in database
    """
    if request.method == 'POST':

        json_payload = request.get_json()
        bubble_id = json_payload['bubble_id']
        email = json_payload['email']
        role = json_payload['role']
        try:
            new_bubble_role = BubbleRole(bubble_id, email, role)
            db.session.add(new_bubble_role)
            db.session.commit()
            return jsonify({
                "code": 200,
                "message": "Add record to bubble_role db success",
                "data": new_bubble_role.json()
            }),200
        except Exception as err:
            return jsonify({
                "code": 404,
                "message": "Failed to add record to bubble_role db - "+str(err),
            }), 404

    if request.method == 'PUT':
        json_payload = request.get_json()
        bubble_id = json_payload['bubble_id']
        email = json_payload['email']
        role = json_payload['role']

        try:
            to_be_updated_bubble_role = BubbleRole.query.filter(BubbleRole.bubble_id==bubble_id, BubbleRole.email==email).first()
            if to_be_updated_bubble_role is None:
                return jsonify({
                    "code": 404,
                    "message": "Record not found in bubble_role db"
                }), 404

            to_be_updated_bubble_role.bubble_id = bubble_id
            to_be_updated_bubble_role.email = email
            to_be_updated_bubble_role.role = role
            try:
                db.session.commit()
                return jsonify({
                    "code": 200,
                    "message": "Update record in bubble_role db success",
                    "data": to_be_updated_bubble_role.json()
                }),200

            except IntegrityError:
                return jsonify({
                    "code": 500,
                    "message": "Duplicate entry"
                }), 500

        except Exception as err:
            return jsonify({
                "code": 404,
                "message": "Failed to update record in bubble_role db - "+str(err),
            }), 404

    if request.method == 'DELETE':
        json_payload = request.get_json()
        bubble_id = json_payload["bubble_id"]
        email = json_payload['email']

        try:
            BubbleRole.query.filter(BubbleRole.bubble_id==bubble_id, BubbleRole.email==email).delete()
            db.session.commit()
            return jsonify({
                "code": 200,
                "message": "Delete record in bubble_role db success",
            }),200
        except Exception as err:
            return jsonify({
                "code": 404,
                "message": "Failed to delete record in bubble_role db - "+str(err),
            }), 404


if __name__ == "__main__":
    # There are multiple addresses on machine
    # 0.0.0.0 means machine is listening on all the ports
    PYTHON_ENV = environ.get("PYTHON_ENV", default="DEV")
    app.run(host="0.0.0.0", port=5003, debug=(PYTHON_ENV == "DEV"))
    