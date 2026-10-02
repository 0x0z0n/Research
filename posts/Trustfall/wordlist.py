#!/usr/bin/env python3
names = ["Santiago", "Alejandro", "Salvador"]
departments = ["HR", "IT", "SALES", "MARKETING", "FINANCE", "SUPPORT", "LEGAL", "ADMIN", "OPERATIONS"]
years = range(1970, 2010)

with open("targeted_wordlist.txt", "w") as f:
    for name in names:
        for dept in departments:
            for year in years:
                f.write(f"TrustFall{dept}{name}{year}!\n")
