import smtplib, random, string, redis
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException

def send_email(to_email, subject, message):
    # Функция для отправки кода подтверждения на почту
    smtp_server = "smtp.elasticemail.com"
    smtp_port = 2525
    smtp_username = "nj.dark.soul@gmail.com"
    smtp_password = "29AB5D5E9045B48BE03F8377BB0399B61619"

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    text = msg.as_string()
    server.sendmail(smtp_username, to_email, text)
    server.quit()

def generate_verification_code():
    # Генерация кода верификации
    return ''.join(random.choices(string.digits, k=6))

# Функция для хранения кода подтверждения смс кода
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_verification_code(email, code):
    # Удаление старого кода, если он существует
    redis_client.delete(email)
    # Сохранение нового кода на 5 минут
    redis_client.setex(email, 300, code)  # 300 секунд = 5 минут

def get_verification_code(email):
    return redis_client.get(email)

async def send_sms_to_email(request):
    
    # Генерация кода подтверждения
    verification_code = generate_verification_code()

    # Отправка email с кодом подтверждения
    subject = "Код подтверждения для Intop"
    message = f"Ваш код подтверждения: {verification_code}"
    send_email(request.email, subject, message)

    # Сохранение кода подтверждения в Redis на 5 минут
    store_verification_code(request.email, verification_code)

    return {"message": "Код подтверждения отправлен на вашу электронную почту."}