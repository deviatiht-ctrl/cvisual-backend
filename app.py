import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

CVISUAL_MAILER_KEY = os.environ.get("CVISUAL_MAILER_KEY", "your_fallback_key_here")

def send_brevo_email(to_email, to_name, subject, html_content):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": CVISUAL_MAILER_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "CVisual Agency", "email": "contact@cvisual.agency"},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 201
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cvisual.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'cvisual-secret-2025' # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)

@app.errorhandler(500)
def handle_500(e):
    return jsonify(error=str(e), message="Internal Server Error"), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify(error=str(e), type=str(type(e))), 500

# Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))
    image = db.Column(db.String(255))
    features = db.Column(db.Text) # Comma separated list

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    main_image = db.Column(db.String(255), nullable=False)
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    live_link = db.Column(db.String(255))
    gallery = db.Column(db.Text) # JSON string or comma separated

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(255))

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='actualite') # actualite, recrutement
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d %b %Y"))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(255))

class Stat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True) # projects, satisfaction, years, etc
    value = db.Column(db.String(50))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    tiktok = db.Column(db.String(100))
    sales_level = db.Column(db.String(50))
    cv_link = db.Column(db.String(255))
    motivation = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending, interview, accepted, rejected
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Auth Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify(msg="Missing JSON in request"), 400
        
    username = data.get('username')
    password = data.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password, password):
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    
    return jsonify(msg="Identifiants invalides"), 401

# Public Data Routes
@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id, 'title': s.title, 'description': s.description, 
        'icon': s.icon, 'image': s.image, 'features': s.features
    } for s in services])

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id, 'title': p.title, 'category': p.category, 
        'main_image': p.main_image, 'challenge': p.challenge,
        'solution': p.solution, 'live_link': p.live_link,
        'gallery': p.gallery.split(',') if p.gallery else []
    } for p in projects])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = Stat.query.all()
    return jsonify({s.key: s.value for s in stats})

@app.route('/api/testimonials', methods=['GET'])
def get_testimonials():
    items = Testimonial.query.all()
    return jsonify([{
        'id': i.id, 'name': i.name, 'company': i.company, 
        'content': i.content, 'avatar': i.avatar
    } for i in items])

@app.route('/api/news', methods=['GET'])
def get_news():
    news = News.query.order_by(News.id.desc()).all()
    return jsonify([{
        'id': n.id, 'title': n.title, 'content': n.content, 
        'type': n.type, 'date': n.date
    } for n in news])

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'logo': c.logo} for c in clients])

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    new_app = Application(
        news_id=data.get('newsId'),
        full_name=data.get('fullName'),
        email=data.get('email'),
        whatsapp=data.get('whatsapp'),
        tiktok=data.get('tiktok'),
        sales_level=data.get('salesLevel'),
        cv_link=data.get('cvLink'),
        motivation=data.get('motivation')
    )
    db.session.add(new_app)
    db.session.commit()

    # Send Notification Email
    email_html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; background-color: #0a0a0a; color: #ffffff; border-radius: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0;">CVISUAL</h1>
            <p style="color: #3b82f6; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px;">Creative Agency</p>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
            <h2 style="font-size: 20px; margin-bottom: 20px;">Candidature Reçue</h2>
            <p>Bonjour <strong>{new_app.full_name}</strong>,</p>
            <p>Merci d'avoir postulé chez <strong>CVisual Agency</strong>. Nous avons bien reçu vos informations.</p>
            <p>Votre dossier est actuellement <strong>en attente de revue</strong> par notre équipe de recrutement.</p>
            <div style="margin: 30px 0; padding: 20px; background: rgba(59,130,246,0.1); border-left: 4px solid #3b82f6; border-radius: 5px;">
                <p style="margin: 0; font-size: 14px;"><strong>Statut :</strong> En attente de revue</p>
            </div>
            <p style="font-size: 14px; color: #94a3b8;">Nous vous contacterons prochainement si votre profil correspond à nos besoins actuels pour une interview.</p>
        </div>
        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #64748b;">
            <p>© 2025 CVisual Agency. Tous droits réservés.</p>
        </div>
    </div>
    """
    send_brevo_email(new_app.email, new_app.full_name, "Confirmation de candidature - CVisual Agency", email_html)

    return jsonify(success=True), 201

# Admin Protected Routes (CRUD)
@app.route('/api/admin/stats', methods=['POST'])
@jwt_required()
def update_stat():
    data = request.json
    for key, value in data.items():
        stat = Stat.query.filter_by(key=key).first()
        if stat:
            stat.value = str(value)
        else:
            db.session.add(Stat(key=key, value=str(value)))
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/admin/news', methods=['POST'])
@jwt_required()
def add_news():
    data = request.json
    item = News(
        title=data.get('title'),
        content=data.get('content'),
        type=data.get('type', 'actualite')
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/admin/news/<int:id>', methods=['DELETE', 'PUT'])
@jwt_required()
def manage_news(id):
    item = News.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify(success=True)
    elif request.method == 'PUT':
        data = request.json
        item.title = data.get('title')
        item.content = data.get('content')
        item.type = data.get('type')
        db.session.commit()
        return jsonify(success=True)

@app.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def get_applications():
    apps = Application.query.order_by(Application.date.desc()).all()
    return jsonify([{
        'id': a.id, 'full_name': a.full_name, 'email': a.email,
        'whatsapp': a.whatsapp, 'tiktok': a.tiktok, 'sales_level': a.sales_level,
        'cv_link': a.cv_link, 'motivation': a.motivation, 'status': a.status,
        'date': a.date.strftime("%d %b %Y"), 'news_id': a.news_id
    } for a in apps])

@app.route('/api/admin/applications/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(id):
    app_item = Application.query.get_or_404(id)
    data = request.json
    app_item.status = data.get('status')
    db.session.commit()
    return jsonify(success=True)

# Initialize Database
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        db.session.add(Admin(username='admin', password=generate_password_hash('admin123')))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
