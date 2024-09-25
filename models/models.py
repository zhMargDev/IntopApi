from sqlalchemy.orm import declarative_base, relationship

# Импорт таблиц из models.tables
from models.tables import *

# Создание базового класса с использованием декларативной базы
Base = declarative_base()

# Определение класса Role, связанного с таблицей 'roles'
class Role(Base):
    __table__ = roles_table

    id = roles_table.c.id
    name = roles_table.c.name
    permission = roles_table.c.permission

    # Связь с пользователями
    users = relationship('User', back_populates='role')

# Определение класса Region, связанного с таблицей 'regions'
class Region(Base):
    __table__ = regions_table

    id = regions_table.c.id
    name = regions_table.c.name
    parent_id = regions_table.c.parent_id

    # Связь с дочерними регионами
    parent = relationship('Region', remote_side=[id], backref='children')
    # Связь с пользователями
    users = relationship('User', back_populates='region')

# Определение класса User, связанного с таблицей 'users'
class User(Base):
    __table__ = users_table

    id = users_table.c.id
    telegram_id = users_table.c.telegram_id
    role_id = users_table.c.role_id
    password = users_table.c.password
    username = users_table.c.username
    first_name = users_table.c.first_name
    second_name = users_table.c.second_name
    phone_number = users_table.c.phone_number
    email = users_table.c.email
    avatar = users_table.c.avatar
    rating = users_table.c.rating
    region_id = users_table.c.region_id
    is_verified = users_table.c.is_verified
    is_active = users_table.c.is_active
    last_active = users_table.c.last_active

    # Связь с ролью
    role = relationship('Role', back_populates='users')
    # Связь с регионом
    region = relationship('Region', back_populates='users')
    # Связь с моделю менеджеров
    store_managers = relationship("StoreManager", back_populates="user")
    # Связь с магазином
    my_stores = relationship("Store", back_populates="owner")

# Определение класса Rating, связанного с таблицей 'ratings'
class Rating(Base):
    __table__ = ratings_table

    id = ratings_table.c.id
    rater_id = ratings_table.c.rater_id
    rated_id = ratings_table.c.rated_id
    rating = ratings_table.c.rating

# Определение класса Category, связанного с таблицей 'categories'
class Category(Base):
    __table__ = categories_table

    id = categories_table.c.id
    name = categories_table.c.name
    parent_id = categories_table.c.parent_id

    # Связь с дочерними категориями
    parent = relationship('Category', remote_side=[id], backref='children')

# Определение класса Store, связанного с таблицей 'stores'
class Store(Base):
    __table__ = stores_table

    id = stores_table.c.id
    name = stores_table.c.name
    short_name = stores_table.c.short_name
    llc_name = stores_table.c.llc_name
    store_main_picture = stores_table.c.store_main_picture
    address = stores_table.c.address
    region_id = stores_table.c.region_id
    category_id = stores_table.c.category_id
    owner_id = stores_table.c.owner_id
    rating = stores_table.c.rating
    is_verified = stores_table.c.is_verified
    created_at = stores_table.c.created_at
    last_active = stores_table.c.last_active

    # Связь с эл. почтами
    emails = relationship('StoreEmail', back_populates="store")
    # Связь с номерами телефонов
    phone_numbers = relationship('StorePhoneNumber', back_populates="store")
    #Связь с менеджерами 
    managers = relationship('StoreManager', back_populates="store")
    # Связь с создателем
    owner = relationship('User', back_populates="my_stores")

# Определение класса StoreEmail, связанного с таблицей 'store_emails'
class StoreEmail(Base):
    __table__ = store_emails_table

    id = store_emails_table.c.id
    store_id = store_emails_table.c.store_id
    email = store_emails_table.c.email
    email_type = store_emails_table.c.email_type

    # Связь с магазином
    store = relationship('Store', back_populates="emails")

# Определение класса StorePhoneNumber, связанного с таблицей 'store_phone_numbers'
class StorePhoneNumber(Base):
    __table__ = store_phone_numbers_table

    id = store_phone_numbers_table.c.id
    store_id = store_phone_numbers_table.c.store_id
    phone_number = store_phone_numbers_table.c.phone_number
    phone_type = store_phone_numbers_table.c.phone_type

    # Связь с магазином
    store = relationship('Store', back_populates="phone_numbers")

# Определение класса StorePrivilege, связанного с таблицей 'store_privileges'
class StorePrivilege(Base):
    __table__ = store_privileges_table

    id = store_privileges_table.c.id
    name = store_privileges_table.c.name
    access_level = store_privileges_table.c.access_level

    # Связь с менеджером
    manager = relationship('StoreManager', back_populates="privileges")

# Определение класса StoreManager, связанного с таблицей 'store_managers'
class StoreManager(Base):
    __table__ = store_managers_table

    id = store_managers_table.c.id
    store_id = store_managers_table.c.store_id
    user_id = store_managers_table.c.user_id
    privileges_id = store_managers_table.c.privileges_id

    # Связь с приыилегиями
    privileges = relationship('StorePrivilege', back_populates="manager")
    # Связь с магазином
    store = relationship('Store', back_populates="managers")
    # Связь с пользователем
    user = relationship("User", back_populates="store_managers")


"""SERVICES"""
# Определение класса сервисов
class ServicesCategories(Base):
    __table__= services_categories_table

    id = services_categories_table.c.id
    title = services_categories_table.c.title
    description = services_categories_table.c.description
    picture = services_categories_table.c.picture

# Определение таблицы способов оплаты
class PaymentMethod(Base):
    __table__ = payment_methodes_table

    id = payment_methodes_table.c.id
    methods_name = payment_methodes_table.c.method_name

# Определение таблицы рейтинга объявления
class ServiceRating(Base):
    __table__ = services_ratings_table

    id = services_ratings_table.c.id
    service_id = services_ratings_table.c.service_id
    rater_id = services_ratings_table.c.rater_id

# Определение таблицы количество просмотров
class ServiceViews(Base):
    __table__ = services_views_table

    id = services_views_table.c.id
    service_id = services_views_table.c.service_id
    rater_id = services_views_table.c.rater_id

# Определение таблицы объявлений
class Service(Base):
    __table__ = services_table

    id = services_table.c.id
    name = services_table.c.name
    lat = services_table.c.lat
    lon = services_table.c.lon
    rating_count = services_table.c.rating_count
    views_count = services_table.c.views_count
    description = services_table.c.description
    price = services_table.c.price
    owner_id = services_table.c.owner_id
    is_active = services_table.c.is_active
    date = services_table.c.date
    picture = services_table.c.picture
    is_store = services_table.c.is_store
    phone_number = services_table.c.phone_number
    email = services_table.c.email
    service_id = services_table.c.service_id
    payment_method_id = services_table.c.payment_method_id

# Определение таблицы рабочих часов объявления сервиса
class ServiceWorkTimes(Base):
    __table__ = services_work_times_table

    id = services_work_times_table.c.id
    service_id = services_work_times_table.c.service_id
    is_morning = services_work_times_table.c.is_morning
    is_day = services_work_times_table.c.is_day
    is_evening = services_work_times_table.c.is_evening
    time_in_second = services_work_times_table.c.time_in_second

# Определение таблицы забронированных сервисов
class BookedService(Base):
    __table__ = booked_services

    id = booked_services.c.id
    user_id = booked_services.c.user_id
    service_id = booked_services.c.service_id
    date = booked_services.c.date 
    time = booked_services.c.time