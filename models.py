"""
models.py
---------
Data-access classes for the four core entities: User, Design, Furniture,
Booking. Each class wraps parameterised SQL against the SQLite database
defined in database/schema.sql, exposing simple staticmethods so the
rest of the app (app.py, agents/, tools/) never writes raw SQL.
"""

import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db


class User:
    @staticmethod
    def create(username, email, password):
        db = get_db()
        password_hash = generate_password_hash(password)
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_email(email):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    @staticmethod
    def find_by_username(username):
        db = get_db()
        return db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    @staticmethod
    def verify_password(user_row, password):
        return check_password_hash(user_row["password_hash"], password)


class Design:
    @staticmethod
    def create(user_id, room_type, style, budget, image_path=None,
               analysis_data=None, design_data=None):
        db = get_db()
        cur = db.execute(
            """INSERT INTO designs
               (user_id, room_type, style, budget, image_path, analysis_data, design_data)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, room_type, style, budget, image_path,
                json.dumps(analysis_data) if analysis_data is not None else None,
                json.dumps(design_data) if design_data is not None else None,
            ),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def update_design_data(design_id, design_data=None, analysis_data=None):
        db = get_db()
        fields, params = [], []
        if design_data is not None:
            fields.append("design_data = ?")
            params.append(json.dumps(design_data))
        if analysis_data is not None:
            fields.append("analysis_data = ?")
            params.append(json.dumps(analysis_data))
        fields.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(design_id)
        db.execute(f"UPDATE designs SET {', '.join(fields)} WHERE id = ?", params)
        db.commit()

    @staticmethod
    def find_by_id(design_id):
        db = get_db()
        return db.execute("SELECT * FROM designs WHERE id = ?", (design_id,)).fetchone()

    @staticmethod
    def find_by_user(user_id, style=None, room_type=None, order_by="newest"):
        db = get_db()
        query = "SELECT * FROM designs WHERE user_id = ?"
        params = [user_id]
        if style and style != "all":
            query += " AND style = ?"
            params.append(style)
        if room_type and room_type != "all":
            query += " AND room_type = ?"
            params.append(room_type)
        query += " ORDER BY created_at " + ("DESC" if order_by == "newest" else "ASC")
        return db.execute(query, params).fetchall()

    @staticmethod
    def delete(design_id, user_id):
        db = get_db()
        db.execute(
            "DELETE FROM designs WHERE id = ? AND user_id = ?", (design_id, user_id)
        )
        db.commit()


class Furniture:
    @staticmethod
    def bulk_create(design_id, items):
        """items: list of dicts with name, category, quantity, price_min,
        price_max, priority, image_url"""
        db = get_db()
        db.executemany(
            """INSERT INTO furniture
               (design_id, name, category, quantity, price_min, price_max, priority, image_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    design_id, i.get("name"), i.get("category"),
                    i.get("quantity", 1), i.get("price_min"), i.get("price_max"),
                    i.get("priority", "medium"), i.get("image_url"),
                )
                for i in items
            ],
        )
        db.commit()

    @staticmethod
    def find_by_design(design_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM furniture WHERE design_id = ?", (design_id,)
        ).fetchall()


class Booking:
    @staticmethod
    def create(design_id, furniture_name, language="en", status="pending"):
        db = get_db()
        cur = db.execute(
            """INSERT INTO bookings (design_id, furniture_name, status, language)
               VALUES (?, ?, ?, ?)""",
            (design_id, furniture_name, status, language),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def find_by_design(design_id):
        db = get_db()
        return db.execute(
            "SELECT * FROM bookings WHERE design_id = ? ORDER BY booking_date DESC",
            (design_id,),
        ).fetchall()

    @staticmethod
    def update_status(booking_id, status):
        db = get_db()
        db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        db.commit()
