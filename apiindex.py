from flask import Flask, render_template_string, request, jsonify
import sqlite3
import json
from datetime import datetime
import os

# 简化版本，避免复杂依赖
app = Flask(__name__)

# 使用SQLite内存数据库（简化）
DB_PATH = "/tmp/stock_monitor.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 创建股票表
    c.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            high_price REAL,
            low_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建交易记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            type TEXT,
            price REAL,
            quantity INTEGER,
            note TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 模拟股票价格获取
def get_stock_price(symbol):
    """
    这里替换成你的实际股票接口
    示例：返回模拟数据
    """
    import random
    return round(10 + random.random() * 5, 2)

@app.route('/api/stock/add', methods=['POST'])
def add_stock():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO stocks (symbol, name, high_price, low_price) 
        VALUES (?, ?, ?, ?)
    ''', (data['symbol'], data.get('name', ''), 
          data.get('high_price'), data.get('low_price')))
    
    conn.commit()
    stock_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': stock_id})

@app.route('/api/stocks')
def get_stocks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM stocks')
    stocks = c.fetchall()
    
    result = []
    for stock in stocks:
        price = get_stock_price(stock[1])  # symbol是第2列
        result.append({
            'id': stock[0],
            'symbol': stock[1],
            'name': stock[2],
            'current_price': price,
            'high_price': stock[3],
            'low_price': stock[4],
            'alert': price and ((stock[3] and price >= stock[3]) or 
                               (stock[4] and price <= stock[4]))
        })
    
    conn.close()
    return jsonify(result)

@app.route('/api/transaction/add', methods=['POST'])
def add_transaction():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO transactions (symbol, type, price, quantity, note) 
        VALUES (?, ?, ?, ?, ?)
    ''', (data['symbol'], data['type'], float(data['price']), 
          int(data['quantity']), data.get('note', '')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/portfolio')
def get_portfolio():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM transactions')
    transactions = c.fetchall()
    
    portfolio = {}
    for t in transactions:
        symbol = t[1]  # symbol
        if symbol not in portfolio:
            portfolio[symbol] = {'total_quantity': 0, 'total_cost': 0}
        
        if t[2] == 'buy':  # type
            portfolio[symbol]['total_quantity'] += t[4]  # quantity
            portfolio[symbol]['total_cost'] += t[3] * t[4]  # price * quantity
        else:  # sell
            portfolio[symbol]['total_quantity'] -= t[4]
            portfolio[symbol]['total_cost'] -= t[3] * t[4]
    
    result = []
    for symbol, data in portfolio.items():
        if data['total_quantity'] > 0:
            current_price = get_stock_price(symbol)
            avg_cost = data['total_cost'] / data['total_quantity']
            current_value = current_price * data['total_quantity']
            profit = current_value - data['total_cost']
            profit_rate = (profit / data['total_cost']) * 100 if data['total_cost'] > 0 else 0
            
            result.append({
                'symbol': symbol,
                'quantity': data['total_quantity'],
                'avg_cost': round(avg_cost, 2),
                'current_price': current_price,
                'current_value': round(current_value, 2),
                'profit': round(profit, 2),
                'profit_rate': round(profit_rate, 2)
            })
    
    conn.close()
    return jsonify(result)

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>股票监控系统</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .profit { color: green; }
            .loss { color: red; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>股票监控系统</h1>
            <p>这是一个简化的股票监控系统，请在前端页面中替换股票价格接口。</p>
            <p>API已就绪，可以使用以下接口：</p>
            <ul>
                <li>GET /api/stocks - 获取股票列表</li>
                <li>POST /api/stock/add - 添加股票</li>
                <li>POST /api/transaction/add - 添加交易</li>
                <li>GET /api/portfolio - 获取持仓</li>
            </ul>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

# Vercel需要这个
def handler(request):
    return app(request)