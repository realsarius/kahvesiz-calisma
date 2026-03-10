from kahvesiz_app.extensions import db
from kahvesiz_app.models import Cafe, User


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def list_all(search_query=""):
        if search_query:
            return User.query.filter(
                (User.name.ilike(f"%{search_query}%"))
                | (User.email.ilike(f"%{search_query}%"))
            ).all()
        return User.query.all()

    @staticmethod
    def add(user):
        db.session.add(user)
        db.session.commit()
        return user


class CafeRepository:
    @staticmethod
    def get_by_id(cafe_id):
        return db.session.get(Cafe, cafe_id)

    @staticmethod
    def get_by_name(name):
        return Cafe.query.filter_by(name=name).first()

    @staticmethod
    def exists_by_name_except_id(name, cafe_id):
        return Cafe.query.filter(Cafe.name == name, Cafe.id != cafe_id).first() is not None

    @staticmethod
    def list_all(search_query=""):
        if search_query:
            return Cafe.query.filter(
                (Cafe.name.ilike(f"%{search_query}%"))
                | (Cafe.location.ilike(f"%{search_query}%"))
            ).all()
        return Cafe.query.all()

    @staticmethod
    def paginate(page, per_page):
        return Cafe.query.order_by(Cafe.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def add(cafe):
        db.session.add(cafe)
        db.session.commit()
        return cafe

    @staticmethod
    def delete(cafe):
        db.session.delete(cafe)
        db.session.commit()


class ModeratorRepository:
    @staticmethod
    def assign(user, cafe):
        if cafe not in user.moderated_cafes:
            user.moderated_cafes.append(cafe)
            db.session.commit()

    @staticmethod
    def remove(user, cafe):
        if cafe in user.moderated_cafes:
            user.moderated_cafes.remove(cafe)
            db.session.commit()
            return True
        return False

