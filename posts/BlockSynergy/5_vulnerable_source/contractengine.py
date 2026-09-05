import datetime
import json
from collections import OrderedDict

class ContractEngine():
    def __init__(self, contract_data):
        try:
            self.contract = contract_data
            self.name = contract_data.get("name")
            self.id = contract_data.get("id")
            self.owner = contract_data.get("owner")
            self.logic = contract_data.get("logic", {})
            self.storage = contract_data.get("storage", {})
            self.storage["balances"] = self.storage.get("balances", {})
            self.debug = contract_data.get("debug", "False")
        except Exception as e:
            print(f"Error initializing contract: {e}")

    def is_allowed(self, func, sender):
        try:
            rule = self.logic.get(func, "deny")
            if rule == "deny":
                return False
            elif rule == "check_owner" and self.owner != sender:
                return False
            elif rule == "allow":
                return True
            elif rule == "vip_only" and self.storage.get("balances", {}).get(sender, 0) >= 100:
                return True 
            elif rule == "once" and not self.storage.get("used", {}).get(func, {}).get(sender, False):
                return True
        except Exception as e:
            print(f"Error in is_allowed: {e}")
            return False

    def mint(self, sender, amount):
        try:
            if self.is_allowed("mint", sender):
                self.storage["balances"].setdefault(sender, 0)
                self.storage["balances"][sender] += amount
                self.storage["total_supply"] += amount
                self.run_hook("on_mint", sender, "mint")
                return True
        except Exception as e:
            print(f"Error in mint: {e}")
            return False

    def burn(self, sender, amount):
        try:
            if self.is_allowed("burn", sender) and self.storage["balances"].get(sender, 0) >= amount:
                self.storage["balances"][sender] -= amount
                self.storage["total_supply"] -= amount
                self.run_hook("on_burn", sender, "burn")
                return True
        except Exception as e:
            print(f"Error in burn: {e}")
            return False

    def vote(self, sender, option):
        try:
            if self.is_allowed("vote", sender) and option in self.storage['votes']:
                self.storage["votes"].setdefault(option, 0)
                self.storage["votes"][option] += 1
                self.storage.setdefault("used", {}).setdefault("vote", {})[sender] = True
                self.run_hook("on_vote", sender, "vote")
                return True
        except Exception as e:
            print(f"Error in vote: {e}")
            return False

    def claim(self, sender):
        try:
            if self.is_allowed("claim", sender):
                self.storage["balances"].setdefault(sender, 0)
                self.storage["balances"][sender] += 1
                self.storage.setdefault("used", {}).setdefault("claimed", {})[sender] = True
                self.run_hook("on_claim", sender, "claim")
                return True
        except Exception as e:
            print(f"Error in claim: {e}")
            return False
        
    def run_hook(self, hook_name, sender=None, action=None):
        try:
            hook_val = self.contract.get("hooks", {}).get(hook_name)

            if hook_val == "grant_vip":
                    self.storage["vip"].setdefault(sender, "True")

            elif hook_val == "track_action":
                self.storage.setdefault("tracking", {}).setdefault("actions", {}).setdefault(action, {})[sender] = 0
                self.storage["tracking"]["actions"][action][sender] += 1
                print(self.storage)

            elif hook_val == "None":
                return True
            
            # Debugging hooks are ONLY meant for testing. REMOVE BEFORE DEPLOYING TO THE REAL BLOCKCHAIN! 
            if self.debug == "True": 

                if hook_val == "log":
                    content = self.contract.get("__meta__", {}).get("log_content", "").get(hook_name, "")
                    file = self.contract.get("__meta__", {}).get("log_file", "")
                    timestamp = datetime.datetime.now().isoformat()
                    logfile = f"/opt/staging/smart_contracts/logs/{file}"
                    with open(logfile, "a") as f:
                        f.write(f"[{timestamp}] [{hook_name}] {content}\n")
                        print(f"Action logged to: {file}")

                elif hook_val == "backup":
                    file = self.contract.get("__meta__", {}).get("backup_filename", "")
                    with open(f"/opt/staging/smart_contracts/logs/{file}", "w") as f:
                        json.dump(self.storage, f, indent=4)
                        print("Backup completed!")
        except Exception as e:
            print(f"Error in run_hook: {e}")

    def return_updated_contract(self):
        try:
            return self.storage
        except Exception as e:
            print(f"Error in return_updated_contract: {e}")
            return None
    
    def return_logs(self):
        try:
            if self.debug == "True":
                file = self.contract.get("__meta__").get("log_file")

                if not file:
                    return "No Log File specified"
                
                logfile = f"/opt/staging/smart_contracts/logs/{file}"
                with open(logfile, "r") as log:
                    return log.read()
        except Exception as e:
            print(f"Error in return_logs: {e}")
            return "Error reading logs"
