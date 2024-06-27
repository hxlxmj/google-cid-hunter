import re
import requests
import urllib.parse
import sys
import os
import argparse
from tqdm import tqdm
from colorama import init, Fore, Style
import jsbeautifier

init(autoreset=True)

def extract_client_id(url):
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    client_id = query_params.get('client_id', [None])[0]
    return client_id

def extract_origin(url):
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    redirect_uri = query_params.get('redirect_uri', [None])[0]
    if (redirect_uri):
        redirect_uri_parsed = urllib.parse.urlparse(urllib.parse.unquote(redirect_uri))
        return redirect_uri_parsed.netloc
    return "Unknown"

def is_valid_client_id(client_id):
    pattern = re.compile(r'^\d+(-[a-z0-9]+)?\.apps\.googleusercontent\.com$')
    return pattern.match(client_id) is not None

def extract_email(response_text):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    match = email_pattern.search(response_text)
    return match.group(0) if match else None

def extract_all_domains(url, response_text):
    domains = set()
    url_pattern = re.compile(r'https://[a-zA-Z0-9.-]+')
    domain_pattern = re.compile(r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

    url_matches = url_pattern.findall(url)
    for match in url_matches:
        domain = match.split("//")[-1]
        domains.add(domain)

    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    for key, values in query_params.items():
        for value in values:
            if '://' in value:
                sub_parsed_url = urllib.parse.urlparse(value)
                domains.add(sub_parsed_url.netloc)

    email = extract_email(response_text)
    if email:
        domain_match = domain_pattern.search(email)
        if domain_match:
            domains.add(domain_match.group(1))

    domains.discard("accounts.google.com")
    domains.discard("www.googleapis.com")
    domains.discard("valid.url")
    domains.discard("")
    
    return domains

def beautify_js(js_code):
    opts = jsbeautifier.default_options()
    opts.indent_size = 2
    return jsbeautifier.beautify(js_code, opts)

def extract_js_domains(response_text):
    lines = response_text.split('\n')
    last_10_lines = '\n'.join(lines[-10:])
    beautified_js = beautify_js(last_10_lines)

    domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
    domains = set(domain_pattern.findall(beautified_js))

    return domains

def process_url(url):
    client_id = extract_client_id(url)
    success = True

    if not client_id:
        print(f"{Fore.RED}No client_id found in the URL.")
        success = False
    elif not is_valid_client_id(client_id):
        print(f"{Fore.RED}Invalid client_id: {client_id}")
        success = False

    if success:
        headers = {
            "Host": "accounts.google.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Cookie": "__Host-GAPS=1:qo5tjYVkpfzrF3EH0jRHUndSlYgjVw:XEtC-4BjS1v1g_5D;",
        }

        data = f'f.req=%5B%5B%5B%22WZfWSd%22%2C%22%5B2%2C1%5D%22%2Cnull%2C%221%22%5D%2C%5B%22etGTrd%22%2C%22%5B%5C%22{client_id}%5C%22%2C%5C%22https%3A%2F%2Fvpn1.volans.tech%5C%22%5D%22%2Cnull%2C%222%22%5D%2C%5B%22Aho3hb%22%2C%22%5B%5D%22%2Cnull%2C%223%22%5D%2C%5B%22i3kFoc%22%2C%22%5B%5D%22%2Cnull%2C%224%22%5D%2C%5B%22zKAP2e%22%2C%22%5B%5C%22identity-signin-password%5C%22%5D%22%2Cnull%2C%226%22%5D%2C%5B%22RzSO2e%22%2C%22%5B%5C%22{client_id}%5C%22%5D%22%2Cnull%2C%227%22%5D%5D%5D&at=ALt4Ve29PZzUxNk6P93qVlYfDpdE%3A1719387079176&'

        try:
            response = requests.post(
                "https://accounts.google.com/v3/signin/_/AccountsSignInUi/data/batchexecute",
                headers=headers,
                data=data
            )

            if response.status_code == 200:
                response_text = response.text
                email = extract_email(response_text)
                domains = extract_all_domains(url, response_text)
                js_domains = extract_js_domains(response_text)
                domains.update(js_domains)

                if email:
                    print(f"{Fore.GREEN}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
                    print(f"{Fore.GREEN}{Style.BRIGHT}Admin Email: {Style.RESET_ALL}{email}")
                else:
                    print(f"{Fore.RED}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
                    print(f"{Fore.RED}No email address found in the response.")

                if domains:
                    print(f"{Fore.GREEN}{Style.BRIGHT}Domains: {Style.RESET_ALL}{', '.join(domains)}")
                else:
                    print(f"{Fore.RED}No domains found in the response.")

                print()

            else:
                print(f"{Fore.RED}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
                print(f"{Fore.RED}Failed to fetch the email. Status Code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
            print(f"{Fore.RED}Error fetching the email: {e}")

def process_client_id(client_id):
    if client_id and is_valid_client_id(client_id):
        url = f"https://accounts.google.com/gsi/select?client_id={client_id}&redirect_uri=https://valid.url"
        process_url(url)
    elif client_id:
        print(f"{Fore.RED}Invalid client_id: {client_id}")

def process_input(input_value):
    if os.path.isfile(input_value):
        with open(input_value, 'r') as file:
            lines = file.readlines()
        for line in tqdm(lines, desc="Validating client IDs and URLs", colour="yellow"):
            line = line.strip()
            if "http" in line:
                process_url(line)
            else:
                process_client_id(line)
    elif "http" in input_value:
        process_url(input_value)
    else:
        process_client_id(input_value)

def main():
    parser = argparse.ArgumentParser(description="Extract and validate Google Client IDs from URLs or files.")
    parser.add_argument("input", help="URL, client_id or file containing URLs/client_ids to validate")
    args = parser.parse_args()

    process_input(args.input)

if __name__ == "__main__":
    main()
