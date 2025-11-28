import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from datetime import datetime
import json
from database import Database

class MasterPolGUI:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.current_order_items = []
        self.setup_logging()
        self.setup_gui()
        self.import_initial_data()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_gui(self):
        """Настройка графического интерфейса"""
        self.root.title("Система 'Мастер пол' - Управление производством")
        self.root.geometry("1400x800")
        
        # Создание вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка партнеров
        self.partners_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.partners_frame, text="📊 Партнеры")
        self.setup_partners_tab()
        
        # Вкладка продукции
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="📦 Продукция")
        self.setup_products_tab()
        
        # Вкладка заявок
        self.orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.orders_frame, text="📋 Заявки")
        self.setup_orders_tab()
        
        # Вкладка управления заявками
        self.manage_orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.manage_orders_frame, text="⚙️ Управление заявками")
        self.setup_manage_orders_tab()
        
        # Вкладка статистики
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📈 Статистика")
        self.setup_stats_tab()
        
        # Вкладка импорта
        self.import_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.import_frame, text="📥 Импорт данных")
        self.setup_import_tab()
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x')
    
    def setup_partners_tab(self):
        """Настройка вкладки партнеров"""
        # Панель управления
        control_frame = ttk.Frame(self.partners_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Обновить список", 
                  command=self.update_partners_list).pack(side='left', padx=5)
        
        # Панель поиска
        search_frame = ttk.Frame(self.partners_frame)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side='left', padx=5)
        self.partner_search_var = tk.StringVar()
        self.partner_search_entry = ttk.Entry(search_frame, textvariable=self.partner_search_var, width=30)
        self.partner_search_entry.pack(side='left', padx=5)
        self.partner_search_entry.bind('<KeyRelease>', self.search_partners)
        
        # Таблица партнеров
        columns = ('ID', 'Тип', 'Компания', 'Директор', 'Email', 'Телефон', 'Рейтинг', 'ИНН')
        self.partners_tree = ttk.Treeview(self.partners_frame, columns=columns, show='headings', height=15)
        
        column_widths = [50, 80, 200, 150, 150, 120, 80, 120]
        for i, col in enumerate(columns):
            self.partners_tree.heading(col, text=col)
            self.partners_tree.column(col, width=column_widths[i])
        
        scrollbar = ttk.Scrollbar(self.partners_frame, orient='vertical', command=self.partners_tree.yview)
        self.partners_tree.configure(yscrollcommand=scrollbar.set)
        
        self.partners_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=5, pady=5)
        
        # Панель деталей
        details_frame = ttk.LabelFrame(self.partners_frame, text="Детали партнера")
        details_frame.pack(fill='x', padx=5, pady=5)
        
        self.partner_info_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.partner_info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Обновление данных
        self.update_partners_list()
        self.partners_tree.bind('<<TreeviewSelect>>', self.on_partner_select)
    
    def setup_products_tab(self):
        """Настройка вкладки продукции"""
        # Таблица продукции
        columns = ('ID', 'Тип', 'Наименование', 'Артикул', 'Цена', 'На складе')
        self.products_tree = ttk.Treeview(self.products_frame, columns=columns, show='headings', height=20)
        
        column_widths = [50, 100, 300, 100, 100, 80]
        for i, col in enumerate(columns):
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=column_widths[i])
        
        scrollbar = ttk.Scrollbar(self.products_frame, orient='vertical', command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.products_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=5, pady=5)
        
        # Обновление данных
        self.update_products_list()
    
    def setup_orders_tab(self):
        """Настройка вкладки создания заявок"""
        main_frame = ttk.Frame(self.orders_frame)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Левая панель - форма заявки
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        
        form_frame = ttk.LabelFrame(left_frame, text="Создание заявки")
        form_frame.pack(fill='x', padx=5, pady=5)
        
        # Выбор партнера
        ttk.Label(form_frame, text="Партнер:*").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.order_partner_var = tk.StringVar()
        self.order_partner_combo = ttk.Combobox(form_frame, textvariable=self.order_partner_var, state='readonly', width=30)
        self.order_partner_combo.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.order_partner_combo.bind('<<ComboboxSelected>>', self.on_partner_selected_for_order)
        
        # Выбор менеджера
        ttk.Label(form_frame, text="Менеджер:*").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.order_manager_var = tk.StringVar()
        self.order_manager_combo = ttk.Combobox(form_frame, textvariable=self.order_manager_var, state='readonly', width=30)
        self.order_manager_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Выбор продукции
        ttk.Label(form_frame, text="Продукция:*").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.order_product_var = tk.StringVar()
        self.order_product_combo = ttk.Combobox(form_frame, textvariable=self.order_product_var, state='readonly', width=30)
        self.order_product_combo.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        
        # Количество
        ttk.Label(form_frame, text="Количество:*").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.order_quantity_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.order_quantity_var, width=30).grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        
        # Способ доставки
        ttk.Label(form_frame, text="Доставка:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.delivery_method_var = tk.StringVar(value="самовывоз")
        delivery_combo = ttk.Combobox(form_frame, textvariable=self.delivery_method_var, 
                                     values=["самовывоз", "доставка"], state='readonly', width=30)
        delivery_combo.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        
        # Кнопки управления
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Добавить в заявку", 
                  command=self.add_to_order).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Очистить заявку", 
                  command=self.clear_order).pack(side='left', padx=5)
        
        # Информация о скидке
        discount_frame = ttk.LabelFrame(left_frame, text="Информация о скидке")
        discount_frame.pack(fill='x', padx=5, pady=5)
        
        self.discount_info_text = scrolledtext.ScrolledText(discount_frame, height=4, wrap=tk.WORD)
        self.discount_info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Правая панель - список товаров в заявке
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        order_list_frame = ttk.LabelFrame(right_frame, text="Товары в заявке")
        order_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('Продукт', 'Количество', 'Цена', 'Сумма')
        self.order_tree = ttk.Treeview(order_list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(order_list_frame, orient='vertical', command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        
        self.order_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=5, pady=5)
        
        # Управление элементами заявки
        item_control_frame = ttk.Frame(order_list_frame)
        item_control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(item_control_frame, text="Удалить выбранный", 
                  command=self.remove_order_item).pack(side='left', padx=5)
        
        # Итоговая информация
        total_frame = ttk.LabelFrame(right_frame, text="Итоговая информация")
        total_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(total_frame, text="Общая сумма:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.order_total_var = tk.StringVar(value="0.00 руб.")
        ttk.Label(total_frame, textvariable=self.order_total_var, font=('Arial', 12, 'bold')).grid(row=0, column=1, padx=5, pady=2, sticky='w')
        
        ttk.Label(total_frame, text="Скидка:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.order_discount_var = tk.StringVar(value="0%")
        ttk.Label(total_frame, textvariable=self.order_discount_var, font=('Arial', 12, 'bold')).grid(row=1, column=1, padx=5, pady=2, sticky='w')
        
        ttk.Label(total_frame, text="Итоговая сумма:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        self.order_final_var = tk.StringVar(value="0.00 руб.")
        ttk.Label(total_frame, textvariable=self.order_final_var, font=('Arial', 12, 'bold'), foreground='green').grid(row=2, column=1, padx=5, pady=2, sticky='w')
        
        # Кнопка создания заявки
        ttk.Button(right_frame, text="Создать заявку", 
                  command=self.create_order).pack(pady=10)
        
        # Обновление данных
        self.update_order_form_data()
    
    def setup_manage_orders_tab(self):
        """Настройка вкладки управления заявками"""
        # Панель фильтров
        filter_frame = ttk.Frame(self.manage_orders_frame)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Статус:").pack(side='left', padx=5)
        self.filter_status_var = tk.StringVar(value="все")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.filter_status_var, 
                                   values=["все", "created", "prepayment_received", "in_production", "ready", "completed", "cancelled"], 
                                   state='readonly', width=15)
        status_combo.pack(side='left', padx=5)
        status_combo.bind('<<ComboboxSelected>>', self.filter_orders)
        
        ttk.Button(filter_frame, text="Обновить", 
                  command=self.update_orders_list).pack(side='left', padx=20)
        ttk.Button(filter_frame, text="Проверить просроченные", 
                  command=self.check_expired_orders).pack(side='left', padx=5)
        
        # Таблица заявок
        columns = ('ID', 'Дата', 'Партнер', 'Менеджер', 'Сумма', 'Статус', 'Доставка')
        self.orders_manage_tree = ttk.Treeview(self.manage_orders_frame, columns=columns, show='headings', height=15)
        
        column_widths = [50, 120, 200, 150, 100, 120, 100]
        for i, col in enumerate(columns):
            self.orders_manage_tree.heading(col, text=col)
            self.orders_manage_tree.column(col, width=column_widths[i])
        
        scrollbar = ttk.Scrollbar(self.manage_orders_frame, orient='vertical', command=self.orders_manage_tree.yview)
        self.orders_manage_tree.configure(yscrollcommand=scrollbar.set)
        
        self.orders_manage_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=5, pady=5)
        
        # Панель управления статусом
        status_control_frame = ttk.LabelFrame(self.manage_orders_frame, text="Управление статусом заявки")
        status_control_frame.pack(fill='x', padx=5, pady=5)
        
        control_inner_frame = ttk.Frame(status_control_frame)
        control_inner_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_inner_frame, text="Предоплата получена", 
                  command=lambda: self.update_selected_order_status('prepayment_received')).pack(side='left', padx=5)
        ttk.Button(control_inner_frame, text="В производство", 
                  command=lambda: self.update_selected_order_status('in_production')).pack(side='left', padx=5)
        ttk.Button(control_inner_frame, text="Готово к отгрузке", 
                  command=lambda: self.update_selected_order_status('ready')).pack(side='left', padx=5)
        ttk.Button(control_inner_frame, text="Завершено", 
                  command=lambda: self.update_selected_order_status('completed')).pack(side='left', padx=5)
        ttk.Button(control_inner_frame, text="Отменить", 
                  command=lambda: self.update_selected_order_status('cancelled')).pack(side='left', padx=5)
        
        # Детали заявки
        details_frame = ttk.LabelFrame(self.manage_orders_frame, text="Детали заявки")
        details_frame.pack(fill='x', padx=5, pady=5)
        
        self.order_details_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.order_details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Обновление данных
        self.update_orders_list()
        self.orders_manage_tree.bind('<<TreeviewSelect>>', self.on_order_select)
    
    def setup_stats_tab(self):
        """Настройка вкладки статистики"""
        notebook_stats = ttk.Notebook(self.stats_frame)
        notebook_stats.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Вкладка статистики партнеров
        partner_stats_frame = ttk.Frame(notebook_stats)
        notebook_stats.add(partner_stats_frame, text="Статистика партнеров")
        
        # Выбор партнера для статистики
        partner_frame = ttk.Frame(partner_stats_frame)
        partner_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(partner_frame, text="Выберите партнера:").pack(side='left', padx=5)
        self.stats_partner_var = tk.StringVar()
        self.stats_partner_combo = ttk.Combobox(partner_frame, textvariable=self.stats_partner_var, state='readonly')
        self.stats_partner_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.stats_partner_combo.bind('<<ComboboxSelected>>', self.show_partner_stats)
        
        # Статистика партнера
        stats_frame = ttk.LabelFrame(partner_stats_frame, text="Статистика партнера")
        stats_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10, wrap=tk.WORD)
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Вкладка топ продуктов
        top_products_frame = ttk.Frame(notebook_stats)
        notebook_stats.add(top_products_frame, text="Топ продуктов")
        
        # Топ продуктов
        top_frame = ttk.LabelFrame(top_products_frame, text="Топ продуктов по продажам")
        top_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('Продукт', 'Тип', 'Кол-во продаж', 'Выручка')
        self.top_products_tree = ttk.Treeview(top_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.top_products_tree.heading(col, text=col)
            self.top_products_tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(top_frame, orient='vertical', command=self.top_products_tree.yview)
        self.top_products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.top_products_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=5, pady=5)
        
        # Обновление данных
        self.update_stats_data()
    
    def setup_import_tab(self):
        """Настройка вкладки импорта данных"""
        main_frame = ttk.Frame(self.import_frame)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Кнопки импорта
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Импорт типов материалов", 
                  command=lambda: self.import_data('material_types')).pack(fill='x', pady=2)
        
        ttk.Button(button_frame, text="Импорт типов продукции", 
                  command=lambda: self.import_data('product_types')).pack(fill='x', pady=2)
        
        ttk.Button(button_frame, text="Импорт продукции", 
                  command=lambda: self.import_data('products')).pack(fill='x', pady=2)
        
        ttk.Button(button_frame, text="Импорт партнеров", 
                  command=lambda: self.import_data('partners')).pack(fill='x', pady=2)
        
        ttk.Button(button_frame, text="Импорт истории продаж", 
                  command=lambda: self.import_data('sales')).pack(fill='x', pady=2)
        
        ttk.Button(button_frame, text="Импорт всех данных", 
                  command=self.import_all_data).pack(fill='x', pady=10)
        
        # Лог импорта
        log_frame = ttk.LabelFrame(main_frame, text="Лог операций")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.import_log = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.import_log.pack(fill='both', expand=True, padx=5, pady=5)
    
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    
    def update_partners_list(self, search_term=""):
        """Обновление списка партнеров"""
        for item in self.partners_tree.get_children():
            self.partners_tree.delete(item)
        
        partners = self.db.get_all_partners()
        for partner in partners:
            if search_term.lower() in partner[2].lower():  # Поиск по названию компании
                self.partners_tree.insert('', 'end', values=partner)
    
    def update_products_list(self):
        """Обновление списка продукции"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        products = self.db.get_all_products()
        for product in products:
            # Добавляем случайное количество на складе для демонстрации
            import random
            stock = random.randint(0, 1000)
            product_with_stock = product + (stock,)
            self.products_tree.insert('', 'end', values=product_with_stock)
    
    def update_stats_data(self):
        """Обновление данных статистики"""
        # Обновление списка партнеров для статистики
        partners = self.db.get_all_partners()
        partner_names = [partner[2] for partner in partners]
        self.stats_partner_combo['values'] = partner_names
        
        # Обновление топа продуктов
        for item in self.top_products_tree.get_children():
            self.top_products_tree.delete(item)
        
        top_products = self.db.get_top_products()
        for product in top_products:
            self.top_products_tree.insert('', 'end', values=product)
    
    def update_order_form_data(self):
        """Обновление данных формы заявки"""
        partners = self.db.get_all_partners()
        partner_names = [partner[2] for partner in partners]
        self.order_partner_combo['values'] = partner_names
        
        products = self.db.get_all_products()
        product_names = [f"{product[2]} ({product[3]})" for product in products]
        self.order_product_combo['values'] = product_names
        
        employees = self.db.get_all_employees()
        employee_names = [f"{emp[1]} ({emp[8]})" for emp in employees]
        self.order_manager_combo['values'] = employee_names
    
    def search_partners(self, event=None):
        """Поиск партнеров"""
        search_term = self.partner_search_var.get()
        self.update_partners_list(search_term)
    
    def on_partner_select(self, event):
        """Обработка выбора партнера"""
        selection = self.partners_tree.selection()
        if selection:
            item = self.partners_tree.item(selection[0])
            partner_data = item['values']
            
            # Получение статистики
            stats = self.db.get_partner_sales_statistics(partner_data[0])
            discount = self.db.calculate_partner_discount(partner_data[0])
            
            info_text = f"""
Компания: {partner_data[2]}
Тип: {partner_data[1]}
Директор: {partner_data[3]}
Email: {partner_data[4]}
Телефон: {partner_data[5]}
Рейтинг: {partner_data[6]}
ИНН: {partner_data[7]}

СТАТИСТИКА ПРОДАЖ:
Общее количество: {stats.get('total_quantity', 0):,} ед.
Общая сумма: {stats.get('total_amount', 0):,.2f} руб.
Уникальных продуктов: {stats.get('unique_products', 0)}
Текущая скидка: {discount * 100:.1f}%
"""
            self.partner_info_text.delete(1.0, tk.END)
            self.partner_info_text.insert(1.0, info_text)
    
    def show_partner_stats(self, event=None):
        """Показать статистику выбранного партнера"""
        partner_name = self.stats_partner_var.get()
        if partner_name:
            partners = self.db.get_all_partners()
            partner_id = None
            for partner in partners:
                if partner[2] == partner_name:
                    partner_id = partner[0]
                    break
            
            if partner_id:
                stats = self.db.get_partner_sales_statistics(partner_id)
                discount = self.db.calculate_partner_discount(partner_id)
                
                stats_text = f"""
СТАТИСТИКА ПАРТНЕРА: {partner_name}

Общее количество проданной продукции: {stats.get('total_quantity', 0):,} ед.
Общая сумма продаж: {stats.get('total_amount', 0):,.2f} руб.
Количество уникальных продуктов: {stats.get('unique_products', 0)}
Текущая скидка: {discount * 100:.1f}%

Уровни скидок:
- Базовый уровень: 2%
- От 1 млн руб.: 5%
- От 5 млн руб.: 10%
- От 10 млн руб.: 15%
"""
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, stats_text)
    
    def on_partner_selected_for_order(self, event=None):
        """Обработка выбора партнера для заявки"""
        partner_name = self.order_partner_var.get()
        if partner_name:
            partner = self.db.get_partner_by_name(partner_name)
            if partner:
                stats = self.db.get_partner_sales_statistics(partner[0])
                discount = self.db.calculate_partner_discount(partner[0])
                
                discount_text = f"""
Партнер: {partner_name}
Объем продаж: {stats.get('total_amount', 0):,.2f} руб.
Текущая скидка: {discount * 100:.1f}%

Следующий уровень скидки:
"""
                if discount < 0.15:
                    next_level = "15%" if discount < 0.10 else "10%" if discount < 0.05 else "5%"
                    required = 10000000 if discount < 0.10 else 5000000 if discount < 0.05 else 1000000
                    current = stats.get('total_amount', 0)
                    remaining = max(0, required - current)
                    discount_text += f"- Для получения скидки {next_level} необходимо продать еще {remaining:,.2f} руб."
                
                self.discount_info_text.delete(1.0, tk.END)
                self.discount_info_text.insert(1.0, discount_text)
                self.calculate_order_total()
    
    def add_to_order(self):
        """Добавление товара в заявку"""
        try:
            product_name_with_article = self.order_product_var.get()
            quantity_str = self.order_quantity_var.get()
            
            if not product_name_with_article or not quantity_str:
                messagebox.showwarning("Предупреждение", "Выберите продукт и укажите количество")
                return
            
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    messagebox.showwarning("Предупреждение", "Количество должно быть положительным числом")
                    return
            except ValueError:
                messagebox.showwarning("Предупреждение", "Введите корректное количество")
                return
            
            # Извлекаем название продукта (без артикула)
            product_name = product_name_with_article.split(' (')[0]
            product = self.db.get_product_by_name(product_name)
            if not product:
                messagebox.showerror("Ошибка", "Продукт не найден")
                return
            
            product_id, product_type, name, article, price = product[0], product[1], product[2], product[3], product[4]
            total = price * quantity
            
            # Добавляем в список
            item = {
                'product_id': product_id,
                'name': name,
                'article': article,
                'price': price,
                'quantity': quantity,
                'total': total
            }
            self.current_order_items.append(item)
            
            # Добавляем в таблицу
            self.order_tree.insert('', 'end', values=(
                f"{name}",
                quantity,
                f"{price:,.2f} руб.",
                f"{total:,.2f} руб."
            ))
            
            # Обновляем итоги
            self.calculate_order_total()
            
            # Очищаем поля
            self.order_quantity_var.set("")
            
            self.log_message(f"Добавлен товар: {name} x {quantity}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении товара: {str(e)}")
    
    def remove_order_item(self):
        """Удаление выбранного товара из заявки"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления")
            return
        
        item_index = self.order_tree.index(selection[0])
        self.order_tree.delete(selection[0])
        self.current_order_items.pop(item_index)
        self.calculate_order_total()
    
    def clear_order(self):
        """Очистка заявки"""
        self.current_order_items.clear()
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        self.calculate_order_total()
    
    def calculate_order_total(self):
        """Расчет общей суммы заявки"""
        total = sum(item['total'] for item in self.current_order_items)
        
        # Расчет скидки
        discount = 0
        partner_name = self.order_partner_var.get()
        if partner_name:
            partner = self.db.get_partner_by_name(partner_name)
            if partner:
                discount = self.db.calculate_partner_discount(partner[0])
        
        discount_amount = total * discount
        final_total = total - discount_amount
        
        self.order_total_var.set(f"{total:,.2f} руб.")
        self.order_discount_var.set(f"{discount * 100:.1f}%")
        self.order_final_var.set(f"{final_total:,.2f} руб.")
    
    def create_order(self):
        """Создание заявки"""
        try:
            if not self.current_order_items:
                messagebox.showwarning("Предупреждение", "Добавьте товары в заявку")
                return
            
            partner_name = self.order_partner_var.get()
            manager_name_with_position = self.order_manager_var.get()
            
            if not partner_name or not manager_name_with_position:
                messagebox.showwarning("Предупреждение", "Выберите партнера и менеджера")
                return
            
            partner = self.db.get_partner_by_name(partner_name)
            employees = self.db.get_all_employees()
            manager_id = None
            for emp in employees:
                if f"{emp[1]} ({emp[8]})" == manager_name_with_position:
                    manager_id = emp[0]
                    break
            
            if not partner or not manager_id:
                messagebox.showerror("Ошибка", "Партнер или менеджер не найден")
                return
            
            total = sum(item['total'] for item in self.current_order_items)
            discount = self.db.calculate_partner_discount(partner[0])
            final_total = total * (1 - discount)
            
            order_id = self.db.create_order(
                partner[0],
                manager_id,
                self.current_order_items,
                final_total,
                self.delivery_method_var.get()
            )
            
            if order_id:
                messagebox.showinfo("Успех", f"Заявка #{order_id} успешно создана!\nСумма: {final_total:,.2f} руб.")
                self.clear_order()
                self.update_orders_list()
                self.log_message(f"Создана новая заявка #{order_id} для {partner_name}")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать заявку")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании заявки: {str(e)}")
    
    def update_orders_list(self):
        """Обновление списка заявок"""
        for item in self.orders_manage_tree.get_children():
            self.orders_manage_tree.delete(item)
        
        status_filter = self.filter_status_var.get()
        if status_filter == "все":
            orders = self.db.get_all_orders()
        else:
            orders = self.db.get_orders_by_status(status_filter)
        
        for order in orders:
            # order structure: [0]id, [1]partner_id, [2]manager_id, [3]order_date, [4]status, 
            # [5]products_list, [6]total_cost, [7]production_date, [8]prepayment_received,
            # [9]prepayment_date, [10]prepayment_amount, [11]full_payment_received,
            # [12]full_payment_date, [13]delivery_method, [14]completion_date, [15]notes,
            # [16]company_name, [17]manager_name
            order_id = order[0]
            order_date = order[3][:10]  # Берем только дату
            partner_name = order[16] or "Не указан"
            manager_name = order[17] or "Не указан"
            total_cost = f"{order[6]:,.2f}" if order[6] else "0.00"
            status = self.get_status_display_name(order[4])
            delivery = order[13] or "самовывоз"
            
            self.orders_manage_tree.insert('', 'end', values=(
                order_id, order_date, partner_name, manager_name, total_cost, status, delivery
            ))
    
    def get_status_display_name(self, status):
        """Получение отображаемого имени статуса"""
        status_names = {
            'created': 'Создана',
            'prepayment_received': 'Предоплата получена',
            'in_production': 'В производстве',
            'ready': 'Готово к отгрузке',
            'completed': 'Завершена',
            'cancelled': 'Отменена'
        }
        return status_names.get(status, status)
    
    def filter_orders(self, event=None):
        """Фильтрация заявок по статусу"""
        self.update_orders_list()
    
    def on_order_select(self, event):
        """Обработка выбора заявки"""
        selection = self.orders_manage_tree.selection()
        if selection:
            item = self.orders_manage_tree.item(selection[0])
            order_data = item['values']
            order_id = order_data[0]
            
            # Получаем полные данные заявки
            orders = self.db.get_all_orders()
            selected_order = None
            for order in orders:
                if order[0] == order_id:
                    selected_order = order
                    break
            
            if selected_order:
                details_text = f"""
ЗАЯВКА #{order_id}
Дата создания: {selected_order[3]}
Партнер: {selected_order[16]}
Менеджер: {selected_order[17]}
Статус: {self.get_status_display_name(selected_order[4])}
Способ доставки: {selected_order[13] or 'самовывоз'}
Общая стоимость: {selected_order[6]:,.2f} руб.

СОСТАВ ЗАЯВКИ:
"""
                try:
                    products_list = json.loads(selected_order[5])
                    for i, product in enumerate(products_list, 1):
                        details_text += f"{i}. {product['name']} ({product['article']}) - {product['quantity']} шт. x {product['price']:,.2f} руб. = {product['total']:,.2f} руб.\n"
                except:
                    details_text += "Ошибка загрузки состава заявки\n"
                
                if selected_order[15]:  # notes
                    details_text += f"\nПримечания: {selected_order[15]}"
                
                self.order_details_text.delete(1.0, tk.END)
                self.order_details_text.insert(1.0, details_text)
    
    def update_selected_order_status(self, new_status):
        """Обновление статуса выбранной заявки"""
        selection = self.orders_manage_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заявку для изменения статуса")
            return
        
        item = self.orders_manage_tree.item(selection[0])
        order_data = item['values']
        order_id = order_data[0]
        
        status_names = {
            'prepayment_received': 'Предоплата получена',
            'in_production': 'В производство',
            'ready': 'Готово к отгрузке',
            'completed': 'Завершена',
            'cancelled': 'Отменена'
        }
        
        status_display = status_names.get(new_status, new_status)
        
        if messagebox.askyesno("Подтверждение", f"Изменить статус заявки #{order_id} на '{status_display}'?"):
            success = self.db.update_order_status(order_id, new_status)
            if success:
                messagebox.showinfo("Успех", f"Статус заявки #{order_id} изменен")
                self.update_orders_list()
                self.log_message(f"Статус заявки #{order_id} изменен на '{new_status}'")
            else:
                messagebox.showerror("Ошибка", "Не удалось изменить статус заявки")
    
    def check_expired_orders(self):
        """Проверка просроченных заявок"""
        expired_count = self.db.check_expired_orders()
        if expired_count > 0:
            messagebox.showinfo("Информация", f"Автоматически отменено {expired_count} заявок с истекшим сроком предоплаты")
            self.update_orders_list()
        else:
            messagebox.showinfo("Информация", "Просроченных заявок не найдено")
    
    def import_data(self, data_type):
        """Импорт данных определенного типа"""
        file_map = {
            'material_types': ('Material_type_import.xlsx', self.db.import_material_types, "типов материалов"),
            'product_types': ('Product_type_import.xlsx', self.db.import_product_types, "типов продукции"),
            'products': ('Products_import.xlsx', self.db.import_products, "продукции"),
            'partners': ('Partners_import.xlsx', self.db.import_partners, "партнеров"),
            'sales': ('Partner_products_import.xlsx', self.db.import_sales_history, "истории продаж")
        }
        
        if data_type in file_map:
            filename, import_func, description = file_map[data_type]
            try:
                success = import_func(filename)
                if success:
                    self.log_message(f"✅ Успешно импортированы данные {description}")
                    # Обновление интерфейса
                    self.update_partners_list()
                    self.update_products_list()
                    self.update_stats_data()
                    self.update_order_form_data()
                    self.update_orders_list()
                else:
                    self.log_message(f"❌ Ошибка импорта {description}")
            except Exception as e:
                self.log_message(f"❌ Ошибка при импорте {description}: {str(e)}")
    
    def import_all_data(self):
        """Импорт всех данных"""
        self.log_message("Начало импорта всех данных...")
        
        import_types = ['material_types', 'product_types', 'products', 'partners', 'sales']
        
        for data_type in import_types:
            self.import_data(data_type)
        
        self.log_message("Импорт всех данных завершен!")
        messagebox.showinfo("Импорт", "Импорт всех данных завершен успешно!")
    
    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.import_log.insert(tk.END, f"{message}\n")
        self.import_log.see(tk.END)
        self.root.update()
    
    def import_initial_data(self):
        """Импорт начальных данных"""
        self.log_message("Запуск системы...")
        self.log_message("Инициализация базы данных завершена")

def main():
    root = tk.Tk()
    app = MasterPolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()