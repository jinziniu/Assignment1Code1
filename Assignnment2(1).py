from flask import Flask, request, jsonify
import re
import string
import base64
import json
import hmac
import hashlib
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, URLMapping

app = Flask(__name__)

# 配置数据库和 JWT 密钥
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # 请替换为一个安全的密钥

db.init_app(app)

with app.app_context():
    db.create_all()

# 用户模型，用于存储注册用户信息
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

with app.app_context():
    db.create_all()

# 辅助函数：Base64 URL 安全编码（去掉填充字符）
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

# 辅助函数：Base64 URL 解码（补全填充字符）
def base64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

# 手工实现的 JWT 生成函数
def jwt_encode(payload, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    header_b64 = base64url_encode(header_json)
    payload_b64 = base64url_encode(payload_json)
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    token = f"{header_b64}.{payload_b64}.{signature_b64}"
    return token

# 手工实现的 JWT 解码和校验函数
def jwt_decode(token, secret):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_signature = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()
        expected_signature_b64 = base64url_encode(expected_signature)
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
        payload_json = base64url_decode(payload_b64)
        payload = json.loads(payload_json.decode('utf-8'))
        # 检查过期时间
        if 'exp' in payload:
            if int(payload['exp']) < int(datetime.datetime.utcnow().timestamp()):
                return None
        return payload
    except Exception:
        return None

# 装饰器：对修改操作进行 JWT 校验
def jwt_required_for_modify(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header missing'}), 403
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != 'Bearer':
                return jsonify({'error': 'Invalid Authorization header format'}), 403
            token = parts[1]
            payload = jwt_decode(token, app.config['SECRET_KEY'])
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 403
            # 可将认证信息保存到请求上下文中
            request.user = payload.get('username')
        return f(*args, **kwargs)
    return decorated_function

# URL 格式验证函数
def validation(url):
    regex = r'^(https?://)' \
            r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})' \
            r'(:\d+)?' \
            r'(/\S*)?$'
    return re.match(regex, url) is not None

# Base62 编码函数，用于生成短链接
F = 100000
def encode(num):
    char = string.digits + string.ascii_lowercase + string.ascii_uppercase
    base = len(char)
    num += F
    result = []
    while num:
        result.append(char[num % base])
        num //= base
    return ''.join(reversed(result))

# 用户注册接口：POST /users
# 请求 JSON 格式: {"username": "unique_username", "password": "user_password"}
@app.route('/users', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    username = data['username']
    password = data['password']
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'duplicate'}), 409
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created'}), 201

# 用户密码更新接口：PUT /users
# 请求 JSON 格式: {"username": "unique_username", "old-password": "current_password", "new-password": "new_password"}
@app.route('/users', methods=['PUT'])
def update_user():
    data = request.get_json()
    if not data or 'username' not in data or 'old-password' not in data or 'new-password' not in data:
        return jsonify({'error': 'Missing parameters'}), 400
    username = data['username']
    old_password = data['old-password']
    new_password = data['new-password']
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, old_password):
        return jsonify({'error': 'forbidden'}), 403
    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'}), 200

# 用户登录接口：POST /users/login
# 请求 JSON 格式: {"username": "unique_username", "password": "user_password"}
# 登录成功后生成一个手工实现的 JWT，返回 200 和 token；否则返回 403
@app.route('/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'forbidden'}), 403
    exp = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    payload = {'username': username, 'exp': int(exp.timestamp())}
    token = jwt_encode(payload, app.config['SECRET_KEY'])
    return jsonify({'token': token}), 200

# URL 映射相关接口（CRUD），修改操作上需要通过 JWT 校验
@app.route('/', methods=['GET', 'POST', 'DELETE'])
@jwt_required_for_modify
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
        return jsonify({'message': 'All URL mappings deleted'}), 204

    return jsonify({'error': 'Invalid operation'}), 404

@app.route('/<short_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required_for_modify
def handle_short_id(short_id):
    mapping = URLMapping.query.filter_by(shortid=short_id).first()
    if request.method == 'GET':
        if mapping:
            response = jsonify({'value': mapping.long_url})
            response.status_code = 301  # 可根据需要调整重定向逻辑
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