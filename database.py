import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import os

class Database:
    def __init__(self, db_name="master_pol.db"):
        self.db_name = db_name
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            # Удаляем старую базу данных для пересоздания
            if os.path.exists(self.db_name):
                os.remove(self.db_name)
                self.logger.info("Удалена старая база данных")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица типов материалов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_type TEXT UNIQUE NOT NULL,
                    defect_percentage REAL NOT NULL
                )
            ''')
            
            # Таблица типов продукции
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_type TEXT UNIQUE NOT NULL,
                    type_coefficient REAL NOT NULL
                )
            ''')
            
            # Таблица продукции
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    article TEXT UNIQUE NOT NULL,
                    min_partner_price REAL NOT NULL,
                    package_length REAL,
                    package_width REAL,
                    package_height REAL,
                    weight_without_package REAL,
                    weight_with_package REAL,
                    quality_certificate BLOB,
                    standard_number TEXT,
                    price_history TEXT,
                    production_time INTEGER,
                    cost_price REAL,
                    workshop_number INTEGER,
                    workers_count INTEGER,
                    required_materials TEXT,
                    stock_quantity INTEGER DEFAULT 0,
                    FOREIGN KEY (product_type) REFERENCES product_types(product_type)
                )
            ''')
            
            # Таблица партнеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_type TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    legal_address TEXT NOT NULL,
                    inn TEXT UNIQUE NOT NULL,
                    director_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    logo BLOB,
                    rating INTEGER DEFAULT 5,
                    sales_locations TEXT,
                    discount_history TEXT
                )
            ''')
            
            # Таблица сотрудников
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_date TEXT,
                    passport_data TEXT,
                    bank_details TEXT,
                    family_status TEXT,
                    health_status TEXT,
                    equipment_access TEXT,
                    position TEXT DEFAULT 'Менеджер'
                )
            ''')
            
            # Таблица заявок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    manager_id INTEGER,
                    order_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    products_list TEXT NOT NULL,
                    total_cost REAL,
                    production_date TEXT,
                    prepayment_received BOOLEAN DEFAULT FALSE,
                    prepayment_date TEXT,
                    prepayment_amount REAL DEFAULT 0,
                    full_payment_received BOOLEAN DEFAULT FALSE,
                    full_payment_date TEXT,
                    delivery_method TEXT,
                    completion_date TEXT,
                    notes TEXT,
                    FOREIGN KEY (partner_id) REFERENCES partners(id),
                    FOREIGN KEY (manager_id) REFERENCES employees(id)
                )
            ''')
            
            # Таблица истории продаж
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    sale_date TEXT NOT NULL,
                    total_amount REAL,
                    FOREIGN KEY (partner_id) REFERENCES partners(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            # Таблица истории рейтингов партнеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partner_rating_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    old_rating INTEGER,
                    new_rating INTEGER,
                    change_date TEXT NOT NULL,
                    changed_by INTEGER,
                    reason TEXT,
                    FOREIGN KEY (partner_id) REFERENCES partners(id),
                    FOREIGN KEY (changed_by) REFERENCES employees(id)
                )
            ''')
            
            # Добавляем тестового менеджера
            cursor.execute('''
                INSERT OR IGNORE INTO employees 
                (full_name, position) 
                VALUES (?, ?)
            ''', ('Иванов Иван Иванович', 'Старший менеджер'))
            
            cursor.execute('''
                INSERT OR IGNORE INTO employees 
                (full_name, position) 
                VALUES (?, ?)
            ''', ('Петрова Мария Сергеевна', 'Менеджер по продажам'))
            
            conn.commit()
            self.logger.info("База данных успешно инициализирована")
            
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка инициализации базы данных: {e}")
        finally:
            conn.close()

    def import_partners(self, file_path):
        """Импорт данных о партнерах из Excel файла"""
        try:
            df = pd.read_excel(file_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO partners 
                    (partner_type, company_name, director_name, email, phone, legal_address, inn, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['Тип партнера'],
                    row['Наименование партнера'],
                    row['Директор'],
                    row['Электронная почта партнера'],
                    row['Телефон партнера'],
                    row['Юридический адрес партнера'],
                    row['ИНН'],
                    row['Рейтинг']
                ))
            
            conn.commit()
            self.logger.info(f"Импортировано {len(df)} партнеров")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта партнеров: {e}")
            return False
        finally:
            conn.close()
    
    def import_material_types(self, file_path):
        """Импорт типов материалов из Excel файла"""
        try:
            df = pd.read_excel(file_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO material_types 
                    (material_type, defect_percentage)
                    VALUES (?, ?)
                ''', (row['Тип материала'], row['Процент брака материала']))
            
            conn.commit()
            self.logger.info(f"Импортировано {len(df)} типов материалов")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта типов материалов: {e}")
            return False
        finally:
            conn.close()
    
    def import_product_types(self, file_path):
        """Импорт типов продукции из Excel файла"""
        try:
            df = pd.read_excel(file_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO product_types 
                    (product_type, type_coefficient)
                    VALUES (?, ?)
                ''', (row['Тип продукции'], row['Коэффициент типа продукции']))
            
            conn.commit()
            self.logger.info(f"Импортировано {len(df)} типов продукции")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта типов продукции: {e}")
            return False
        finally:
            conn.close()
    
    def import_products(self, file_path):
        """Импорт продукции из Excel файла"""
        try:
            df = pd.read_excel(file_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO products 
                    (product_type, name, article, min_partner_price)
                    VALUES (?, ?, ?, ?)
                ''', (
                    row['Тип продукции'],
                    row['Наименование продукции'],
                    row['Артикул'],
                    row['Минимальная стоимость для партнера']
                ))
            
            conn.commit()
            self.logger.info(f"Импортировано {len(df)} продуктов")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта продуктов: {e}")
            return False
        finally:
            conn.close()
    
    def import_sales_history(self, file_path):
        """Импорт истории продаж из Excel файла"""
        try:
            df = pd.read_excel(file_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            imported_count = 0
            for _, row in df.iterrows():
                # Получаем ID партнера и продукта
                cursor.execute('SELECT id FROM partners WHERE company_name = ?', (row['Наименование партнера'],))
                partner_result = cursor.fetchone()
                
                cursor.execute('SELECT id FROM products WHERE name = ?', (row['Продукция'],))
                product_result = cursor.fetchone()
                
                if partner_result and product_result:
                    partner_id = partner_result[0]
                    product_id = product_result[0]
                    
                    # Получаем стоимость продукта для расчета общей суммы
                    cursor.execute('SELECT min_partner_price FROM products WHERE id = ?', (product_id,))
                    price_result = cursor.fetchone()
                    total_amount = price_result[0] * row['Количество продукции'] if price_result else 0
                    
                    cursor.execute('''
                        INSERT INTO sales_history 
                        (partner_id, product_id, quantity, sale_date, total_amount)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        partner_id,
                        product_id,
                        row['Количество продукции'],
                        row['Дата продажи'],
                        total_amount
                    ))
                    imported_count += 1
            
            conn.commit()
            self.logger.info(f"Импортировано {imported_count} записей истории продаж")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта истории продаж: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_partners(self):
        """Получение всех партнеров"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners ORDER BY company_name')
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения партнеров: {e}")
            return []
        finally:
            conn.close()

    def get_all_products(self):
        """Получение всей продукции"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY name')
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения продукции: {e}")
            return []
        finally:
            conn.close()

    def get_product_by_name(self, product_name):
        """Получение продукта по названию"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE name = ?', (product_name,))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Ошибка получения продукта: {e}")
            return None
        finally:
            conn.close()

    def get_partner_by_name(self, partner_name):
        """Получение партнера по названию"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM partners WHERE company_name = ?', (partner_name,))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Ошибка получения партнера: {e}")
            return None
        finally:
            conn.close()

    def get_all_employees(self):
        """Получение всех сотрудников"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees ORDER BY full_name')
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения сотрудников: {e}")
            return []
        finally:
            conn.close()

    def get_all_orders(self):
        """Получение всех заявок"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, p.company_name, e.full_name as manager_name
                FROM orders o
                LEFT JOIN partners p ON o.partner_id = p.id
                LEFT JOIN employees e ON o.manager_id = e.id
                ORDER BY o.order_date DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения заявок: {e}")
            return []
        finally:
            conn.close()

    def get_orders_by_status(self, status):
        """Получение заявок по статусу"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, p.company_name, e.full_name as manager_name
                FROM orders o
                LEFT JOIN partners p ON o.partner_id = p.id
                LEFT JOIN employees e ON o.manager_id = e.id
                WHERE o.status = ?
                ORDER BY o.order_date DESC
            ''', (status,))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка получения заявок: {e}")
            return []
        finally:
            conn.close()

    def create_order(self, partner_id, manager_id, products_list, total_cost, delivery_method=None):
        """Создание новой заявки"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO orders 
                (partner_id, manager_id, order_date, status, products_list, total_cost, delivery_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                partner_id,
                manager_id,
                order_date,
                'created',
                json.dumps(products_list),
                total_cost,
                delivery_method
            ))
            
            order_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Создана заявка #{order_id} для партнера #{partner_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"Ошибка создания заявки: {e}")
            return None
        finally:
            conn.close()

    def update_order_status(self, order_id, status, notes=None):
        """Обновление статуса заявки"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            update_fields = "status = ?"
            params = [status]
            
            if status == 'prepayment_received':
                update_fields += ", prepayment_received = TRUE, prepayment_date = ?"
                params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            elif status == 'in_production':
                update_fields += ", production_date = ?"
                params.append(datetime.now().strftime('%Y-%m-%d'))
            elif status == 'ready':
                update_fields += ", completion_date = ?"
                params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            elif status == 'completed':
                update_fields += ", full_payment_received = TRUE, full_payment_date = ?, completion_date = ?"
                params.extend([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
            elif status == 'cancelled':
                update_fields += ", prepayment_received = FALSE"
            
            if notes:
                update_fields += ", notes = ?"
                params.append(notes)
            
            params.append(order_id)
            
            cursor.execute(f'UPDATE orders SET {update_fields} WHERE id = ?', params)
            conn.commit()
            
            self.logger.info(f"Статус заявки #{order_id} изменен на '{status}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса заявки: {e}")
            return False
        finally:
            conn.close()

    def add_partner(self, partner_data):
        """Добавление нового партнера"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO partners 
                (partner_type, company_name, legal_address, inn, director_name, email, phone, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                partner_data['partner_type'],
                partner_data['company_name'],
                partner_data['legal_address'],
                partner_data['inn'],
                partner_data['director_name'],
                partner_data['email'],
                partner_data['phone'],
                partner_data.get('rating', 5)
            ))
            
            partner_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Добавлен новый партнер: {partner_data['company_name']}")
            
            return partner_id
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления партнера: {e}")
            return None
        finally:
            conn.close()

    def update_partner_rating(self, partner_id, new_rating, changed_by, reason=None):
        """Обновление рейтинга партнера"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Получаем текущий рейтинг
            cursor.execute('SELECT rating FROM partners WHERE id = ?', (partner_id,))
            old_rating = cursor.fetchone()[0]
            
            # Обновляем рейтинг
            cursor.execute('UPDATE partners SET rating = ? WHERE id = ?', (new_rating, partner_id))
            
            # Добавляем запись в историю
            cursor.execute('''
                INSERT INTO partner_rating_history 
                (partner_id, old_rating, new_rating, change_date, changed_by, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                partner_id,
                old_rating,
                new_rating,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                changed_by,
                reason
            ))
            
            conn.commit()
            self.logger.info(f"Рейтинг партнера #{partner_id} изменен с {old_rating} на {new_rating}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления рейтинга: {e}")
            return False
        finally:
            conn.close()

    def get_partner_sales_statistics(self, partner_id):
        """Получение статистики продаж для партнера"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    p.company_name,
                    SUM(sh.quantity) as total_quantity,
                    SUM(sh.total_amount) as total_amount,
                    COUNT(DISTINCT sh.product_id) as unique_products
                FROM sales_history sh
                JOIN partners p ON p.id = sh.partner_id
                WHERE sh.partner_id = ?
                GROUP BY p.company_name
            ''', (partner_id,))
            
            result = cursor.fetchone()
            return {
                'company_name': result[0] if result else '',
                'total_quantity': result[1] if result else 0,
                'total_amount': result[2] if result else 0,
                'unique_products': result[3] if result else 0
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики продаж: {e}")
            return {}
        finally:
            conn.close()
    
    def calculate_partner_discount(self, partner_id):
        """Расчет скидки для партнера на основе истории продаж"""
        try:
            stats = self.get_partner_sales_statistics(partner_id)
            total_amount = stats.get('total_amount', 0)
            
            # Логика расчета скидки на основе общего объема продаж
            if total_amount > 10000000:  # более 10 млн
                discount = 0.15  # 15%
            elif total_amount > 5000000:  # более 5 млн
                discount = 0.10  # 10%
            elif total_amount > 1000000:  # более 1 млн
                discount = 0.05  # 5%
            else:
                discount = 0.02  # 2%
            
            return discount
            
        except Exception as e:
            self.logger.error(f"Ошибка расчета скидки: {e}")
            return 0.0

    def get_top_products(self, limit=10):
        """Получение топовых продуктов по продажам"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    p.name,
                    p.product_type,
                    SUM(sh.quantity) as total_sold,
                    SUM(sh.total_amount) as total_revenue
                FROM sales_history sh
                JOIN products p ON p.id = sh.product_id
                GROUP BY p.id
                ORDER BY total_sold DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            self.logger.error(f"Ошибка получения топовых продуктов: {e}")
            return []
        finally:
            conn.close()

    def check_expired_orders(self):
        """Проверка заявок с истекшим сроком предоплаты"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT id, partner_id 
                FROM orders 
                WHERE status = 'created' 
                AND prepayment_received = FALSE
                AND order_date < ?
            ''', (three_days_ago,))
            
            expired_orders = cursor.fetchall()
            
            for order in expired_orders:
                cursor.execute('''
                    UPDATE orders 
                    SET status = 'cancelled', notes = 'Автоматическая отмена: не поступила предоплата в течение 3 дней'
                    WHERE id = ?
                ''', (order[0],))
            
            conn.commit()
            self.logger.info(f"Автоматически отменено {len(expired_orders)} заявок")
            
            return len(expired_orders)
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки просроченных заявок: {e}")
            return 0
        finally:
            conn.close()