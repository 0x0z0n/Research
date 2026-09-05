import requests
from datetime import datetime
import hashlib
import json
import itertools
url = "http://127.0.0.1:8080/"

class Miner:
     
    def __init__(self):
        self.pending_transactions = []
        self.difficulty = ""
        self.chain = []
        self.address = "9d9407b17e3aafc709e7fc670299aba3fb8c9b01d7730badd4a198472489a5a64412837dd528728a9d08b73ff0c07a8ef96b9a0d84f47f25e6bdbce3f7bdc6c0"
    
    def get_data(self):

        response = requests.get(url + "mining_data")

        if response.status_code == 400:
             print("No Transactions!")
             return False
        else:
            data = response.json()

            print(f"Data: {data}")

            
            self.chain = data[0]
            self.pending_transactions = data[1]
            self.previous_hash = data[2]
            self.difficulty = data[3]
            self.fakedata = [{
                        'amount': 2, 
                        'receiver': '9d9407b17e3aafc709e7fc670299aba3fb8c9b01d7730badd4a198472489a5a64412837dd528728a9d08b73ff0c07a8ef96b9a0d84f47f25e6bdbce3f7bdc6c0', 
                        'sender': 'd386e15ea16a93b3e1325a4d3418ad17552fea23e5b1a6c9ac6279c2deec617fc6f3f7e33cf7a6c51a35585171a079857e59cca99c94795b8082852a04f97263', 'signature': 'f33365be8f8f07bc0f398be8d20fb74e1e45a2ba9a876a956e53656742174d208cff39776120bb7e3261cfd72efdd89893570958266255734dde9aad9303fa81', 
                        'timestamp': '2025-05-10 16:36:33.224966'
                        }]
            self.proof_of_work()


    def proof_of_work(self):
            nonce = 0
            check = False

            index = len(self.chain) + 1
            timestamp = str(datetime.now())
            previous_hash = self.previous_hash
            block_data = self.pending_transactions[:5]

            # Mining. Damit der Block zur Chain hinzugefügt wird muss eine gewisser Rechenleistung aufgebracht werden um den richtigen Hash zu "finden". 
            # Sobald die Bedingung des hashes erfüllt ist wird der Block erstellt 
            while check is False:

                pow_hash = (f"{index}{previous_hash}{timestamp}{json.dumps(block_data, sort_keys=True)}{nonce}")
                pow_hash = hashlib.sha256(pow_hash.encode()).hexdigest()

                if str(pow_hash)[:len(self.difficulty)] == self.difficulty:
                    check = True
                    print("Gültiger Hash gefunden! Block wird gebaut und gesendet")
                    
                    self.block = {'index': index,
                            'nonce': nonce,
                            'timestamp': timestamp,
                            'previous_hash': previous_hash,
                            'data': block_data,
                            'hash': pow_hash
                            }
                    
                    print(f"Block: {self.block}")

                    self.payload = {
                         'address': self.address,
                         'block': self.block
                    }

                    self.send_block() 

                else:
                    nonce += 1  


    def send_block(self):

        requests.post(url + "/submit_block", json=self.payload)


miner = Miner()
miner.get_data()