import firebase_admin, pyrebase
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('firebase_conf/firebase_config.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://intop-project-default-rtdb.firebaseio.com/',
    'storageBucket': 'gs://intop-project.appspot.com'
})

# Инициализация pyrebase
firebase_config = {
    "apiKey": "AIzaSyBqHuFSr0muVsePoaxgkBU0_y6HkXdY6OY",
    "authDomain": "intop-project.firebaseapp.com",
    "databaseURL": "https://intop-project-default-rtdb.firebaseio.com",
    "projectId": "intop-project",
    "storageBucket": "intop-project.appspot.com",
    "messagingSenderId": "1056920316512",
    "appId": "1:1056920316512:web:421b3c7b282a2180807105"
}

FIREBASE_API_KEY = "AIzaSyBqHuFSr0muVsePoaxgkBU0_y6HkXdY6OY"

firebase = pyrebase.initialize_app(firebase_config)