import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('firebase/firebase_config.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://intop-project-default-rtdb.firebaseio.com/'
})