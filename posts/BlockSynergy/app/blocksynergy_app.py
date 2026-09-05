from flask import Flask, flash, url_for, render_template, request, Response, send_file, jsonify, redirect, session
from Blockchain import Blockchain, Wallet
import json
from io import BytesIO
from werkzeug.wsgi import wrap_file
from flask_session import Session
from ecdsa import SigningKey, NIST256p, VerifyingKey
import requests
import argparse
import threading
import subprocess
import platform, socket, psutil, time
from urllib.parse import urlparse
import ipaddress
import uuid 

app = Flask(__name__, template_folder="templates", static_folder='static')

blockchain = Blockchain()
wallet = None

@app.before_request
def ensure_session():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

def session_wallet():
    try:
        wallet_data = session.get('wallet')
        if not wallet_data or 'private_key' not in wallet_data or 'public_key' not in wallet_data:
            return None

        wallet = Wallet()
        wallet.priv_key = SigningKey.from_string(bytes.fromhex(wallet_data['private_key']), curve=NIST256p)
        wallet.pub_key = VerifyingKey.from_string(bytes.fromhex(wallet_data['public_key']), curve=NIST256p)
        wallet.address = wallet_data['public_key']
        return wallet
    except Exception as e:
        flash(f"Error in session_wallet: {e}", 'error')
        return None


@app.route('/')
def home():
    try:
        return render_template('home.html')
    except Exception as e:
        flash(f"Error in home route: {e}", 'error')
        return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    try:
        return render_template("dashboard.html", page="dashboard")
    except Exception as e:
        flash(f"Error in dashboard route: {e}", 'error')
        return redirect(url_for('home'))

@app.route('/dashboard/wallet', methods=['GET', 'POST'])
def wallet():
    try:
        action = request.form.get("action") or request.args.get("action")

        if action == "load":
            if 'file' not in request.files:
                flash("No file uploaded", 'error')
            else:
                file = request.files.get("file")
                try:
                    wallet = Wallet()
                    wallet.load_wallet(file.stream)
                    session['wallet'] = {
                        'private_key': wallet.priv_key.to_string().hex(),
                        'public_key': wallet.pub_key.to_string().hex()
                    }
                    flash("Wallet loaded successfully!", 'success')
                except (json.JSONDecodeError, UnicodeDecodeError):
                    flash("Invalid file format. Please upload a valid wallet file.", 'error')

        elif action == "create":
            filename = request.form.get("filename") or request.args.get("filename")
            if not filename:
                flash("Please enter a filename to save the wallet.", 'error')
            else:
                wallet_created = Wallet()
                data = wallet_created.create_wallet()
                json_data = json.dumps(data).encode('utf-8')
                memory_file = BytesIO(json_data)
                flash("Wallet created successfully! Downloading the file...", 'success')
                return send_file(memory_file, as_attachment=True, mimetype="application/json", download_name=filename + ".json")

        return render_template('dashboard.html', page="wallet")
    except Exception as e:
        flash(f"Error in wallet route: {e}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/dashboard/deposit', methods=['GET', 'POST'])
def deposit():
    try:
        return render_template("dashboard.html", page="deposit")
    except Exception as e:
        flash(f"Error in deposit route: {e}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/dashboard/withdraw', methods=['GET', 'POST'])
def withdraw():
    try:
        return render_template("dashboard.html", page="withdraw")
    except Exception as e:
        flash(f"Error in withdraw route: {e}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/dashboard/info', methods=['GET', 'POST'])
def wallet_info():
    try:
        wallet = session_wallet()
        if wallet:
            address = wallet.address
            pub = wallet.pub_key.to_string().hex()
            priv = wallet.priv_key.to_string().hex()
            bal = wallet.calc_balance(blockchain.chain, blockchain.pending_transactions)
            return render_template("dashboard.html", page="wallet_info", address=address, pub=pub, priv=priv, bal=bal)
        else:
            flash("No Wallet loaded", 'error')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"Error in wallet_info route: {e}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/dashboard/blockchain', methods= ['GET', 'POST'])
def blockchain_dashboard():
    return render_template("dashboard.html", page="blockchain")

@app.route('/dashboard/txn', methods= ['GET', 'POST'])
def blockchain_txn():
    wallet = session_wallet()

    if wallet != None:
        action = request.form.get("action") or request.args.get("action")
        if action == "send":
            receiver = request.form.get("receiver") or request.args.get("receiver")
            amount = request.form.get("amount") or request.args.get("amount")

            if receiver and amount:
                data = wallet.txn(blockchain, receiver, int(amount))
                if receiver == wallet.address:
                    flash("You cant send coins to yourself")

                elif amount.isnumeric():
                    if int(amount) <= wallet.balance:
                        blockchain.pending_transactions.append(data)

                        flash("Transaction has been added to pending Transactions", 'success')

                        for node in blockchain.nodes:  
                            requests.post(node + "/broadcast_transaction", json=data)

                        print(f"Pending Transactions: {blockchain.pending_transactions}")
                    else:
                        flash("Not enough coins!", 'error')
                else:
                    flash("Enter a valid number")
            else:
                flash("Receiver or amount missing!", 'error')

        return render_template("dashboard.html", page="txn")
    else:
        flash("No Wallet loaded!")
        return redirect(request.referrer or url_for('dashboard'))

@app.route('/dashboard/txn_history', methods= ['GET', 'POST'])
def txn_history():
    wallet = session_wallet()
    
    if wallet != None:
        
        txnhistory = []
        if 'wallet' in session:
            if wallet.history != []:
                txnhistory = wallet.history(blockchain.chain)
            else:  
                txnhistory = []     
        else:
            txnhistory = []

        return render_template("dashboard.html", page="txn_history", history=txnhistory)
    else:
        flash("No Wallet loaded!")
        return redirect(request.referrer or url_for('dashboard'))
    
@app.route('/dashboard/pending_txn', methods= ['GET', 'POST'])
def pending_txn():
    wallet = session_wallet()

    if wallet != None:
        data = []
        for txn in blockchain.pending_transactions:
            if txn['sender'] == wallet.address:
                data.append(txn)
        
        return render_template("dashboard.html", page="pending_txn", pendingtxn=data)
    else:
        flash("No Wallet loaded")
        return redirect(request.referrer or url_for('dashboard'))
    
  
@app.route('/dashboard/vip/nodes', methods= ['GET', 'POST'])
def nodes_management():
    wallet = session_wallet()
    if wallet != None:

        balance = wallet.calc_balance(blockchain.chain, blockchain.pending_transactions)
        if balance < 10:
            flash("Permission Denied")
            return redirect(request.referrer or url_for('dashboard'))
        else:
            nodes = list(blockchain.nodes)
            action = request.form.get("action") or request.args.get("action")

            if action == "register":
                node_url = request.form.get('node')
                if is_internal_address(node_url):
                    flash("Invalid URL or localhost!")
                else:
                    blockchain.register_nodes(node_url)
                    print(blockchain.nodes)
                    flash("Node registered!")

            elif action == "download_blockchain" or action == "download_app":
                flash("Currently unavailable!")
            
            return render_template("dashboard.html", page="nodes", nodes=nodes)
    else:
        flash("No Wallet loaded")
        return redirect(request.referrer or url_for('dashboard'))

@app.route('/dashboard/vip/nodes/test_node/<node_id>', methods= ['GET', 'POST'])
def test_node(node_id):
    wallet = session_wallet()
    if wallet != None:

        balance = wallet.calc_balance(blockchain.chain, blockchain.pending_transactions)
        if balance < 10:
            flash("Permission Denied")
            return redirect(request.referrer or url_for('dashboard'))
        else:    
            try:
                node_url = blockchain.nodes[int(node_id)]
                r = requests.get(node_url, timeout=8)
                if 'application/json' in r.headers.get('Content-Type', ''):
                    return jsonify(r.json())
                else:
                    return r.text  
                
            except (IndexError, ValueError, requests.exceptions.RequestException):
                flash("Node not reachable or invalid ID!")
                return render_template("dashboard.html", page="nodes")
    else:
        flash("No Wallet loaded")
        return redirect(request.referrer or url_for('dashboard')) 

@app.route('/dashboard/vip/smart_contracts', methods= ['GET', 'POST'])
def smart_contracts():
    wallet = session_wallet()
    if wallet != None:
        balance = wallet.calc_balance(blockchain.chain, blockchain.pending_transactions)
        if balance < 10:
            flash("Permission Denied")
            return redirect(request.referrer or url_for('dashboard'))
        return render_template("dashboard.html", page="smart_contracts") 
    else:
        flash("No Wallet loaded")
        return redirect(request.referrer or url_for('dashboard'))
    
@app.route('/dashboard/api', methods= ['GET', 'POST'])
def api_endpoints():
    apis = {
        'Blockchain': '/blockchain',
        'Nodes': '/nodes',
        'Mining Data': '/mining_data',
        'Submit Block': '/submit_block',
        'Broadcast Transaction': '/broadcast_transaction'
    }
    return render_template("dashboard.html", page="api", apis=apis)

@app.route("/admin", methods = ['GET', 'POST'])
def admin_dashboard():
    if is_admin() == True:
        return render_template("admin_dashboard.html", page="dashboard", chain=blockchain.chain, nodes=blockchain.nodes)
    else:
        return "Permission Denied", 403

@app.route('/admin/nodes/add_node', methods= ['GET', 'POST'])
def admin_add_node(): 
    action = request.form.get("action") or request.args.get("action")

    if action == "register":
        node_url = request.form.get('node')
        if is_internal_address(node_url):
            flash("Invalid URL or localhost!")
        else:
            blockchain.register_nodes(node_url)
            print(blockchain.nodes)
            flash("Node registered!")
    return render_template("admin_dashboard.html", page="add_node")

@app.route("/admin/nodes/manage", methods = ['GET', 'POST'])
def admin_manage_nodes():
    if is_admin() == True:
        outputs = {} 
        action = request.form.get("action") or request.args.get("action")
        nodes = blockchain.nodes
        if action == 'ping_node':
            target = request.form.get("target") or request.args.get("target")
            try:
                ip = extract_ip_from_url(target)
                output = subprocess.check_output(f"ping -w 4{ip}", shell=True, stderr=subprocess.STDOUT, encoding="cp850", text=True)
            except subprocess.CalledProcessError as e:
                output = e.output

            for node in nodes:
                if node == target:
                    outputs[node] = output
                else:
                    outputs[node] = ""
        elif action == 'resync':
            blockchain.sync()
            for node in nodes:
                outputs[node] = ""
        elif action == 'remove_node':
            index = request.form.get("node_index") or request.args.get("node_index")
            index = int(index)
            blockchain.nodes.pop(index)
            flash(f"Removing node {index}")

            nodes = blockchain.nodes
            for node in nodes:
                outputs[node] = ""
            return render_template("admin_dashboard.html", page="manage_nodes", outputs=outputs, nodes=nodes)
        else:
            for node in nodes:
                outputs[node] = ""
        return render_template("admin_dashboard.html", page="manage_nodes", outputs=outputs, nodes=nodes)
    else:
        return "Permission Denied", 403

@app.route("/admin/blockchain", methods = ['GET', 'POST'])
def admin_blockchain_backup_restore():
    if is_admin() == True:
        output = ""
        action = request.form.get("action") or request.args.get("action")
        if action == 'backup':
            name = request.form.get("filename")
            data = blockchain.chain
            json_data = json.dumps(data).encode('utf-8')
            memory_file = BytesIO(json_data)

            return send_file(memory_file, as_attachment=True, mimetype="application/json", download_name=f"{name}.json")
        elif action == "restore":
            if 'file' not in request.files:
                return "Keine Datei hochgeladen", 400
            else:
                file = request.files.get("file")
                try:
                    blockchain.restore_chain(file.stream)

                    flash("Blockchain restored", 'success')
                except json.JSONDecodeError:
                    flash("Ungültiges Format", 'error')

        return render_template("admin_dashboard.html", page="blockchain")
    else:
        return "Permission Denied", 403

@app.route("/admin/blockchain/view", methods = ['GET', 'POST'])
def admin_blockchain_view():
    if is_admin() == True:
        return render_template("admin_dashboard.html", page="view_blockchain", chain=blockchain.chain)
    else:
        return "Permission Denied", 403
    
@app.route("/admin/blockchain/validate", methods = ['GET', 'POST'])
def admin_validate_chain():
    if is_admin() == True:
        output = ""
        action = request.form.get("action") or request.args.get("action")
        if action == "validate":
            if blockchain.validation(blockchain.chain):
                output = "Blockchain is valid!"
            else: 
                output = "Blockchain invalid!"
        return render_template("admin_dashboard.html", page="validate_blockchain", output=output)
    else:
        return "Permission Denied", 403
    
@app.route("/admin/txn/pending", methods = ['GET', 'POST'])
def admin_pending_transactions():
    if is_admin() == True:
        return render_template("admin_dashboard.html", page="pending_txn", pendingtxn=blockchain.pending_transactions)
    else:
        return "Permission Denied", 403
    
@app.route("/admin/txn/history", methods = ['GET', 'POST'])
def admin_transaction_history():
    if is_admin() == True:
        txnhistory = blockchain.txn_history(blockchain.chain)
        return render_template("admin_dashboard.html", page="txn_history", txnhistory=txnhistory)
    else:
        return "Permission Denied", 403
    
@app.route("/admin/system", methods = ['GET', 'POST'])
def admin_systeminfo():
    if is_admin() == True:
        action = request.form.get("action") or request.args.get("action")
        output = ""
        if action == "systeminfo":
            boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))
            sysinfo = {
                "Hostname": socket.gethostname(),
                "IP Address": socket.gethostbyname(socket.gethostname()),
                "OS": platform.system() + " " + platform.release(),
                "Architecture": platform.machine(),
                "Uptime": boot_time,
                "CPU Cores": psutil.cpu_count(logical=True),
                "CPU Usage": f"{psutil.cpu_percent()}%",
                "RAM": f"{round(psutil.virtual_memory().used / (1024**2))} MB / {round(psutil.virtual_memory().total / (1024**2))} MB",
                "Disk": f"{round(psutil.disk_usage('/').used / (1024**3), 1)} GB / {round(psutil.disk_usage('/').total / (1024**3), 1)} GB",
                "Python Version": platform.python_version()
            }
            print(output)
            # Umwandeln in eine Liste von Schlüssel-Wert-Paaren
            output = [{"key": k, "value": v} for k, v in sysinfo.items()]
        return render_template("admin_dashboard.html", page="system", sysinfo=output)
    else:
        return "Permission Denied", 403
    
def is_internal_address(url):
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        ip = socket.gethostbyname(host)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_loopback
    except Exception as e:
        flash(f"Error in is_internal_address: {e}", 'error')
        return True

def extract_ip_from_url(url):
    try:
        if url.startswith("http://"):
            url = url[len("http://"):]

        elif url.startswith("https://"):
            url = url[len("https://"):]

        ip = url.split('/')[0]
        ip = ip.split(':')[0]
        return ip
    except Exception as e:
        flash(f"Error in extract_ip_from_url: {e}", 'error')
        return None

def is_admin():
    try:
        return request.remote_addr == "127.0.0.1"
    except Exception as e:
        flash(f"Error in is_admin: {e}", 'error')
        return False

@app.route("/blockchain", methods = ['POST', 'GET'])
def blockchain_api():
    return jsonify(blockchain.chain), 200

@app.route("/nodes", methods = ['POST', 'GET'])
def nodes_api():
    return jsonify(blockchain.nodes), 200

@app.route("/broadcast_transaction", methods = ['GET', 'POST'])
def broadcast_api():

    if request.method == "POST":

        data = request.json

        if data not in blockchain.pending_transactions:
            print(f"Received Transaction: {data}")
            blockchain.pending_transactions.append(data) 
            print(f"Pending Transactions {blockchain.pending_transactions}")
        else:
            return "Transaction already pending"

        return "Added!"

@app.route("/mining_data", methods = ['GET'])
def mining_data_api():

    if request.method == "GET":

        data = []
        tx_data = []

        if blockchain.pending_rewards != [] and blockchain.pending_transactions != []:
            tx_data.insert(0, blockchain.pending_rewards[0])         
            tx_data.extend(blockchain.pending_transactions)
            
        elif blockchain.pending_transactions != []:
            tx_data.extend(blockchain.pending_transactions)

        if tx_data:
            data = {
                "blockchain": blockchain.chain,
                "pending_transactions": tx_data,
                "latest_block": blockchain.get_latest_block(),
                "difficulty": blockchain.difficulty
            }

            return data, 200
        else:
            return "No Transactions", 400
        
@app.route("/submit_block", methods = ['GET', 'POST'])
def submit():

    if request.method == 'POST':

        data = request.json

        block = data['block']
        address = data['address']

        print(f"Block received: {block}")
        
        if blockchain.validate_block(block) == True:

            print("Adding Miner Reward!")
            blockchain.reward_miner(address)

            blockchain.chain.append(block)
            print("Block added to Blockchain")

            blockchain.sync()
            print("Synchronizing chain!")
            return "Added!"
        else:
            print("Block is not being added to the Blockchain!")

            return "Not Added! Make sure the block meets the requirements"

def autosync():
    blockchain.sync()
    threading.Timer(10, autosync).start()

def simulate():
    blockchain.simulate_txn()
    threading.Timer(5, simulate).start()

if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--portarg", type=int, default=8080, help="Port for Flask server")
        args = parser.parse_args()
        port = args.portarg
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_FILE_DIR"] = f"/var/lib/staging/smart_contracts/sessions"
        app.secret_key = f"BlockChainKey_{port}" 

        sync_thread = threading.Thread(target=autosync, daemon=True)
        sync_thread.start()

        simulate_thread = threading.Thread(target=simulate, daemon=True)
        simulate_thread.start()

        Session(app)
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        flash(f"Error in main: {e}", 'error')






