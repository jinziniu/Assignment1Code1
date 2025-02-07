from flask import Flask, request, jsonify
import re
import string
from database import db,URLMapping

app = Flask(__name__)

#database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


def validation(url):
    regex = r'^(https?://)' \
            r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})' \
            r'(:\d+)?' \
            r'(/\S*)?$'
    return re.match(regex, url) is not None


F = 100000
def encode(num):
   #base 62
    char = string.digits + string.ascii_lowercase + string.ascii_uppercase
    base = len(char)
    num += F
    result = []
    while num:
        result.append(char[num % base])
        num //= base
    return ''.join(reversed(result))

@app.route('/', methods=['GET', 'POST', 'DELETE'])
def root():

    if request.method == 'GET':
        mappings = URLMapping.query.all()
        result = {mapping.shortid: mapping.long_url for mapping in mappings}
        return jsonify(result), 200

    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({'error': 'Missing URL'}), 400
        long_url = data['value']

        if not validation(long_url):
            return jsonify({'error': 'Invalid URL format'}), 400

        new_mapping = URLMapping(long_url=long_url, shortid='')
        db.session.add(new_mapping)
        db.session.commit()

        short_id = encode(new_mapping.id)
        new_mapping.shortid = short_id
        db.session.commit()
        return jsonify({'id': short_id}), 201


    elif request.method == 'DELETE':

        db.session.query(URLMapping).delete()
        db.session.commit()
    return jsonify({'error': 'Invalid operation'}), 404

@app.route('/<short_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_short_id(short_id):
    mapping = URLMapping.query.filter_by(shortid= short_id).first()

    if request.method == 'GET':
        if mapping:
            mapping.visit_count +=1
            db.session.commit()

            response = jsonify({'value': mapping.long_url})
            response.status_code =301
            return response


        else:
            return jsonify({'error': 'Short URL not found'}), 404

    elif request.method == 'PUT':
        if not mapping:
            return jsonify({'error': 'Short URL not found'}), 404

        data = request.get_json(force=True)
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL'}), 400

        new_url = data['url']
        if not validation(new_url):
            return jsonify({'error': 'Invalid URL format'}), 400


        mapping.long_url = new_url
        db.session.commit()
        return jsonify({'message': 'Updated successfully'}), 200


    elif request.method == 'DELETE':

        if mapping:
            db.session.delete(mapping)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'Short URL not found'}), 404

if __name__ == '__main__':
    app.run(port=8000, debug=True)
