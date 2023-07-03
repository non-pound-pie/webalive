import sys
import argparse
from concurrent.futures import ThreadPoolExecutor
import requests


def is_listening(url, method):
    try:
        headers = {"Connection": "close"}
        response = requests.request(method, url, headers=headers, timeout=10)
        response.close()
        return True
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Port checker")
    parser.add_argument("-c", type=int, default=20, help="set the concurrency level (split equally between HTTPS and HTTP requests)")
    parser.add_argument("-p", action="append", dest="probes", help="add additional probe (proto:port)")
    parser.add_argument("-s", action="store_true", help="skip the default probes (http:80 and https:443)")
    parser.add_argument("-t", type=int, default=10000, help="timeout (milliseconds)")
    parser.add_argument("--prefer-https", action="store_true", help="only try plain HTTP if HTTPS fails")
    parser.add_argument("--method", default="GET", help="HTTP method to use")

    args = parser.parse_args()

    concurrency = args.c
    probes = args.probes or []
    skip_default = args.s
    timeout = args.t / 1000
    prefer_https = args.prefer_https
    method = args.method

    https_urls = []
    http_urls = []
    output = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for line in sys.stdin:
            domain = line.strip().lower()

            if not skip_default:
                https_urls.append(domain)

            for p in probes:
                if ":" not in p:
                    continue

                proto, port = p.split(":", 1)
                if proto.lower() == "https":
                    https_urls.append(f"{domain}:{port}")
                else:
                    http_urls.append(f"{domain}:{port}")

        def process_url(url):
            if url.startswith("https://"):
                with_proto = url
                if is_listening(with_proto, method):
                    output.append(with_proto)

                    if prefer_https:
                        return

            if url.startswith("http://"):
                with_proto = url
                if is_listening(with_proto, method):
                    output.append(with_proto)

        executor.map(process_url, https_urls)
        executor.map(process_url, http_urls)

    for o in output:
        print(o)


if __name__ == "__main__":
    main()