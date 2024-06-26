import re
import requests
import urllib.parse
import sys
import os
import argparse
from tqdm import tqdm
from colorama import init, Fore, Style

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
    if redirect_uri:
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

def process_url(url):
    client_id = extract_client_id(url)
    origin = extract_origin(url)

    if not client_id:
        print(f"{Fore.RED}No client_id found in the URL.")
        return

    if not is_valid_client_id(client_id):
        print(f"{Fore.RED}Invalid client_id format.")
        return

    headers = {
        "Host": "accounts.google.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Cookie": "__Host-GAPS=1:qo5tjYVkpfzrF3EH0jRHUndSlYgjVw:XEtC-4BjS1v1g_5D;",
    }

    data = f'f.req=%5B%5B%5B%22WZfWSd%22%2C%22%5B2%2C1%5D%22%2Cnull%2C%221%22%5D%2C%5B%22etGTrd%22%2C%22%5B%5C%22{client_id}%5C%22%2C%5C%22https%3A%2F%2Fvpn1.volans.tech%5C%22%5D%22%2Cnull%2C%222%22%5D%2C%5B%22Aho3hb%22%2C%22%5B%5D%22%2Cnull%2C%223%22%5D%2C%5B%22i3kFoc%22%2C%22%5B%5D%22%2Cnull%2C%224%22%5D%2C%5B%22zKAP2e%22%2C%22%5B%5C%22identity-signin-password%5C%22%5D%22%2Cnull%2C%226%22%5D%2C%5B%22RzSO2e%22%2C%22%5B%5C%22{client_id}%5C%22%5D%22%2Cnull%2C%227%22%5D%5D%5D&at=ALt4Ve29PZzUxNk6P93qVlYfDpdE%3A1719387079176&'

    response = requests.post(
        "https://accounts.google.com/v3/signin/_/AccountsSignInUi/data/batchexecute?rpcids=WZfWSd%2CetGTrd%2CAho3hb%2Ci3kFoc%2CzKAP2e%2CRzSO2e&source-path=%2Fv3%2Fsignin%2Fchallenge%2Fpwd&f.sid=-4453641016717953570&bl=boq_identityfrontendauthuiserver_20240609.08_p0&hl=en-US&TL=AC3PFD5op1jFLF1g6M_Z1HG3lRBSFNhzNp-HToRplZO5KeTgWLcfi8zD_d-uvsTd&_reqid=212684&rt=c",
        headers=headers,
        data=data
    )

    if response.status_code == 200:
        email = extract_email(response.text)
        if email:
            print(f"{Fore.GREEN}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
            print(f"{Fore.GREEN}{Style.BRIGHT}Domain: {Style.RESET_ALL}{origin}")
            print(f"{Fore.GREEN}{Style.BRIGHT}Admin Email: {Style.RESET_ALL}{email}")
        else:
            print(f"{Fore.RED}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
            print(f"{Fore.RED}{Style.BRIGHT}Domain: {Style.RESET_ALL}{origin}")
            print(f"{Fore.RED}No email address found in the response.")
    else:
        print(f"{Fore.RED}{Style.BRIGHT}Client ID: {Style.RESET_ALL}{client_id}")
        print(f"{Fore.RED}{Style.BRIGHT}Domain: {Style.RESET_ALL}{origin}")
        print(f"{Fore.RED}Failed to fetch the email. Status Code: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="Extract and validate Google Client IDs from URLs.")
    parser.add_argument("url", nargs="?", help="URL to extract client_id from")
    parser.add_argument("--input-file", help="File containing client_id to validate")
    args = parser.parse_args()

    if args.input_file:
        if not os.path.isfile(args.input_file):
            print(f"{Fore.RED}The file {args.input_file} does not exist.")
            sys.exit(1)

        with open(args.input_file, 'r') as file:
            lines = file.readlines()

        for line in tqdm(lines, desc="Validating client IDs"):
            client_id = line.strip()
            if is_valid_client_id(client_id):
                url = f"https://accounts.google.com/gsi/select?client_id={client_id}&redirect_uri=https%3A%2F%2Fexample.com"
                process_url(url)
            else:
                print(f"{Fore.RED}Invalid client_id: {client_id}")

    elif args.url:
        process_url(args.url)
    else:
        print(f"{Fore.RED}Usage: gcid-extractor.py <URL> or gcid-extractor.py --input-file <file>")
        sys.exit(1)

if __name__ == "__main__":
    main()
