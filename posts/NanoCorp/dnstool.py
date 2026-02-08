'''
DNS tool to automate DNS enum

Author: Karim (@fsociety_py00)(github.com/cpu0x00)
'''
import dns.resolver
import dns.zone
import dns.query
import dns.update
from subprocess import getoutput # for dig
import textwrap
import argparse


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,epilog=textwrap.dedent(''' 

Examples:

dnstool.py -t zonetransfer.me -r A --> returns the A record\t

dnstool.py -t zonetransfer.me -zt  --> attempts zonetransfer against the target (using the dig utility)

dnstool.py -update -t domain.com -r A -e subdomain.domain.com --map ip_address --> will attempt to update the A record of the subdomain
on the dns server to the mapped (ip_address) # useful in a dns cache poison attack 

dnstool.py -add -t domain.com -r A -e subdomain.domain.com --map ip_address --> will attempt to add a new A record of the subdomain 
on the dns server to the mapped (ip_address)

dnstool.py --file domains.txt --all --> will return all available records for every domain in the file

	'''))

parser.add_argument('--target', '-t', help='the target domain name OR ip address')
parser.add_argument('--zonetransfer', '-zt', action='store_true', help='attempt to make a zone transfer on the given domain')
parser.add_argument('--record', '-r', help="the record to resolve (example: A, NS, CNAME, SOA , PTR, MX, TXT, AAAA)")
parser.add_argument('--all', action='store_true', help='alias for (ANY) record, returns all the available records')
parser.add_argument('-update', action='store_true', help='update an entry [requires the (--entry) flag and (--record) flag]')
parser.add_argument('--entry', '-e', help='entry to update [to be used only with the --update/--add flag]')
parser.add_argument('--map', '-m', help='mapping target to map the newly added entry to [to be used only with the --update/--add flag] ')
parser.add_argument('-add',action='store_true', help='add a new entry to the dns server')
parser.add_argument('--file', '-f', help='enumerate mutliple domains from file')
args = parser.parse_args()

domain = args.target

records = ['A','NS','CNAME','SOA','PTR','MX','TXT','AAAA']


def get_domains_from_file():

	if args.file:
		domains_list = open(args.file, 'r', encoding='latin1').readlines()
		domains = [d.strip() for d in domains_list]

	return domains

def update_record(zone, record, entry, mapped): 
# updates a record in a dns server (if the dns server supports updates) [HIGHLY EXPERMENTAL]
	NS_IPV4 = []

	print('[*] attempting dns entry update')
	delete_entry = dns.update.Update(zone)  # zone is the server or the main domain of a subdomain
	delete_entry.delete(entry, record)
	for ip in NS_IPV4: # query to make sure the delete request is submitted
		dns.query.tcp(delete_entry,ip)

	add_entry = dns.update.Update(domain)
	add_entry.add(entry, 1234, record, mapped) # mapped here will be MYIP in a dns cache poison attack

	def get_response():
		ns_query = dns.resolver.resolve(zone, 'NS')

		for answer in ns_query:
			ns_ipv4 = dns.resolver.resolve(str(answer)[:-1], 'A')
			for ip in ns_ipv4:
				NS_IPV4.append(str(ip))
				response = dns.query.tcp(add_entry, str(ip))
				if 'REFUSED' in str(response):
					print(f'\n[REFUSED] the nameserver ({str(answer)[:-1]} -> {ip}) refused the update request \n')
					print('[i] full response')
					print('-------------------------')
					print(response)

				if 'REFUSED' not in str(response):
					print('[SUCCESS] entry added successfully')
					print(f'[*] nameserver: {str(answer)[:-1]} -> {ip}\n')
					print('[i] full response')
					print('-------------------------')
					print(response)

	try:

		get_response()
	except Exception as e:
		if 'The DNS response does not contain an answer to the question' in str(e):
			exit('[FATAL] no nameserver (NS) records has been found for the given domain !')

def add_record(zone, record, entry, mapped):
	# add a record to a dns server (if the dns server supports it) [HIGHLY EXPERMENTAL]
	add_entry = dns.update.Update(domain)
	add_entry.add(entry, 1234, record, mapped) # mapped here will be MYIP in a dns cache poison attack

	def get_response():
		ns_query = dns.resolver.resolve(zone, 'NS')

		for answer in ns_query:
			ns_ipv4 = dns.resolver.resolve(str(answer)[:-1], 'A')
			for ip in ns_ipv4:
				
				response = dns.query.tcp(add_entry, str(ip))
				if 'REFUSED' in str(response):
					print(f'\n[REFUSED] the nameserver ({str(answer)[:-1]} -> {ip}) refused the add request \n')
					print('[i] full response')
					print('-------------------------')
					print(response)

				if 'REFUSED' not in str(response):
					print('[SUCCESS] entry added successfully')
					print(f'[*] nameserver: {str(answer)[:-1]} -> {ip}\n')
					print('[i] full response')
					print('-------------------------')
					print(response)

	try:

		get_response()
	except Exception as e:
		if 'The DNS response does not contain an answer to the question' in str(e):
			exit('[FATAL] no nameserver (NS) records has been found for the given domain !')



def zonetransfer(domain):
	check_for_dig = "which dig"

	which_output = getoutput(check_for_dig)

	if 'dig' not in which_output: # checking for the dig utility
		print('[FATAL] did not found (dig) utility')
		print('[INFO] use: (apt install dnsutils) to install it ')

		exit()



	NS = []
	try:

		print(f'[*] attempting zonetransfer against {domain} with (dig) utility')
		nameservers = dns.resolver.resolve(domain, 'NS')
		for nameserver in nameservers:
			nameserver = str(nameserver)[:-1]
			# print(nameserver)
			NS.append(nameserver)

		print(f"[*] found {len(nameservers)} NS records: {', '.join(NS)}")
		print('[*] starting zonetransfer...\n')


		for ns in NS:

			print(getoutput(f'dig axfr {domain} @{ns}'))
	
	except KeyboardInterrupt:
		exit('\n[ERROR] operation terminated by a user')

	except Exception as e:
		if 'The DNS query name does not exist' in str(e):
			print(f'[ERROR] failed to resolve the domain ({domain}) CHECK THE SYNTAX')
		
		if 'The DNS response does not contain an answer to the question' in str(e):
			print('[FATAL] did not find any nameserver (NS) records ')



def resolver_onDemand(domain, record):
	if record not in records:
		print('[FATAL] wrong record ')
		print(f'[INFO] records: {" ".join(records)}')
		exit()

	try:
		print(f'[*] resolving the ({record}) record for {domain}\n')

		query = dns.resolver.resolve(domain, record)

		for answer in query:
			if record == 'NS' or record == 'ns':
				ns_ipv4 = dns.resolver.resolve(str(answer)[:-1], 'A')
				for ipv4 in ns_ipv4:

					print(f'[ANSWER] {answer} -> {ipv4}')

			else:
				print(f'[ANSWER] {answer}')


	except KeyboardInterrupt:
		exit('\n[ERROR] operation terminated by a user')
	except Exception as e:
		if 'The DNS response does not contain an answer to the question' in str(e):
			print(f'\n[FAILED] there is no {record} record for {domain}')



def resolver_ANY(domain):
	try:
		print(f'[*] getting every DNS record possible for {domain}\n')
		

		for r in records:
			try:

				query = dns.resolver.resolve(domain, r)

				for answer in query:
					print(f'{r} {answer.to_text()}')

			except Exception as e:
				if 'The DNS response does not contain an answer to the question' in str(e):
					# print(f'there is no {r} record for {domain}')
					pass
				
				if 'The DNS query name does not exist:' in str(e):
					exit(f'[FATAL] the domain ({domain}) not found CHECK THE SYNTAX')


	except KeyboardInterrupt:
		exit('\n[ERROR] operation terminated by a user')	

def main():
	if not args.target and not args.file:
		exit('[ERROR] you must provide a single target or a domains file. use: [--target/--file]')
	
	if (args.update and args.add):
		exit('[ERROR] cannot run in both update and add mode in the same time')

	if args.zonetransfer and args.target:

		zonetransfer(args.target)	

	if args.record and not args.update and not args.add and not args.entry and not args.map and args.target:
		resolver_onDemand(args.target, args.record)
		exit()
	
	if args.all and args.target:
		resolver_ANY(args.target)
		exit()

	if args.update and args.entry and args.record and args.map and args.target:
		update_record(domain, args.record, args.entry, args.map)
		exit()

	if args.add and args.entry and args.record and args.map and args.target:
		add_record(domain, args.record, args.entry, args.map)
		exit()
	
	if args.file and args.zonetransfer:
		domains = get_domains_from_file()

		for domain in domians:
			zonetransfer(domain)
			print('\n----------------------------------------------------------------------\n\n')	

		

	if args.record and args.file and not args.update and not args.add and not args.entry and not args.map:
		domains = get_domains_from_file()

		for domain in domains:
			resolver_onDemand(domain, args.record)
			print('\n----------------------------------------------------------------------\n\n')
		
	
	if args.all and args.file:
		domains = get_domains_from_file()

		for domain in domains:
			resolver_ANY(domain)
			print('\n----------------------------------------------------------------------\n\n')



	if (args.update or args.add) and not args.entry:
		exit('[ERROR] you must use an entry to update OR add, use the [--entry/-e] flag')


	if args.entry and (args.update or args.add) and not args.record:
		exit('[ERROR] No record specified to update or add use the [--record/-r] flag')

	if (args.update or args.add) and args.record and args.entry and not args.map:
		exit('[ERROR] no mapping to map the new entry to use [--map/-m] flag')


	if (args.entry or args.map) and (not args.update or not args.add) and not args.file:
		exit('[ERROR] the script will not run in update OR add mode unless one of [--update/-u OR --add/-a] flags is specified')
		


if __name__ == "__main__":
	main()
