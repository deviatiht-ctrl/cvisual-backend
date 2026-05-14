import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cvisual.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'cvisual-secret-2025'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
jwt = JWTManager(app)

CVISUAL_MAILER_KEY = os.environ.get("CVISUAL_MAILER_KEY", "your_fallback_key_here")

# --- Models ---

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    image = db.Column(db.String(255))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    main_image = db.Column(db.String(255))
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    live_link = db.Column(db.String(255))

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='actualite')
    image = db.Column(db.String(255))
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d %b %Y"))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(255))

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class RecruitmentQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default='text')
    options = db.Column(db.Text)
    required = db.Column(db.Boolean, default=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    tiktok = db.Column(db.String(100))
    sales_level = db.Column(db.String(50))
    cv_filename = db.Column(db.String(255))
    cv_link = db.Column(db.String(255))
    motivation = db.Column(db.Text)
    answers = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Routes ---

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    admin = Admin.query.filter_by(username=data.get('username')).first()
    if admin and check_password_hash(admin.password, data.get('password')):
        return jsonify(access_token=create_access_token(identity=admin.username)), 200
    return jsonify(msg="Invalide"), 401

# Public Data
@app.route('/api/services', methods=['GET'])
def get_services():
    items = Service.query.all()
    return jsonify([{'id':i.id, 'title':i.title, 'description':i.description, 'icon':i.icon, 'image':i.image} for i in items])

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    items = Project.query.all()
    return jsonify([{'id':i.id, 'title':i.title, 'category':i.category, 'main_image':i.main_image} for i in items])

@app.route('/api/news', methods=['GET'])
def get_news():
    items = News.query.order_by(News.id.desc()).all()
    return jsonify([{'id':i.id, 'title':i.title, 'content':i.content, 'type':i.type, 'image':i.image, 'date':i.date} for i in items])

@app.route('/api/clients', methods=['GET'])
def get_clients():
    items = Client.query.all()
    return jsonify([{'id':i.id, 'name':i.name, 'logo':i.logo} for i in items])

@app.route('/api/recruitment/questions', methods=['GET'])
def get_questions():
    qs = RecruitmentQuestion.query.all()
    return jsonify([{'id': q.id, 'question': q.question, 'type': q.type, 'options': q.options, 'required': q.required} for q in qs])

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    new_app = Application(full_name=data.get('fullName'), email=data.get('email'), whatsapp=data.get('whatsapp'), tiktok=data.get('tiktok'), cv_filename=data.get('cvFilename'), motivation=data.get('motivation'))
    db.session.add(new_app)
    db.session.commit()
    return jsonify(success=True)

# Admin CRUD
@app.route('/api/admin/upload', methods=['POST'])
@jwt_required()
def upload():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        name = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
        return jsonify(success=True, url=f"/api/uploads/{name}")
    return jsonify(error="Error"), 400

@app.route('/api/admin/services', methods=['POST'])
@app.route('/api/admin/services/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_services(id=None):
    if request.method == 'POST':
        d = request.json
        s = Service(title=d['title'], description=d.get('description'), icon=d.get('icon'), image=d.get('image'))
        db.session.add(s); db.session.commit(); return jsonify(success=True)
    item = Service.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']; item.description = d.get('description'); item.icon = d.get('icon'); item.image = d.get('image')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/portfolio', methods=['POST'])
@app.route('/api/admin/portfolio/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_portfolio(id=None):
    if request.method == 'POST':
        d = request.json
        p = Project(title=d['title'], category=d['category'], main_image=d.get('main_image'), challenge=d.get('challenge'))
        db.session.add(p); db.session.commit(); return jsonify(success=True)
    item = Project.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']; item.category = d['category']; item.main_image = d.get('main_image'); item.challenge = d.get('challenge')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/news', methods=['POST'])
@app.route('/api/admin/news/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_news(id=None):
    if request.method == 'POST':
        d = request.json
        n = News(title=d['title'], content=d['content'], type=d.get('type'), image=d.get('image'))
        db.session.add(n); db.session.commit(); return jsonify(success=True)
    item = News.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']; item.content = d['content']; item.type = d.get('type'); item.image = d.get('image')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/clients', methods=['POST'])
@app.route('/api/admin/clients/<int:id>', methods=['DELETE'])
@jwt_required()
def admin_clients(id=None):
    if request.method == 'POST':
        d = request.json
        db.session.add(Client(name=d['name'], logo=d.get('logo'))); db.session.commit(); return jsonify(success=True)
    item = Client.query.get_or_404(id)
    db.session.delete(item); db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def admin_apps():
    items = Application.query.order_by(Application.date.desc()).all()
    return jsonify([{'id':a.id, 'full_name':a.full_name, 'email':a.email, 'status':a.status, 'date':a.date.strftime("%d %b %Y"), 'cv_filename':a.cv_filename} for a in items])

@app.route('/api/admin/applications/<int:id>/status', methods=['PUT'])
@jwt_required()
def admin_app_status(id):
    item = Application.query.get_or_404(id)
    item.status = request.json.get('status')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/recruitment/questions', methods=['POST'])
@app.route('/api/admin/recruitment/questions/<int:id>', methods=['DELETE'])
@jwt_required()
def admin_questions(id=None):
    if request.method == 'POST':
        d = request.json
        db.session.add(RecruitmentQuestion(question=d['question'], type=d.get('type'), options=d.get('options'))); db.session.commit(); return jsonify(success=True)
    item = RecruitmentQuestion.query.get_or_404(id)
    db.session.delete(item); db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/newsletter', methods=['GET'])
@jwt_required()
def admin_newsletter():
    items = Newsletter.query.all()
    return jsonify([{'id':i.id, 'email':i.email, 'date':i.date.strftime("%d %b %Y")} for i in items])

# Init
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        db.session.add(Admin(username='admin', password=generate_password_hash('admin123')))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
