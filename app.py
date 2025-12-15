from flask import Flask, jsonify, request
import json
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# 使用SQLite内存数据库（重启会丢失数据，但部署最简单）
# 如果需要持久化，我们可以后续改进

# 初始化内存数据库
def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    
    # 创建股票监控表
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
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

# 全局数据库连接
db_conn = init_db()

# 你的股票价格接口函数
def get_stock_price(symbol):
    """
    这里替换成你的实际股票查询接口
    示例格式：返回一个浮点数，如 100.5
    现在先用模拟数据测试
    """
    import random
    # 模拟价格，你可以随时替换成你的接口
    return round(10 + random.random() * 10, 2)

@app.route('/')
def home():
    """首页，显示一个简单的界面"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>股票监控系统</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; background-color: #f8f9fa; }
            .card { margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .table-responsive { max-height: 400px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-4">📈 股票监控系统</h1>
            
            <!-- 添加股票 -->
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">➕ 添加监控股票</h5>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <input type="text" class="form-control" id="symbol" placeholder="股票代码" required>
                        </div>
                        <div class="col-md-3">
                            <input type="text" class="form-control" id="name" placeholder="股票名称（可选）">
                        </div>
                        <div class="col-md-2">
                            <input type="number" class="form-control" id="high" placeholder="监控高价">
                        </div>
                        <div class="col-md-2">
                            <input type="number" class="form-control" id="low" placeholder="监控低价">
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-primary w-100" onclick="addStock()">添加</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 股票列表 -->
            <div class="card">
                <div class="card-header bg-info text-white d-flex justify-content-between">
                    <h5 class="mb-0">📊 监控列表</h5>
                    <button class="btn btn-sm btn-light" onclick="loadStocks()">刷新</button>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>代码</th>
                                    <th>名称</th>
                                    <th>当前价</th>
                                    <th>高价提醒</th>
                                    <th>低价提醒</th>
                                    <th>状态</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="stockList">
                                <tr><td colspan="7" class="text-center py-3">正在加载...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- 交易记录 -->
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0">💹 添加交易记录</h5>
                </div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-md-2">
                            <input type="text" class="form-control" id="tSymbol" placeholder="股票代码">
                        </div>
                        <div class="col-md-2">
                            <select class="form-select" id="tType">
                                <option value="buy">买入</option>
                                <option value="sell">卖出</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <input type="number" class="form-control" id="tPrice" placeholder="价格" step="0.01">
                        </div>
                        <div class="col-md-2">
                            <input type="number" class="form-control" id="tQuantity" placeholder="数量">
                        </div>
                        <div class="col-md-3">
                            <input type="text" class="form-control" id="tNote" placeholder="备注（可选）">
                        </div>
                        <div class="col-md-1">
                            <button class="btn btn-success w-100" onclick="addTransaction()">+</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 持仓和收益 -->
            <div class="card">
                <div class="card-header bg-purple text-white d-flex justify-content-between">
                    <h5 class="mb-0">💰 持仓和收益</h5>
                    <button class="btn btn-sm btn-light" onclick="loadPortfolio()">刷新</button>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>代码</th>
                                    <th>持仓</th>
                                    <th>成本</th>
                                    <th>现价</th>
                                    <th>市值</th>
                                    <th>盈亏</th>
                                    <th>收益率</th>
                                </tr>
                            </thead>
                            <tbody id="portfolioList">
                                <tr><td colspan="7" class="text-center py-3">正在加载...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // 页面加载时获取数据
            document.addEventListener('DOMContentLoaded', function() {
                loadStocks();
                loadPortfolio();
                
                // 每30秒自动刷新
                setInterval(() => {
                    loadStocks();
                    loadPortfolio();
                }, 30000);
            });
            
            // 添加股票
            function addStock() {
                const symbol = document.getElementById('symbol').value;
                const name = document.getElementById('name').value;
                const high = document.getElementById('high').value;
                const low = document.getElementById('low').value;
                
                fetch('/api/stock/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        symbol: symbol,
                        name: name,
                        high_price: high || null,
                        low_price: low || null
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadStocks();
                        // 清空表单
                        document.getElementById('symbol').value = '';
                        document.getElementById('name').value = '';
                        document.getElementById('high').value = '';
                        document.getElementById('low').value = '';
                        alert('添加成功！');
                    }
                });
            }
            
            // 添加交易记录
            function addTransaction() {
                const symbol = document.getElementById('tSymbol').value;
                const type = document.getElementById('tType').value;
                const price = document.getElementById('tPrice').value;
                const quantity = document.getElementById('tQuantity').value;
                const note = document.getElementById('tNote').value;
                
                fetch('/api/transaction/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        symbol: symbol,
                        type: type,
                        price: parseFloat(price),
                        quantity: parseInt(quantity),
                        note: note
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadPortfolio();
                        // 清空表单
                        document.getElementById('tSymbol').value = '';
                        document.getElementById('tPrice').value = '';
                        document.getElementById('tQuantity').value = '';
                        document.getElementById('tNote').value = '';
                        alert('交易记录添加成功！');
                    }
                });
            }
            
            // 加载股票列表
            function loadStocks() {
                fetch('/api/stocks')
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.getElementById('stockList');
                        let html = '';
                        
                        if (data.length === 0) {
                            html = '<tr><td colspan="7" class="text-center py-3">暂无监控的股票</td></tr>';
                        } else {
                            data.forEach(stock => {
                                const alertClass = stock.alert ? 'table-warning' : '';
                                html += `
                                    <tr class="${alertClass}">
                                        <td><strong>${stock.symbol}</strong></td>
                                        <td>${stock.name || '-'}</td>
                                        <td>${stock.current_price ? stock.current_price.toFixed(2) : 'N/A'}</td>
                                        <td>${stock.high_price || '-'}</td>
                                        <td>${stock.low_price || '-'}</td>
                                        <td>${stock.alert ? '<span class="badge bg-danger">预警</span>' : '<span class="badge bg-success">正常</span>'}</td>
                                        <td><button class="btn btn-sm btn-danger" onclick="deleteStock(${stock.id})">删除</button></td>
                                    </tr>
                                `;
                            });
                        }
                        tbody.innerHTML = html;
                    });
            }
            
            // 加载持仓
            function loadPortfolio() {
                fetch('/api/portfolio')
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.getElementById('portfolioList');
                        let html = '';
                        
                        if (data.length === 0) {
                            html = '<tr><td colspan="7" class="text-center py-3">暂无持仓记录</td></tr>';
                        } else {
                            data.forEach(item => {
                                const profitClass = item.profit >= 0 ? 'text-success' : 'text-danger';
                                html += `
                                    <tr>
                                        <td>${item.symbol}</td>
                                        <td>${item.quantity}</td>
                                        <td>${item.avg_cost.toFixed(2)}</td>
                                        <td>${item.current_price ? item.current_price.toFixed(2) : 'N/A'}</td>
                                        <td>${item.current_value.toFixed(2)}</td>
                                        <td class="${profitClass}">${item.profit.toFixed(2)}</td>
                                        <td class="${profitClass}">${item.profit_rate.toFixed(2)}%</td>
                                    </tr>
                                `;
                            });
                        }
                        tbody.innerHTML = html;
                    });
            }
            
            // 删除股票
            function deleteStock(id) {
                if (confirm('确定要删除这只股票吗？')) {
                    fetch('/api/stock/delete/' + id, { method: 'POST' })
                        .then(() => loadStocks());
                }
            }
        </script>
    </body>
    </html>
    '''
    return html

# API：添加股票
@app.route('/api/stock/add', methods=['POST'])
def api_add_stock():
    data = request.json
    c = db_conn.cursor()
    
    c.execute('''
        INSERT INTO stocks (symbol, name, high_price, low_price) 
        VALUES (?, ?, ?, ?)
    ''', (data['symbol'], data.get('name', ''), 
          data.get('high_price'), data.get('low_price')))
    
    db_conn.commit()
    return jsonify({'success': True, 'id': c.lastrowid})

# API：获取股票列表
@app.route('/api/stocks', methods=['GET'])
def api_get_stocks():
    c = db_conn.cursor()
    c.execute('SELECT * FROM stocks')
    stocks = c.fetchall()
    
    result = []
    for stock in stocks:
        price = get_stock_price(stock[1])  # symbol是第2列
        alert = False
        
        if stock[3] and price and price >= stock[3]:  # 检查高价
            alert = True
        if stock[4] and price and price <= stock[4]:  # 检查低价
            alert = True
        
        result.append({
            'id': stock[0],
            'symbol': stock[1],
            'name': stock[2],
            'current_price': price,
            'high_price': stock[3],
            'low_price': stock[4],
            'alert': alert
        })
    
    return jsonify(result)

# API：添加交易记录
@app.route('/api/transaction/add', methods=['POST'])
def api_add_transaction():
    data = request.json
    c = db_conn.cursor()
    
    c.execute('''
        INSERT INTO transactions (symbol, type, price, quantity) 
        VALUES (?, ?, ?, ?)
    ''', (data['symbol'], data['type'], data['price'], data['quantity']))
    
    db_conn.commit()
    return jsonify({'success': True})

# API：获取持仓
@app.route('/api/portfolio', methods=['GET'])
def api_get_portfolio():
    c = db_conn.cursor()
    c.execute('SELECT * FROM transactions')
    transactions = c.fetchall()
    
    # 计算持仓
    holdings = {}
    for t in transactions:
        symbol = t[1]  # symbol
        if symbol not in holdings:
            holdings[symbol] = {'quantity': 0, 'cost': 0}
        
        if t[2] == 'buy':  # type
            holdings[symbol]['quantity'] += t[4]  # quantity
            holdings[symbol]['cost'] += t[3] * t[4]  # price * quantity
        else:  # sell
            holdings[symbol]['quantity'] -= t[4]
            holdings[symbol]['cost'] -= t[3] * t[4]
    
    result = []
    for symbol, data in holdings.items():
        if data['quantity'] > 0:
            current_price = get_stock_price(symbol)
            avg_cost = data['cost'] / data['quantity']
            current_value = current_price * data['quantity']
            profit = current_value - data['cost']
            profit_rate = (profit / data['cost']) * 100 if data['cost'] > 0 else 0
            
            result.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'avg_cost': round(avg_cost, 2),
                'current_price': current_price,
                'current_value': round(current_value, 2),
                'profit': round(profit, 2),
                'profit_rate': round(profit_rate, 2)
            })
    
    return jsonify(result)

# API：删除股票
@app.route('/api/stock/delete/<int:stock_id>', methods=['POST'])
def api_delete_stock(stock_id):
    c = db_conn.cursor()
    c.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
    db_conn.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
