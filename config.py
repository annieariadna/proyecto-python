
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cambia_esto_por_una_clave_segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///lost_and_found.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
