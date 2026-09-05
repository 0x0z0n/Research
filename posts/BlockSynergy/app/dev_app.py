from flask import Flask, flash, url_for, render_template, request, Response, send_file, jsonify, redirect, session
from dev_blockchain import Blockchain, Wallet, Contract
import json
from io import BytesIO
from werkzeug.wsgi import wrap_file
from flask_session import Session
from ecdsa import SigningKey, NIST256p, VerifyingKey
import requests
import argparse
import threading
import os
from urllib.parse import urlparse
import hashlib
from contract import ContractEngine
from collections import OrderedDict
from markupsafe import Markup

app = Flask(__name__, template_folder="templates", static_folder='static')

blockchain = Blockchain()
blockchain_contract = Contract()
wallet = None


def session_wallet():
    try:
        if 'wallet' not in session:
            return None

        wallet_data = session['wallet']
        wallet = Wallet()
        wallet.priv_key = SigningKey.from_string(bytes.fromhex(wallet_data['private_key']), curve=NIST256p)
        wallet.pub_key = VerifyingKey.from_string(bytes.fromhex(wallet_data['public_key']), curve=NIST256p)
        wallet.address = wallet_data['public_key']
        return wallet
    except Exception as e:
        flash(f"Error in session_wallet: {e}", 'error')
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect(url_for('dashboard'))
    
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    try:
        sender = "Developer"
        contract_list = blockchain_contract.contracts
        action = request.form.get("action") or request.args.get("action")
        selected_id = request.args.get("id")
        contract = None
        contract_id = session.get("current_contract_id")

        if contract_id is not None:
            try:
                contract_data = blockchain_contract.load_contract(contract_id)
                contract = ContractEngine(contract_data)
                logfile = contract.return_logs()
            except (KeyError, IndexError):
                session.pop("current_contract_id", None)

        if selected_id:
            if blockchain_contract.contracts.get(int(selected_id)) is None:
                flash("No Contract with this id found", 'error')
                selected_contract = None
                logfile = None
            else:
                selected_contract = blockchain_contract.load_contract(selected_id)
                contract = ContractEngine(selected_contract)
                logfile = contract.return_logs()
        else:
            selected_contract = None
            logfile = None

        if action == "upload_contract":
            if 'contract_file' not in request.files:
                flash("No File selected", 'error')
            else:
                file = request.files.get("contract_file")
                try:
                    contract_data = json.load(file, object_pairs_hook=OrderedDict)
                    contract_id = blockchain_contract.save_contract(contract_data)
                    contract = ContractEngine(contract_data)
                    session["current_contract_id"] = contract_id
                    flash("Contract loaded", 'success')
                except (json.JSONDecodeError, UnicodeDecodeError):
                    flash("Invalid format", 'error')

        if action == "load_contract":
            try:
                contract_id = request.form.get("id") or request.args.get("id")
                contract_data = blockchain_contract.load_contract(contract_id)
                contract = ContractEngine(contract_data)
                logfile = contract.return_logs()
                session["current_contract_id"] = contract_id
            except Exception as e:
                flash(f"Error loading contract: {e}", 'error')

        if action == "contract_mint" and contract:
            try:
                amount = request.form.get("contract_mint_amount") or request.args.get("contract_mint_amount")
                resp = contract.mint(sender, int(amount))
                if resp == False:
                    flash("Error minting contract", 'error')
            except Exception as e:
                flash(f"Error minting contract: {e}", 'error')

        if action == "contract_burn" and contract:
            try:
                amount = request.form.get("contract_burn_amount") or request.args.get("contract_burn_amount")
                resp = contract.burn(sender, int(amount))
                if resp == False:
                    flash("Error burning contract", 'error')
            except Exception as e:
                flash(f"Error burning contract: {e}", 'error')

        if action == "contract_claim" and contract:
            try:
                resp = contract.claim(sender)
                if resp == False:
                    flash("Error claiming contract", 'error')
            except Exception as e:
                flash(f"Error claiming contract: {e}", 'error')

        if action == "contract_vote" and contract:
            try:
                option = request.form.get("contract_vote_option") or request.args.get("contract_vote_option")
                resp = contract.vote(sender, option)
                if resp == False:
                    flash("Error voting on contract", 'error')
            except Exception as e:
                flash(f"Error voting on contract: {e}", 'error')

        if action is not None and contract and contract_id is not None:
            try:
                blockchain_contract.update_contract(contract_id, contract.return_updated_contract())
                selected_contract = blockchain_contract.load_contract(contract_id)
                logfile = contract.return_logs()
            except Exception as e:
                flash(f"Error updating contract: {e}", 'error')

        return render_template("dashboard.html", page="smart_contracts", contracts=contract_list, contract_data=selected_contract, logfile=logfile)
    except Exception as e:
        flash(f"Error in dashboard: {e}", 'error')
        return redirect(url_for('dashboard'))


@app.template_filter('tojson_preserve')
def tojson_preserve(obj):
    return Markup(json.dumps(obj, indent=2, sort_keys=False))


@app.route("/blockchain", methods=['POST', 'GET'])
def blockchain_api():
    try:
        return jsonify(blockchain.chain), 200
    except Exception as e:
        flash(f"Error in blockchain API: {e}", 'error')
        return jsonify({"error": "Unable to fetch blockchain data"}), 500


@app.route("/nodes", methods=['POST', 'GET'])
def nodes_api():
    try:
        return jsonify(blockchain.nodes), 200
    except Exception as e:
        flash(f"Error in nodes API: {e}", 'error')
        return jsonify({"error": "Unable to fetch nodes data"}), 500


@app.route("/broadcast_transaction", methods=['GET', 'POST'])
def broadcast_api():
    try:
        if request.method == "POST":
            data = request.json
            if data not in blockchain.pending_transactions:
                blockchain.pending_transactions.append(data)
                return "Added!"
            else:
                return "Transaction already pending"
    except Exception as e:
        flash(f"Error in broadcast API: {e}", 'error')
        return "Error processing transaction", 500


@app.route("/mining_data", methods=['GET'])
def mining_data_api():
    try:
        data = []
        tx_data = []

        if blockchain.pending_rewards and blockchain.pending_transactions:
            tx_data.insert(0, blockchain.pending_rewards[0])
            tx_data.extend(blockchain.pending_transactions)
        elif blockchain.pending_transactions:
            tx_data.extend(blockchain.pending_transactions)

        if tx_data:
            data.append(blockchain.chain)
            data.append(tx_data)
            data.append(blockchain.get_latest_block())
            data.append(blockchain.difficulty)
            return jsonify(data), 200
        else:
            return "No Transactions", 400
    except Exception as e:
        flash(f"Error in mining data API: {e}", 'error')
        return "Error fetching mining data", 500


@app.route("/submit_block", methods=['GET', 'POST'])
def submit():
    try:
        if request.method == 'POST':
            data = request.json
            block = data['block']
            address = data['address']

            if blockchain.validate_block(block):
                blockchain.reward_miner(address)
                blockchain.chain.append(block)
                blockchain.sync()
                return "Added!"
            else:
                return "Not Added! Make sure the block meets the requirements"
    except Exception as e:
        flash(f"Error in submit block: {e}", 'error')
        return "Error submitting block", 500


def autosync():
    try:
        blockchain.sync()
        threading.Timer(10, autosync).start()
    except Exception as e:
        flash(f"Error in autosync: {e}", 'error')


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--portarg", type=int, default=5000, help="Port for Flask server")
        args = parser.parse_args()
        port = args.portarg
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_FILE_DIR"] = f"./flask_sessions_{port}"
        app.secret_key = f"dev_server_secret_key_{port}"

        sync_thread = threading.Thread(target=autosync, daemon=True)
        sync_thread.start()

        Session(app)
        app.run(host="127.0.0.1", port=port)
    except Exception as e:
        flash(f"Error in main: {e}", 'error')






