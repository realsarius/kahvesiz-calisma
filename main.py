import os
import itsdangerous

from datetime import datetime, timezone
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CafeForm, ContactForm, UserForm

load_dotenv()


def get_env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def get_env_int(name, default):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///cafes.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = get_env_int('MAIL_PORT', 587)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = get_env_bool('MAIL_USE_TLS', True)
app.config['MAIL_USE_SSL'] = get_env_bool('MAIL_USE_SSL', False)
app.config['WTF_CSRF_ENABLED'] = get_env_bool('WTF_CSRF_ENABLED', True)
app.config['WTF_CSRF_TIME_LIMIT'] = get_env_int('WTF_CSRF_TIME_LIMIT', 3600)
app.config['TINYMCE_API_KEY'] = os.getenv('TINYMCE_API_KEY', '')
app.config['CAFES_PER_PAGE'] = get_env_int('CAFES_PER_PAGE', 20)
app.config['COFFEE_CURRENCY_SYMBOL'] = os.getenv('COFFEE_CURRENCY_SYMBOL', '£')
app.config['AUTO_CREATE_SCHEMA'] = get_env_bool('AUTO_CREATE_SCHEMA', False)

mail = Mail(app=app)
csrf = CSRFProtect(app)
s = itsdangerous.URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf}


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'CSRF token missing or invalid.'}), 400
    flash('CSRF doğrulaması başarısız. Lütfen tekrar deneyin.', 'danger')
    return redirect(request.referrer or url_for('home'))


def generate_verification_token(email):
    return s.dumps(email, salt='email-confirm')


def verify_verification_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='email-confirm', max_age=expiration)
    except itsdangerous.SignatureExpired:
        return None
    except itsdangerous.BadSignature:
        return None
    return email


def send_confirmation_email(user_email):
    token = generate_verification_token(user_email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    msg = Message('Please confirm your email', sender=app.config['MAIL_USERNAME'], recipients=[user_email])
    msg.body = f'Your link is {confirm_url}'
    with app.app_context():
        mail.send(msg)


# from flask_ckeditor import CKEditor

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base, metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate(app, db, render_as_batch=True)
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    moderated_cafes = db.relationship('Cafe', secondary='user_cafe', back_populates='moderators')

    def __repr__(self):
        return f"<User {self.name}>"

    @property
    def is_admin_status(self):
        return self.is_admin  # Use property to avoid conflict

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

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc),
                           nullable=False)

    moderators = db.relationship('User', secondary='user_cafe', back_populates='moderated_cafes')

    def __repr__(self):
        return f"<Cafe {self.name}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)

    return decorated_function


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required.'}), 401
        return f(*args, **kwargs)

    return decorated_function


def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required.'}), 401
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)

    return decorated_function


def user_can_edit_cafe(user, cafe):
    return user.is_authenticated and (user.is_admin or user.is_moderator_of(cafe.id))


def normalize_coffee_price(raw_price):
    symbol = app.config['COFFEE_CURRENCY_SYMBOL']
    value = str(raw_price or '').strip()
    if not value:
        return value
    if value.startswith(symbol):
        return value
    return f'{symbol}{value}'


def serialize_cafe(cafe):
    return {
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


def parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Çıkış yaptınız.', 'info')
    return redirect(url_for('home'))


if app.config['AUTO_CREATE_SCHEMA']:
    with app.app_context():
        db.create_all()


# def sanitize_html(html_content):
#     allowed_tags = bleach.sanitizer.ALLOWED_TAGS + ['i', 'b', 'u']
#     return bleach.clean(html_content, tags=allowed_tags, strip=True)

def assign_moderator(user_id, cafe_id):
    user = db.session.get(User, int(user_id))
    cafe = db.session.get(Cafe, int(cafe_id))

    if not user or not cafe:
        raise ValueError("User or Cafe not found")

    if cafe not in user.moderated_cafes:
        user.moderated_cafes.append(cafe)
        db.session.commit()


@app.route('/admin/assign_moderator', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_moderator_page():
    if not current_user.is_admin:
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

    users = User.query.all()
    cafes = Cafe.query.all()
    return render_template('admin_dashboard.html', users=users, cafes=cafes)


@app.route('/remove_moderator/<int:user_id>/<int:cafe_id>', methods=['DELETE'])
@login_required
@admin_required
def remove_moderator(user_id, cafe_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    cafe = db.session.get(Cafe, cafe_id)
    if not cafe:
        return jsonify({'success': False, 'message': 'Cafe not found'}), 404

    if cafe in user.moderated_cafes:
        user.moderated_cafes.remove(cafe)
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'message': 'Cafe is not moderated by this user'}), 400


@app.route('/moderated_cafes/<int:user_id>', methods=['GET'])
@login_required
def get_moderated_cafes(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'You do not have permission to access this data.'}), 403

    user = User.query.get_or_404(user_id)
    cafes = user.moderated_cafes
    cafes_list = [{'id': cafe.id, 'name': cafe.name} for cafe in cafes]
    return jsonify(cafes=cafes_list)


@app.route('/cafes/update/<int:cafe_id>', methods=['GET', 'POST'])
@login_required
def update_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    tinymce_api_key = app.config['TINYMCE_API_KEY']

    if not cafe:
        return redirect(url_for('cafes'))
    if not user_can_edit_cafe(current_user, cafe):
        flash('Bu kafe için düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('cafe_detail', cafe_id=cafe.id))

    form = CafeForm(obj=cafe)

    if form.validate_on_submit():
        form.populate_obj(cafe)
        cafe.coffee_price = normalize_coffee_price(form.coffee_price.data)
        try:
            db.session.commit()
            flash('Cafe updated successfully!', 'success')
            return redirect(url_for('cafes'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')

    return render_template('update_cafe.html', form=form, cafe=cafe, tinymce_api_key=tinymce_api_key)


@app.route('/api/cafes/<int:cafe_id>', methods=['PUT'])
@app.route('/api/update_cafe/<int:cafe_id>', methods=['PUT'])
@api_login_required
def api_update_cafe(cafe_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    required_fields = ['name', 'map_url', 'img_url', 'location', 'has_sockets', 'has_toilet', 'has_wifi',
                       'can_take_calls', 'seats', 'coffee_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    cafe = db.session.get(Cafe, cafe_id)
    if not cafe:
        return jsonify({'error': 'Cafe not found'}), 404
    if not user_can_edit_cafe(current_user, cafe):
        return jsonify({'error': 'You do not have permission to update this cafe.'}), 403

    if Cafe.query.filter(Cafe.name == data['name'], Cafe.id != cafe_id).first():
        return jsonify({'error': 'A cafe with this name already exists. Please choose a different name.'}), 409

    cafe.name = data['name']
    cafe.map_url = data['map_url']
    cafe.img_url = data['img_url']
    cafe.location = data['location']
    cafe.has_sockets = data['has_sockets']
    cafe.has_toilet = data['has_toilet']
    cafe.has_wifi = data['has_wifi']
    cafe.can_take_calls = data['can_take_calls']
    cafe.seats = data['seats']
    cafe.coffee_price = normalize_coffee_price(data['coffee_price'])
    cafe.details = data.get('details')

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
    tinymce_api_key = app.config['TINYMCE_API_KEY']

    if form.validate_on_submit():
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
            coffee_price=normalize_coffee_price(coffee_price),
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
    elif request.method == 'POST':
        flash('Form doğrulaması başarısız. Lütfen alanları kontrol edin.', 'error')

    return render_template('add_cafe.html', form=form, tinymce_api_key=tinymce_api_key)


@app.route('/api/cafes/<int:cafe_id>', methods=['DELETE'])
@app.route('/api/delete_cafe/<int:cafe_id>', methods=['DELETE'])
@api_admin_required
def api_delete_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)

    if not cafe:
        return jsonify({'error': 'Cafe not found'}), 404

    try:
        db.session.delete(cafe)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Cafe deleted successfully!'}), 200


@app.route('/api/cafes', methods=['POST'])
@app.route('/api/add_cafe', methods=['POST'])
@api_admin_required
def api_add_cafe():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    required_fields = ['name', 'map_url', 'img_url', 'location', 'has_sockets', 'has_toilet', 'has_wifi',
                       'can_take_calls', 'seats', 'coffee_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    existing_cafe = Cafe.query.filter_by(name=data['name']).first()
    if existing_cafe:
        return jsonify({'error': 'A cafe with this name already exists. Please choose a different name.'}), 409

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
        coffee_price=normalize_coffee_price(data['coffee_price']),
        details=data.get('details')
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
    cafe = db.session.get(Cafe, id)
    if not cafe:
        return make_response(jsonify({'error': 'Cafe not found'}), 404)
    return make_response(jsonify(serialize_cafe(cafe)), 200)


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

        cafes_list = [serialize_cafe(cafe) for cafe in cafes]
        return make_response(jsonify({'cafes': cafes_list}), 200)
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return make_response(jsonify({'error': 'An error occurred while retrieving cafes'}), 500)


@app.route('/cafes', methods=['GET'])
def cafes():
    try:
        page = parse_positive_int(request.args.get('page', 1), 1)
        per_page = app.config['CAFES_PER_PAGE']
        pagination = Cafe.query.order_by(Cafe.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return render_template(
            'cafes.html',
            cafes=pagination.items,
            total_pages=pagination.pages,
            current_page=page
        )
    except Exception as e:
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
    cafe = db.session.get(Cafe, cafe_id)
    if not cafe:
        return render_template('cafe_detail.html', cafe=None, error="Cafe not found.")
    return render_template('cafe_detail.html', cafe=cafe)


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email:
        return jsonify({'error': 'E-posta adresi gerekli.'}), 422
    if not password:
        return jsonify({'error': 'Şifre gerekli.'}), 422

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Geçersiz e-posta adresi veya şifre.'}), 401
    if not user.is_confirmed:
        return jsonify({'error': 'Hesabınızı doğrulamanız gerekiyor.'}), 403

    login_user(user)
    return jsonify({'message': 'Giriş başarılı!'}), 200


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

        if not form.email.errors and not form.password.errors:
            user = User.query.filter_by(email=email).first()

            if user:
                if check_password_hash(user.password, password):
                    if user.is_confirmed:
                        login_user(user)
                        flash('Giriş başarılı! Ana sayfaya yönlendiriliyorsunuz.', 'success')
                        return redirect(url_for('home'))
                    else:
                        flash('E-posta adresinizi doğrulamanız gerekiyor. Lütfen e-posta adresinizi kontrol edin.',
                              'warning')
                else:
                    flash('Geçersiz şifre.', 'danger')
            else:
                flash('Geçersiz e-posta adresi.', 'danger')

    return render_template('login.html', form=form)


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        return jsonify({'error': 'İsim gerekli.'}), 422
    if not email:
        return jsonify({'error': 'E-posta adresi gerekli.'}), 422
    if not password:
        return jsonify({'error': 'Şifre gerekli.'}), 422
    if len(password) < 8:
        return jsonify({'error': 'Şifre en az 8 karakter olmalı.'}), 422

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'E-posta adresi zaten kullanımda.'}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(name=name, email=email, password=hashed_password, is_admin=False, is_confirmed=False)

    db.session.add(new_user)
    db.session.commit()

    send_confirmation_email(email)  # Send the verification email

    return jsonify({'message': 'Hesabınız başarıyla oluşturuldu! Lütfen e-posta adresinizi doğrulayın.'}), 201


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
        new_user = User(name=name, email=email, password=hashed_password, is_admin=False, is_confirmed=False)
        db.session.add(new_user)
        db.session.commit()

        send_confirmation_email(email)  # Send the confirmation email

        flash('Hesabınız başarıyla oluşturuldu! Lütfen e-posta adresinizi doğrulayın.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
    email = verify_verification_token(token)
    if email is None:
        flash('Onaylama bağlantısı geçersiz veya süresi dolmuş.', 'danger')
        return redirect(url_for('signup'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_confirmed:
        flash('Hesap zaten onaylanmış. Lütfen giriş yapın.', 'success')
    else:
        user.is_confirmed = True
        user.confirmed_on = datetime.now(timezone.utc)
        db.session.commit()
        flash('Hesabınız onaylandı! Şimdi giriş yapabilirsiniz.', 'success')

    return redirect(url_for('login'))


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

        users_list = [
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            }
            for user in users
        ]
        return make_response(jsonify({'users': users_list}), 200)
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
    app.run(debug=False)
