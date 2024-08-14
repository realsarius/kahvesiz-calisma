import requests
from functools import wraps
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, String, select, UniqueConstraint, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, URL
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CafeForm, ContactForm, UserForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os

# from flask_ckeditor import CKEditor

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

user_cafe = db.Table('user_cafe',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('cafe_id', db.Integer, db.ForeignKey('cafe.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    moderated_cafes = db.relationship('Cafe', secondary='user_cafe', back_populates='moderators')

    def __repr__(self):
        return f"<User {self.name}>"
    
    def is_admin(self):
        return self.id == 1

    def is_moderator_of(self, cafe_id):
        return any(cafe.id == cafe_id for cafe in self.moderated_cafes)

    def get_default_cafe_id(self):
        if self.moderated_cafes:
            return self.moderated_cafes[0].id
        return None


class Cafe(db.Model):
    __tablename__ = 'cafe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    map_url = db.Column(db.String(255), unique=True, nullable=False)
    img_url = db.Column(db.String(255), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    has_sockets = db.Column(db.Boolean, default=False)
    has_toilet = db.Column(db.Boolean, default=False)
    has_wifi = db.Column(db.Boolean, default=False)
    can_take_calls = db.Column(db.Boolean, default=False)
    seats = db.Column(db.String(100), nullable=False)
    coffee_price = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)

    moderators = db.relationship('User', secondary='user_cafe', back_populates='moderated_cafes')

    def __repr__(self):
        return f"<Cafe {self.name}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Çıkış yaptınız.', 'info')
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

# def sanitize_html(html_content):
#     allowed_tags = bleach.sanitizer.ALLOWED_TAGS + ['i', 'b', 'u']
#     return bleach.clean(html_content, tags=allowed_tags, strip=True)

def assign_moderator(user_id, cafe_id):
    user = User.query.get(user_id)
    cafe = Cafe.query.get(cafe_id)
    
    if not user or not cafe:
        raise ValueError("User or Cafe not found")

    if cafe not in user.moderated_cafes:
        user.moderated_cafes.append(cafe)
        db.session.commit()

    if user not in cafe.moderators:
        cafe.moderators.append(user)
        db.session.commit()

@app.route('/admin/assign_moderator', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_moderator_page():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        cafe_id = request.form.get('cafe_id')
        
        try:
            assign_moderator(user_id, cafe_id)
            flash('Moderator assigned successfully!', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
        return redirect(url_for('assign_moderator_page'))

    users = User.query.all()
    cafes = Cafe.query.all()
    return render_template('assign_moderator.html', users=users, cafes=cafes)

@app.route('/cafes/update/<int:cafe_id>', methods=['GET', 'POST'])
@login_required
def update_cafe(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    tinymce_api_key = os.getenv('TINYMCE_API_KEY')
    
    if not cafe:
        return redirect(url_for('cafes'))

    form = CafeForm(obj=cafe)

    if form.validate_on_submit():
        form.populate_obj(cafe)
        try:
            db.session.commit()
            flash('Cafe updated successfully!', 'success')
            return redirect(url_for('cafes'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')

    return render_template('update_cafe.html', form=form, cafe=cafe, tinymce_api_key=tinymce_api_key)

@app.route('/api/update_cafe/<int:cafe_id>', methods=['PUT'])
def api_update_cafe(cafe_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    required_fields = ['name', 'map_url', 'img_url', 'location', 'has_sockets', 'has_toilet', 'has_wifi', 'can_take_calls', 'seats', 'coffee_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return jsonify({'error': 'Cafe not found'}), 404

    if Cafe.query.filter(Cafe.name == data['name'], Cafe.id != cafe_id).first():
        return jsonify({'error': 'A cafe with this name already exists. Please choose a different name.'}), 400

    cafe.name = data['name']
    cafe.map_url = data['map_url']
    cafe.img_url = data['img_url']
    cafe.location = data['location']
    cafe.has_sockets = data['has_sockets']
    cafe.has_toilet = data['has_toilet']
    cafe.has_wifi = data['has_wifi']
    cafe.can_take_calls = data['can_take_calls']
    cafe.seats = data['seats']
    cafe.coffee_price = data['coffee_price']
    cafe.details = data['details']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Cafe updated successfully!'}), 200

@app.route('/add_cafe', methods=['GET', 'POST'])
@login_required
@admin_required
def add_cafe():
    form = CafeForm()
    tinymce_api_key = os.getenv('TINYMCE_API_KEY')

    if request.method == 'POST':
        name = form.name.data
        map_url = form.map_url.data
        img_url = form.img_url.data
        location = form.location.data
        has_sockets = form.has_sockets.data
        has_toilet = form.has_toilet.data
        has_wifi = form.has_wifi.data
        can_take_calls = form.can_take_calls.data
        seats = form.seats.data
        coffee_price = form.coffee_price.data
        details = form.details.data

        new_cafe = Cafe(
            name=name,
            map_url=map_url,
            img_url=img_url,
            location=location,
            has_sockets=has_sockets,
            has_toilet=has_toilet,
            has_wifi=has_wifi,
            can_take_calls=can_take_calls,
            seats=seats,
            coffee_price="£" + coffee_price,
            details=details
        )

        try:
            db.session.add(new_cafe)
            db.session.commit()
            flash('Cafe added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the cafe: {e}', 'error')
            print(f'Error: {e}')
    
    return render_template('add_cafe.html', form=form, tinymce_api_key=tinymce_api_key)

@app.route('/api/delete_cafe/<int:cafe_id>', methods=['DELETE'])
def api_delete_cafe(cafe_id):
    cafe = Cafe.query.get(cafe_id)

    if not cafe:
        return jsonify({'error': 'Cafe not found'}), 404

    try:
        db.session.delete(cafe)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Cafe deleted successfully!'}), 200

@app.route('/api/add_cafe', methods=['POST'])
def api_add_cafe():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    required_fields = ['name', 'map_url', 'img_url', 'location', 'has_sockets', 'has_toilet', 'has_wifi', 'can_take_calls', 'seats', 'coffee_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    existing_cafe = Cafe.query.filter_by(name=data['name']).first()
    if existing_cafe:
        return jsonify({'error': 'A cafe with this name already exists. Please choose a different name.'}), 400

    new_cafe = Cafe(
        name=data['name'],
        map_url=data['map_url'],
        img_url=data['img_url'],
        location=data['location'],
        has_sockets=data['has_sockets'],
        has_toilet=data['has_toilet'],
        has_wifi=data['has_wifi'],
        can_take_calls=data['can_take_calls'],
        seats=data['seats'],
        coffee_price="£" + data['coffee_price'],
        details=data['details']
    )

    try:
        db.session.add(new_cafe)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Cafe added successfully!'}), 201


@app.route('/api/cafes/<int:id>', methods=['GET'])
def get_cafe(id):
    try:
        cafe = Cafe.query.get_or_404(id)
        cafe_data = {
            'id': cafe.id,
            'name': cafe.name,
            'map_url': cafe.map_url,
            'img_url': cafe.img_url,
            'location': cafe.location,
            'has_sockets': cafe.has_sockets,
            'has_toilet': cafe.has_toilet,
            'has_wifi': cafe.has_wifi,
            'can_take_calls': cafe.can_take_calls,
            'seats': cafe.seats,
            'coffee_price': cafe.coffee_price,
            'details': cafe.details
        }
        return make_response(jsonify(cafe_data), 200)
    except Exception as e:
        print(f"An error occurred: {e}")
        return make_response(jsonify({'error': 'An error occurred while retrieving the cafe'}), 500)
    

@app.route('/api/cafes', methods=['GET'])
def get_all_cafes():
    search_query = request.args.get('search', '').strip()
    
    try:
        if search_query:
            cafes = Cafe.query.filter(
                (Cafe.name.ilike(f'%{search_query}%')) |
                (Cafe.location.ilike(f'%{search_query}%'))
            ).all()
        else:
            cafes = Cafe.query.all()

        if cafes:
            cafes_list = [
                {
                    'id': cafe.id,
                    'name': cafe.name,
                    'map_url': cafe.map_url,
                    'img_url': cafe.img_url,
                    'location': cafe.location,
                    'has_sockets': cafe.has_sockets,
                    'has_toilet': cafe.has_toilet,
                    'has_wifi': cafe.has_wifi,
                    'can_take_calls': cafe.can_take_calls,
                    'seats': cafe.seats,
                    'coffee_price': cafe.coffee_price,
                    'details': cafe.details
                }
                for cafe in cafes
            ]
            return make_response(jsonify({'cafes': cafes_list}), 200)
        else:
            return make_response(jsonify({'error': 'No cafes found'}), 404)
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return make_response(jsonify({'error': 'An error occurred while retrieving cafes'}), 500)


        
@app.route('/cafes', methods=['GET'])
def cafes():
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        response = requests.get('http://localhost:5000/api/cafes')
        if response.status_code == 200:
            cafes_data = response.json().get('cafes', [])
            start = (page - 1) * per_page
            end = start + per_page
            paginated_cafes = cafes_data[start:end]
            total_pages = (len(cafes_data) + per_page - 1) // per_page
            return render_template('cafes.html', cafes=paginated_cafes, total_pages=total_pages, current_page=page)
        else:
            return render_template('cafes.html', cafes=[], error="No cafes found.")
    except requests.RequestException as e:
        app.logger.error(f"An error occurred: {e}")
        return render_template('cafes.html', cafes=[], error="An error occurred while retrieving cafes.")


@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    form = ContactForm()
    if form.validate_on_submit():
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact_us'))
    
    return render_template('contact_us.html', form=form)

@app.route('/cafes/<int:cafe_id>')
def cafe_detail(cafe_id):
    try:
        response = requests.get(f'http://localhost:5000/api/cafes/{cafe_id}')
        if response.status_code == 200:
            cafe_data = response.json()
            return render_template('cafe_detail.html', cafe=cafe_data)
        else:
            return render_template('cafe_detail.html', error="Cafe not found.")
    except requests.RequestException as e:
        app.logger.error(f"An error occurred: {e}")
        return render_template('cafe_detail.html', error="An error occurred while retrieving the cafe.")

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name:
        return jsonify({'error': 'İsim gerekli.'}), 400
    if not email:
        return jsonify({'error': 'E-posta adresi gerekli.'}), 400
    if not password:
        return jsonify({'error': 'Şifre gerekli.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Şifre en az 8 karakter olmalı.'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'E-posta adresi zaten kullanımda.'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Hesabınız başarıyla oluşturuldu!'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email:
        return jsonify({'error': 'E-posta adresi gerekli.'}), 400
    if not password:
        return jsonify({'error': 'Şifre gerekli.'}), 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'message': 'Giriş başarılı!'}), 200
    else:
        return jsonify({'error': 'Geçersiz e-posta adresi veya şifre.'}), 400
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = UserForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        if not email:
            form.email.errors.append('E-posta adresi gerekli.')
        if not password:
            form.password.errors.append('Şifre gerekli.')

        # Proceed if no errors
        if not form.email.errors and not form.password.errors:
            # Check if the user exists
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                # Log the user in
                login_user(user)
                flash('Giriş başarılı! Ana sayfaya yönlendiriliyorsunuz.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Geçersiz e-posta adresi veya şifre.', 'danger')

    return render_template('login.html', form=form)
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = UserForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        if User.query.filter_by(email=email).first():
            flash('Email kullanılmakta.', 'danger')
            return redirect(url_for('signup'))

        if len(password) < 8:
            flash('Şifre en az 8 karakter olmalı.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Hesabınız başarıyla oluşturuldu! Artık giriş yapabilirsiniz.', 'success')

    return render_template('signup.html', form=form)

@app.route('/api/users', methods=['GET'])
def get_all_users():
    search_query = request.args.get('search', '').strip()
    
    try:
        if search_query:
            users = User.query.filter(
                (User.name.ilike(f'%{search_query}%')) |
                (User.email.ilike(f'%{search_query}%'))
            ).all()
        else:
            users = User.query.all()

        if users:
            users_list = [
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                }
                for user in users
            ]
            return make_response(jsonify({'users': users_list}), 200)
        else:
            return make_response(jsonify({'error': 'No users found'}), 404)
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return make_response(jsonify({'error': 'An error occurred while retrieving users'}), 500)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/license")
def license():
    return render_template("license.html")

@app.route("/index")
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

if __name__ == "__main__":
    
    app.run(debug=True)