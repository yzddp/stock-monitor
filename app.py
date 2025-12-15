from flask import Flask, jsonify, request, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 使用SQLite内存数据库
def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    
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

# 股票价格接口 - 使用东方财富API
def get_stock_price(symbol):
    """
    使用东方财富API获取股票实时价格
    """
    try:
        import requests
        
        # 根据股票代码判断市场
        if symbol.startswith('6'):
            secid = f"1.{symbol}"  # 上海证券交易所
        elif symbol.startswith('0') or symbol.startswith('3'):
            secid = f"0.{symbol}"  # 深圳证券交易所
        else:
            return None
        
        # 东方财富API URL
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            'secid': secid,
            'fields': 'f43'  # 只获取最新价字段，简化请求
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('rc') == 0 and data.get('data'):
                current_price = data['data'].get('f43')
                if current_price is not None:
                    return float(current_price)
        
        return None
        
    except Exception as e:
        print(f"获取股票 {symbol} 价格错误: {e}")
        return None

@app.route('/')
def home():
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
            .card { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-4">📈 股票监控系统</h1>
            
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
            
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">📊 监控列表</h5>
                </div>
                <div class="card-body">
                    <table class="table">
                        <thead>
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
                            <tr><td colspan="7" class="text-center">正在加载...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0">💹 持仓和收益</h5>
                </div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>代码</th>
                                <th>持仓</th>
                                <th>成本</th>
                                <th>现价</th>
                                <th>市值</th>
                                <th>盈亏</th>
                            </tr>
                        </thead>
                        <tbody id="portfolioList">
                            <tr><td colspan="6" class="text-center">正在加载...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            function loadStocks() {
                fetch('/api/stocks')
                    .then(r => r.json())
                    .then(data => {
                        let html = '';
                        data.forEach(stock => {
                            html += `<tr>
                                <td>${stock.symbol}</td>
                                <td>${stock.name || '-'}</td>
                                <td>${stock.current_price || 'N/A'}</td>
                                <td>${stock.high_price || '-'}</td>
                                <td>${stock.low_price || '-'}</td>
                                <td>${stock.alert ? '⚠️预警' : '正常'}</td>
                                <td><button class="btn btn-sm btn-danger">删除</button></td>
                            </tr>`;
                        });
                        document.getElementById('stockList').innerHTML = html;
                    });
            }
            
            function addStock() {
                const symbol = document.getElementById('symbol').value;
                const name = document.getElementById('name').value;
                const high = document.getElementById('high').value;
                const low = document.getElementById('low').value;
                
                fetch('/api/stock/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({symbol, name, high_price: high, low_price: low})
                }).then(() => {
                    loadStocks();
                    document.getElementById('symbol').value = '';
                    document.getElementById('name').value = '';
                    document.getElementById('high').value = '';
                    document.getElementById('low').value = '';
                });
            }
            
            // 页面加载
            document.addEventListener('DOMContentLoaded', loadStocks);
        </script>
    </body>
    </html>
    '''
    return html

# API路由
@app.route('/api/stock/add', methods=['POST'])
def api_add_stock():
    data = request.json
    c = db_conn.cursor()
    c.execute('INSERT INTO stocks (symbol, name, high_price, low_price) VALUES (?, ?, ?, ?)',
              (data['symbol'], data.get('name'), data.get('high_price'), data.get('low_price')))
    db_conn.commit()
    return jsonify({'success': True})

@app.route('/api/stocks')
def api_get_stocks():
    c = db_conn.cursor()
    c.execute('SELECT * FROM stocks')
    stocks = c.fetchall()
    
    result = []
    for stock in stocks:
        price = get_stock_price(stock[1])
        alert = False
        if stock[3] and price and price >= stock[3]:
            alert = True
        if stock[4] and price and price <= stock[4]:
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

if __name__ == '__main__':
    app.run(debug=True)
