from datetime import datetime
import hashlib
from ecdsa import SigningKey, NIST256p, VerifyingKey
import ecdsa
import json
import requests
import threading
import time
from random import randint, choice

from contract import ContractEngine


class Blockchain:

    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.pending_rewards = []
        self.difficulty = "000" # Reduced difficulty for Developing
        self.proof_of_work(data=[{"Genesis Block": "Genesis Block", "timestamp": str(datetime.now())}])
        self.nodes = []
        self.last_adjustment_block = 0
        self.txnhistory = []
        

    
    def create_block(self, index, timestamp, previous_hash, hash, nonce, data):

        block = {'index': index,
                'nonce': nonce,
                'timestamp': timestamp,
                'previous_hash': previous_hash,
                'data': data,
                'hash': hash
                }
        self.chain.append(block)
        self.dynamic_difficulty()


    def get_latest_block(self):

        if self.chain:
            latest_block = self.chain[-1] 
            previous_hash = latest_block['hash']
        else:
            previous_hash = "0"

        return previous_hash
 

    def proof_of_work(self, data):

        nonce = 0
        check = False
        index = len(self.chain) + 1
        timestamp = str(datetime.now())
        previous_hash = self.get_latest_block()

        while check is False:

            pow_hash = (f"{index}{previous_hash}{timestamp}{json.dumps(data, sort_keys=True)}{nonce}")
            pow_hash = hashlib.sha256(pow_hash.encode()).hexdigest()

            if str(pow_hash)[:len(self.difficulty)] == self.difficulty:
                check = True
                print("Valid hash found! Block is being created")
                self.create_block(index, timestamp, previous_hash, pow_hash, nonce, data)
                return True
            else:
                nonce += 1

  
    def reward_miner(self, address):

        coinbase_txn = {
            'timestamp': str(datetime.now()),
            'sender': "Blockchain_Reward",
            'receiver': address,
            'amount': 5,
            'signature': 'Blockchain'
        }

        self.pending_rewards.append(coinbase_txn)
        print(f"Miner Reward added to list: {self.pending_rewards}")


    def dynamic_difficulty(self):

        target_time = 10
        block_amount = 5 
        total_time = 0
        previous_average = None

        if len(self.chain) < block_amount:
            return
        
        for i in range(len(self.chain) - block_amount, len(self.chain) - 1):
            
            format = '%Y-%m-%d %H:%M:%S.%f'
            next_block = self.chain[i + 1] 
            block = self.chain[i]
            timestamp1 = datetime.strptime(next_block['timestamp'], format)
            timestamp2 = datetime.strptime(block['timestamp'], format)
            total_time += (timestamp1 - timestamp2).total_seconds()

        if previous_average is None:
            average = total_time / block_amount
            previous_average = average
        else:
            average = (0.7 * (total_time / block_amount) + (0.3 * previous_average))
        
        previous_average = 0.9 * previous_average + 0.1 * average
        print(f"Average Mining Time: {average}")

        if self.last_adjustment_block % 5 == 0: 

            if average > target_time * 1.5:
                self.difficulty = self.difficulty[:-1]
                print(f"Difficulty lowered to {self.difficulty}")
            elif average < target_time * 0.6:
                self.difficulty += "0"
                print(f"Difficulty increased to {self.difficulty}")

        self.last_adjustment_block += 1


    def hash(self, block):

        block_string = f"{block['index']}{block['previous_hash']}{block['timestamp']}{json.dumps(block['data'], sort_keys=True)}{block['nonce']}"
        hash = hashlib.sha256(block_string.encode()).hexdigest()

        return hash


    def validation(self, chain):

        for i in range(1, len(chain)):

            latest_block = chain[i - 1] 
            block = chain[i]
            previous_hash = block['previous_hash']
            real_previous_hash = self.hash(latest_block)
            block_hash = block['hash']
            real_block_hash = self.hash(block)

            if previous_hash != real_previous_hash:
                print("Blockchain Invalid")
                return False

            if block_hash != real_block_hash or block_hash[:len(self.difficulty)] != self.difficulty:
                print("Blockchain Invalid!")
                return False

        return True


    def validate_block(self, block):
        
        latest_block = self.chain[-1] 
        previous_hash = block['previous_hash']
        real_previous_hash = self.hash(latest_block)
        block_hash = block['hash']
        real_block_hash = self.hash(block)
        txns = block['data']
        reward = txns[0]

        for txn in txns[1:]:
            if txn not in self.pending_transactions:
                print("False Data detected! Block invalid")
                return False
        
        if reward['sender'] == 'Blockchain_Reward':
            if reward not in self.pending_rewards:
                print("False Data detected! Block invalid")
                return False
            else: 
                self.pending_rewards.pop(0)

        if len(txns) > 5:
            print("Block to large! Block Invalid!")
            return False
        elif previous_hash != real_previous_hash:
            print("Block Invalid!")
            return False
        elif block_hash != real_block_hash or block_hash[:len(self.difficulty)] != self.difficulty:
            print("Block Invalid!")
            return False
        else: 
            print("Block valid!")
            for txn in txns:
                if txn in self.pending_transactions:
                    self.pending_transactions.remove(txn)        
                    print("Removed pending transactions")
            return True


    def txn_verify(self, data):

        verify_string = (f"{data['timestamp']}{data['sender']}{data['receiver']}{data['amount']}") 
        verify_hash = hashlib.sha256(verify_string.encode()).digest()
        verify_key = VerifyingKey.from_string(bytes.fromhex(data['sender']), curve=NIST256p)
        signature = bytes.fromhex(data['signature'])

        try:  
            verify_key.verify(signature, verify_hash)
            print("Signature valid!")
            return True
        except ecdsa.BadSignatureError:
            print("Signature not valid!")
            return False


    def register_nodes(self, data):

        if data not in self.nodes:
            self.nodes.append(data)


    def sync(self):

        for node in self.nodes:

            print(f"Requesting Node: {node}")
            try:
                data = requests.get(node).json()
                print(data)
            except requests.exceptions.RequestException:
                print("Fehler beim aufrufen von Node")
                continue

            self.newchain = data

            if self.validation(self.newchain) == True and len(data) > len(self.chain):

                print("Longer valid blockchain found. Will be updated!")
                self.chain = self.newchain
            else:
                print("No larger blockchain found!")
    

    def restore_chain(self, file):

        if isinstance(file, str):
            with open(file, "r") as f:
                data = json.load(f)
        else:
            data = json.load(file)

        self.chain = data


    def txn_history(self, blockchain):

        for block in blockchain:

            if block['index'] == 1:
                continue

            for txn in block['data']:
                history = {
                    'timestamp': txn['timestamp'],
                    'sender': txn['sender'],
                    'receiver': txn['receiver'],
                    'amount': txn['amount']
                }

                if history not in self.txnhistory:
                    self.txnhistory.append(history)
                else:
                    continue

        return self.txnhistory


    def simulate_txn(self):

        if len(self.chain) < 3 and len(self.pending_transactions) == 5 and self.pending_rewards == []:
            self.proof_of_work(data=self.pending_transactions[:5])
            self.pending_transactions.clear()
            print("Simulated Block with 5 Transactions created!")

        elif len(self.chain) < 3 and len(self.pending_transactions) == 4 and self.pending_rewards != []:
            txn_data = []
            txn_data.insert(0, self.pending_rewards[0])         
            txn_data.extend(self.pending_transactions[:4])
            self.proof_of_work(data=txn_data)  
            self.pending_transactions.clear()
            self.pending_rewards.pop(0)
            print("Simulated Block with 5 Transactions created!")
            
        if len(self.pending_transactions) < 20:
            priv_key = SigningKey.generate(curve=NIST256p)
            pub_key = priv_key.verifying_key
            sender = pub_key.to_string().hex()
            priv_key = SigningKey.generate(curve=NIST256p)
            receiver_pub_key = priv_key.verifying_key
            receiver = receiver_pub_key.to_string().hex()
            amount = randint(1, 100)
            timestamp = str(datetime.now())
            txn_string = (f"{timestamp}{sender}{receiver}{amount}")
            txn_hash = hashlib.sha256(txn_string.encode()).digest()
            signature = priv_key.sign(txn_hash)

            transaction = {
                    'timestamp': timestamp, 
                    'sender': sender,
                    'receiver': receiver,
                    'amount': amount,
                    'signature': signature.hex()}
        
            self.pending_transactions.append(transaction)

            priv_key = SigningKey.generate(curve=NIST256p)
            receiver_pub_key = priv_key.verifying_key
            receiver = receiver_pub_key.to_string().hex()
            
            if self.pending_rewards == [] and len(self.chain) == 2:
                transaction2 = {
                        'timestamp': timestamp, 
                        'sender': "Blockchain_Reward",
                        'receiver': receiver,
                        'amount': 5,
                        'signature': "Blockchain"}
                
                self.pending_rewards.append(transaction2)

            
        
class Wallet:

    def __init__(self):
        self.priv_key = SigningKey.generate(curve=NIST256p)
        self.pub_key = self.priv_key.verifying_key
        self.address = self.pub_key.to_string().hex()
        self.balance = 0
        self.txnhistory = []
        

    def save_wallet(self, filename):

        data = {'private_key': self.priv_key.to_string().hex(),
                'public_key': self.pub_key.to_string().hex()}
        
        with open(filename, "w") as wallet:
            json.dump(data, wallet)


    def create_wallet(self):

        data = {'private_key': self.priv_key.to_string().hex(),
                'public_key': self.pub_key.to_string().hex()}
        print("Wallet created!")
        return data
    

    def load_wallet(self, file):

        if isinstance(file, str):
            with open(file, "r") as wallet:
                data = json.load(wallet)
        else:
            data = json.load(file)

        self.priv_key = SigningKey.from_string(bytes.fromhex(data['private_key']), curve=NIST256p)
        self.pub_key = VerifyingKey.from_string(bytes.fromhex(data['public_key']), curve=NIST256p)
        self.address = data['public_key']
        print(f"Saved Public Key: {data['public_key']}")
        print(f"Loaded Public Key: {self.pub_key.to_string().hex()}")
        print(f"Address: {self.address}")
    

    def txn(self, chain, receiver, amount):

        if amount <= 0:
            print("Invalid amount!")

        self.calc_balance(chain.chain, chain.pending_transactions)   

        if amount > 0:
            if float(self.balance) < float(amount):
                print("Not enough credit!")

            elif float(self.balance) >= float(amount):

                timestamp = str(datetime.now())
                txn_string = (f"{timestamp}{self.address}{receiver}{amount}")
                txn_hash = hashlib.sha256(txn_string.encode()).digest()
                signature = self.priv_key.sign(txn_hash)

                transaction = {
                        'timestamp': timestamp, 
                        'sender': self.address,
                        'receiver': receiver,
                        'amount': amount,
                        'signature': signature.hex()}
                
                print(f"Transaction Data: {transaction}")

                return transaction 


    def calc_balance(self):

        self.balance = 99999
        return self.balance
    

    def history(self, blockchain):

        for block in blockchain:
            if block['index'] == 1:
                continue

            for txn in block['data']:
                if self.address == txn['sender']:

                    history = {
                        'receiver': txn['receiver'],
                        'amount': txn['amount']
                    }

                    self.txnhistory.append(history)

        return self.txnhistory



class Contract:

    def __init__(self):
        self.contracts = {}
        self.index = 0


    def save_contract(self, data, id=None):

        if not id:
            id = self.index
            self.index += 1 

            self.contracts[int(id)] = data
            return id
    

    def load_contract(self, id):

        return self.contracts[int(id)]
    
    
    def update_contract(self, id , storage):

        self.contracts[int(id)]["storage"] = storage