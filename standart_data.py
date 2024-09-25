from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, Role, StorePrivilege, StoreManager  # Импортируйте свои модели и Base из соответствующего модуля
from config import DB_CONNECT  # Импортируйте URL вашей базы данных

def roles_and_privileges():
    # Автозаполнение ролей и привилегий
    # Создание подключения к базе данных
    engine = create_engine(DB_CONNECT)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Проверка наличия данных в таблице 'roles'
    if session.query(Role).count() == 0:
        # Определение начальных данных
        roles = [
            {"name": "admin", "permission": "all"},
            {"name": "user", "permission": "basic"},
            {"name": "guest", "permission": "read"}
        ]
        
        # Заполнение таблицы 'roles'
        for role_data in roles:
            role = Role(name=role_data["name"], permission=role_data["permission"])
            session.add(role)
        
        session.commit()
        print("Roles populated successfully.")
    else:
        print("Roles table already contains data.")
    
    # Проверка наличия данных в таблице 'store_privileges'
    if session.query(StorePrivilege).count() == 0:
        # Определение начальных данных
        privileges = [
            {
                "name": "director",
                "access_level": 5
            },
            {
                "name": "manager",
                "access_level": 4
            },
            {
                "name": "editor",
                "access_level": 3
            },
            {
                "name": "accountant",
                "access_level": 2
            },
            {
                "name": "viewer",
                "access_level": 1
            },
        ]
        
        # Заполнение таблицы 'store_privileges'
        for privilege_data in privileges:
            privilege = StorePrivilege(
                name=privilege_data["name"], 
                access_level=privilege_data["access_level"]
            )
            session.add(privilege)
        
        session.commit()
        print("StorePrivileges populated successfully.")
    else:
        print("StorePrivileges table already contains data.")

    session.close()

if __name__ == "__main__":
    roles_and_privileges()