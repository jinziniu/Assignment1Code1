from flask import Flask, request, jsonify
import re
import string

app = Flask(__name__)


url_database = {}

# 使用全局计数器生成唯一数字
counter = 1

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
    global counter
    if request.method == 'GET':
        return jsonify(url_database), 200

    elif request.method == 'POST':
        # 创建新的 URL 映射
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({'error': 'Missing URL'}), 400
        long_url = data['value']

        if not validation(long_url):
            return jsonify({'error': 'Invalid URL format'}), 400

        # 使用全局 counter 生成短 id，并进行 Base62 编码
        short_id = encode(counter)
        counter += 1

        url_database[short_id] = long_url
        return jsonify({'id': short_id}), 201

    elif request.method == 'DELETE':

        url_database.clear()
        return jsonify({'error': 'Invalid operation'}), 404

@app.route('/<short_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_short_id(short_id):
    if request.method == 'GET':

        if short_id in url_database:
            long_url = url_database[short_id]

            response = jsonify({'value': long_url})
            response.status_code =301
            return response


        else:
            return jsonify({'error': 'Short URL not found'}), 404

    elif request.method == 'PUT':
        if short_id not in url_database:
            return jsonify({'error': 'Short URL not found'}), 404

        data = request.get_json(force=True)
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL'}), 400

        new_url = data['url']
        if not validation(new_url):
            return jsonify({'error': 'Invalid URL format'}), 400


        url_database[short_id] = new_url
        return jsonify({'message': 'Updated successfully'}), 200


    elif request.method == 'DELETE':

        if short_id in url_database:
            del url_database[short_id]
            return '', 204
        else:
            return jsonify({'error': 'Short URL not found'}), 404

if __name__ == '__main__':
    app.run(port=8000, debug=True)
