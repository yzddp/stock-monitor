from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

# 使用SQLite内存数据库
def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT (
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

db_conn = init_db()

# 股票价格获取函数（模拟数据，您可替换为真实接口）
def get_stock_price(symbol):
    import random
    return round(10 + random.random() * 20, 2)

@app.route('/')
def index():
    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width-scale=1.0">
        <title>股票监控系统 - 腾讯云Web托管</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .card {{
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                border: none;
            }}
            .card-header {{
                border-radius: 15px 15px 0 0 !important;
                border: none;
                font-weight: 600;
            }}
            th {{
                border-top: none;
                font-weight: 600;
            }}
            .profit {{ color: #28a745; font-weight: bold; }}
            .loss {{ color: #dc3545; font-weight: bold; }}
            .btn-primary {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                border: none;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="text-center text-white mb-4">
                <h1><i class="fas fa-chart-line me-2"></i>股票监控系统</h1>
                <p class="lead">腾讯云Web托管部署版 - 实时监控股票价格</p>
                <p class="textuted">服务器时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0"><i class="fas fa-plus-circle me-2"></i>添加监控股票</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g-2">
                                <div class="col-5">
                                    <inputtext" class="form-control" id="symbol" placeholder="股票代码">
                                </div>
                                <div class="col-5">
                                    <input type="text" class="form-control" id="name" placeholder="股票名称">
                                </div>
                                <div class="col-2">
                                    <button class="btn btn-primary w-100" onclick="addStock()">添加</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0"><i class="fas fa-exchange-alt me-2"></i>交易记录</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g">
                                <div class="col-3">
                                    <input type="text" class="form-control" id="tSymbol" placeholder="代码">
                                </div>
                                <div class="col-3">
                                    <select class="form-select" id="tType">
                                        <option value="buy">买入</option>
                                        <option value="sell">卖出</option>
                                    </select>
                                </div>
                                <div class="col-2">
                                    <input type="number" class="form-control" id="tPrice" placeholder="价格" step="0.01">
                                </div>
                                <div class="col-2">
                                    <input type="number" class="form-control" id="tQuantity" placeholder="数量">
                                </div>
                                <div class="col-2">
                                     class="btn btn-success w-100" onclick="addTransaction()">+</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                            <h5 class="mb-0"><i class="fas fa-chart-bar me-2"></i>系统状态</h5>
                            <button class="btn btn-light btn-sm" onclick="refreshAll()">
                                <i class="fas fa-sync-alt"></i> 刷新
                            </button>
                        </div>
                        <div class="card-body">
                            <div id="status">
                                <div class="alert alert-success">
                                    <i class="fas fa-check-circle me-"></i>
                                    <strong>系统运行正常</strong>
                                    <div class="mt-2">
                                        <small>最后刷新: <span id="lastUpdate">刚刚</span></small>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3">
                                <h6>API端点:</h6>
                                <ul class="list-unstyled small">
                                    <li><code>GET /api/stocks</code> - 股票列表</li>
                                    <li><code>POST /api/stock/add</code> - 添加股票</li>
                                    <li><code /api/portfolio</code> - 持仓信息</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header bg-warning text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-list me-2"></i>监控列表</h5>
                    <button class="btn btn-light btn-sm" onclick="loadStocks()">
                        <i class="fas fa-sync-alt me-1"></i> 刷新
                    </button>
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
                                <tr>
                                    <td colspan="7" class="text-center py-4">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">加载中...</span>
                                        </div>
                                        <p class="mt-2 text-muted">正在加载股票数据...</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header bg-purple text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>持仓和收益</h5>
                    <button class="btn btn-light btn-sm" onclick="loadPortfolio()">
                        <i class="fas fa-sync-alt me-1"></i> 刷新
                    </button>
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
                                <tr>
                                    <td colspan="7" class="text-center py-4">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">加载中...</span>
                                        </div>
                                        <p class="mt-2 text-muted">正在加载持仓数据...</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // 页面加载时初始化
            document.addEventListener('DOMContentLoaded', function() {
                loadStocks();
                loadPortfolio();
                setInterval(refreshAll, 30000); // 30秒自动刷新
            });

            function addStock() {
                const symbol = document.getElementById('symbol').value.trim();
                const name = document.getElementById('name').value.trim();
                
                if (!symbol) {
                    showAlert('请输入股票代码', 'warning');
                    return;
                }
                
                fetch('/api/stock/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({symbol: symbol, name: name || symbol})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('股票添加成功', 'success');
                        document.getElementById('symbol').value = '';
                        document.getElementById('name').value = '';
                        loadStocks();
                    } else {
                        showAlert(data.message || '添加失败', 'error');
                    }
                })
                .catch(error => {
                    showAlert('网络错误: ' + error, 'error');
                });
            }

            function addTransaction() {
                const symbol = document.getElementById('tSymbol').value.trim();
                const type = document.getElementById('tType').value;
                const price = document.getElementById('tPrice').value;
                const quantity = document.getElementById('tQuantity').value;
                
                if (!symbol || !price || !quantity) {
                    showAlert('请填写完整的交易信息', 'warning');
                    return;
                }
                
                fetch('/api/transaction/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        symbol: symbol,
                        type: type,
                        price: parseFloat(price),
                        quantity: parseInt(quantity)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('交易记录添加成功', 'success');
                        document.getElementById('tSymbol').value = '';
                        document.getElementById('tPrice').value = '';
                        document.getElementById('tQuantity').value = '';
                        loadPortfolio();
                    }
                })
                .catch(error => {
                    showAlert('网络错误: ' + error, 'error');
                });
            }

            function loadStocks() {
                fetch('/api/stocks')
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.getElementById('stockList');
                        let html = '';
                        
                        if (data.length === 0) {
                            html = '<tr><td colspan="7" class="text-center py-4 text-muted">暂无监控的股票</td></tr>';
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
                                        <td>
                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteStock(${stock.id})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `;
                            });
                        }
                        tbody.innerHTML = html;
                        updateStatus('数据加载成功');
                    })
                    .catch(error => {
                        console.error('加载股票失败:', error);
                        updateStatus('数据加载失败', 'error');
                    });
            }

            function loadPortfolio() {
                fetch('/api/portfolio')
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.getElementById('portfolioList');
                        let html = '';
                        
                        if (data.length === 0) {
                            html = '<tr><td colspan="7" class="text-center py-4 text-muted">暂无持仓记录</td></tr>';
                        } else {
                            data.forEach(item => {
                                const profitClass = item.profit >= 0 ? 'profit' : 'loss';
                                html += `
                                    <tr>
                                        <td>${item.symbol}</td>
                                        <td>${item.quantity}</td>
                                        <td>${item.avg_cost.toFixed(2)}</td>
                                        <td>${item.current_price ? item.current_price.toFixed(2) : 'N/A'}</td>
                                        <td>${item.current_value.toFixed(2)}</td>
                                        <td class="${profitClass}">${item.profit >= 0 ? '+' : ''}${item.profit.toFixed(2)}</td>
                                        <td class="${profitClass}">${item.profit_rate.toFixed(2)}%</td>
                                    </tr>
                                `;
                            });
                        }
                        tbody.innerHTML = html;
                    })
                    .catch(error => {
                        console.error('加载持仓失败:', error);
                    });
            }

            function deleteStock(stockId) {
                if (confirm('确定要删除这只股票吗？')) {
                    fetch('/api/stock/delete/' + stockId, {method: 'DELETE'})
                        .then(() => loadStocks());
                }
            }

            function refreshAll() {
                loadStocks();
                loadPortfolio();
                updateStatus('数据已刷新');
            }

            function updateStatus(message, type = 'success') {
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = `
                    <div class="alert alert-${type}">
                        <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle me-2"></i>
                        <strong>${message}</strong>
                        <div class="mt-2">
                            <small>最后刷新: <span id="lastUpdate">${new Date().toLocaleTimeString()}</span></small>
                        </div>
                    </div>
                `;
            }

            function showAlert(message, type) {
                const alert = document.createElement('div');
                alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
                alert.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
                alert.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(alert);
                setTimeout(() => alert.remove(), 3000);
            }
        </script>
    </body>
    </html>
    '''
    return html

# API路由
@app.route('/api/stocks')
def get_stocks():
    c = db_conn.cursor()
    c.execute('SELECT * FROM stocks ORDER BY created_at DESC')
    stocks = c.fetchall()
    
    result = []
    for stock in stocks:
        price = get_stock_price(stock[1])
        alert = False
        if price and stock[3] and price >= stock[3]:
            alert = True
        if price and stock[4] and price <= stock[4]:
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

@app.route('/api/stock/add', methods=['POST'])
def add_stock():
    data = request.json
    c = db_conn.cursor()
    
    # 检查是否已存在
    c.execute('SELECT id FROM stocks WHERE symbol = ?', (data['symbol'],))
    if c.fetchone():
        return jsonify({'success': False, 'message': '股票已存在'})
    
    c.execute('INSERT INTO stocks (symbol, name) VALUES (?, ?)', 
              (data['symbol'], data.get('name', data['symbol'])))
    db_conn.commit()
    return jsonify({'success': True, 'message': '添加成功'})

@app.route('/api/stock/delete/<int:stock_id>', methods=['DELETE'])
def delete_stock(stock_id):
    c = db_conn.cursor()
    c.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
    db_conn.commit()
    return jsonify({'success': True})

@app.route('/api/transaction/add', methods=['POST'])
def add_transaction():
    data = request.json
    c = db_conn.cursor()
    c.execute('INSERT INTO transactions (symbol, type, price, quantity) VALUES (?, ?, ?, ?)',
              (data['symbol'], data['type'], data['price'], data['quantity']))
    db_conn.commit()
    return jsonify({'success': True})

@app.route('/api/portfolio')
def get_portfolio():
    c = db_conn.cursor()
    c.execute('SELECT * FROM transactions')
    transactions = c.fetchall()
    
    holdings = {}
    for t in transactions:
        symbol = t[1]
        if symbol not in holdings:
            holdings[symbol] = {'quantity': 0, 'cost': 0}
        
        if t[2] == 'buy':
            holdings[symbol]['quantity'] += t[4]
            holdings[symbol]['cost'] += t[3] * t[4]
        else:
            holdings[symbol]['quantity'] -= t[4]
            holdings[symbol]['cost'] -= t[3] * t[4]
    
    result = []
    for symbol, data in holdings.items():
        if data['quantity'] > 0:
            current_price = get_stock_price(symbol)
            avg_cost = data['cost'] / data['quantity']
            current_value = current_price * data['quantity'] if current_price else 0
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

# 健康检查端点
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# 腾讯云Web托管配置 - 关键修改：监听80端口
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))  # 使用80端口
    app.run(host='0.0.0.0', port=port, debug=False)
