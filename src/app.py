"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from utils import APIException, generate_sitemap
from datastructures import FamilyStructure
from flask import current_app
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

# creates the jackson family object
jackson_family = FamilyStructure("Jackson")

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/members', methods=['GET'])
def handle_members():
    # here we use the Family datastructure by calling its methods
    members = jackson_family.get_all_members()

    if not members:
        # Return a JSON response with a 400 status code and an error message
        return jsonify({"error": "Bad request: No members found"}), 400

    response_body = {
        "members": members
    }
    return jsonify(response_body), 200

@app.route('/member/<int:member_id>', methods=['GET'])
def get_member(member_id):
    member = jackson_family.get_member(member_id)

    if member is None:
        return jsonify({"error": "Member not found"}), 400
    
    response_body = {
        "id": member["id"],
        "first_name": member["first_name"],
        "last_name": member ["last_name"],
        "age": member["age"],
        "lucky_numbers": member["lucky_numbers"]
    }
    return jsonify(response_body), 200

@app.route('/add-member', methods=['POST'])
def add_member():
    data = request.json

    # Check if required fields are present in the request data
    if 'first_name' not in data or 'age' not in data or 'lucky_numbers' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    provided_id = data.get('id')
    # Check if provided ID is already in use
    if provided_id and any(existing_member["id"] == provided_id for existing_member in jackson_family.get_all_members()):
        current_app.logger.error(f"Provided member ID ({provided_id}) is already in use")
        return jsonify({"error": "Provided member ID is already in use. Please use another ID or don't provide one."}), 400


    new_member = {
        "id": data.get('id', jackson_family._generateId()),  # Generate ID if not provided
        "first_name": data['first_name'],
        "last_name": data ["last_name"],
        "age": data['age'],                                              
        "lucky_numbers": data.get('lucky_numbers', []),
    }

    current_app.logger.debug(f"New member data: {new_member}")

    #Adds the new member to the family data structure
    member_id = jackson_family.add_member(new_member)

    # Retrieves the new member's details
    added_member = jackson_family.get_member(member_id) 

    current_app.logger.debug(f"Added member: {added_member}")


    response_body = {
        "id": added_member["id"],
        "first_name": added_member["first_name"],
        "last_name": added_member ["last_name"],
        "age": added_member["age"],
        "lucky_numbers": added_member["lucky_numbers"]
    }
    return jsonify(response_body), 200

@app.route('/delete-member/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    delete_success = jackson_family.delete_member(member_id)

    # if deletion success, returns json response 200
    if delete_success:
        return jsonify ({
            "msg": f"Member {delete_success['first_name']} with ID {member_id} deleted", 
            }), 200
    
    else:
        return jsonify ({"error": "Member not found"}), 400



# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
