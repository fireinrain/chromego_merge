import datetime
import http.client
import random
import re
import socket
import ssl
import time
from urllib.parse import urlparse

import ping3
import requests

import utils


class IPChecker:
    @staticmethod
    def check_port_open(host: socket, port: str | int) -> bool:
        sock = None
        port = int(port)
        try:
            # Create a socket object
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set timeout to 1 second
            sock.settimeout(2.5)
            # Connect to the host and port
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f">>> Port {port} is open on {host}")
                return True
            else:
                print(f">>> Port {port} is closed on {host}")

        except Exception as e:
            print(f"Error checking port: {e}")
        finally:
            sock.close()
        return False

    @staticmethod
    def check_port_open_with_retry(host: socket, port: str | int, retry: int = 1) -> bool:
        for i in range(retry):
            with_retry = IPChecker.check_port_open(host, port)
            if with_retry:
                return True
            utils.random_sleep(15)
        return False

    @staticmethod
    def check_band_with_gfw_with_retry(host: str, port: str | int, check_count: int) -> bool:
        host = host.strip()
        if check_count <= 0:
            raise ValueError("min_pass must be smaller than check_count")
        for i in range(check_count):
            gfw = IPChecker.check_baned_with_gfw(host, port)
            if not gfw:
                return False
            time.sleep(15)
        # 使用v2接口再次检测一下
        ipv_ = utils.is_valid_ipv4(host)
        if not ipv_:
            host = utils.get_ip_address(host)
        is_ban = IPChecker.check_baned_with_gfw_v2(host, port)
        if not is_ban:
            return False
        return True

    # 检测ip端口是否被gfw ban
    @staticmethod
    def check_baned_with_gfw(host: str, port: str | int) -> bool:

        request_url = f"https://www.toolsdaquan.com/toolapi/public/ipchecking/{host}/{port}"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,ja;q=0.6",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.toolsdaquan.com/ipcheck/",
            "Sec-Ch-Ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"macOS\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest"
        }
        random_user_agent = IPChecker.get_random_user_agent()
        headers['User-Agent'] = random_user_agent

        try:
            resp = requests.get(request_url, headers=headers)
            resp.raise_for_status()

            response_data = resp.json()

            if response_data['icmp'] == "success" and response_data['tcp'] == "success":
                print(f">>> ip: {host}:{port} is ok in China!")
                return False
            else:
                print(f">>> ip: {host}:{port} is banned in China!")
                return True
        except Exception as e:
            print(">>> Error request for ban check:", e, "check_baned_with_gfw")
            return True

    @staticmethod
    def check_baned_with_gfw_v2(host: str, port: str | int) -> bool:
        import subprocess
        import json

        # 1716887992202
        timestamp_ = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        data = {
            "idName": f"itemblockid{timestamp_}",
            "ip": f"{host}"
        }
        random_user_agent = IPChecker.get_random_user_agent()

        curl_command = [
            'curl', 'https://www.vps234.com/ipcheck/getdata/',
            '-H', 'Accept: */*',
            '-H', 'Accept-Language: zh,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,ja;q=0.6',
            '-H', 'Cache-Control: no-cache',
            '-H', 'Connection: keep-alive',
            '-H', 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
            '-H', 'Origin: https://www.vps234.com',
            '-H', 'Pragma: no-cache',
            '-H', 'Referer: https://www.vps234.com/ipchecker/',
            '-H', 'Sec-Fetch-Dest: empty',
            '-H', 'Sec-Fetch-Mode: cors',
            '-H', 'Sec-Fetch-Site: same-origin',
            '-H',
            f'User-Agent: {random_user_agent}',
            '-H', 'X-Requested-With: XMLHttpRequest',
            '-H', 'sec-ch-ua: "Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            '-H', 'sec-ch-ua-mobile: ?0',
            '-H', 'sec-ch-ua-platform: "macOS"',
            '--data-raw', f'idName={data["idName"]}&ip={data["ip"]}'
        ]

        try:
            # Execute the curl command
            result = subprocess.run(curl_command, capture_output=True, text=True)

            # Print the output
            # print(result.stdout)
            response_data = json.loads(str(result.stdout))

            if response_data['data']['data']['innerTCP'] == True and response_data['data']['data'][
                'outTCP'] == True:
                print(f">>> ip: {host}:{port} is ok in China!")
                return False
            else:
                print(f">>> ip: {host}:{port} is banned in China!")
                return True
        except Exception as e:
            print(">>> Error request for ban check:", e, "check_baned_with_gfw_v2")
            return True

    @staticmethod
    def get_random_user_agent() -> str:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
        ]

        return random.choice(user_agents)

    @staticmethod
    def check_cloudflare_proxy(host: str, port: str | int, tls: bool = True) -> [bool, {}]:
        ip = host
        port = int(port)
        # Set the headers for the download request
        headers = {'Host': 'speed.cloudflare.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
                   }
        test_url = 'speed.cloudflare.com/cdn-cgi/trace'
        if tls:
            params = {'resolve': f"speed.cloudflare.com:{port}:{ip}", 'alpn': 'h2,http/1.1', 'utls': 'random'}

            url = f'https://{test_url}'
        else:
            params = {'resolve': f"speed.cloudflare.com:{port}:{ip}"}

            url = f'http://{test_url}'
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path:
            path = '/'
        if parsed_url.scheme != 'https' and parsed_url.scheme != 'http':
            return [False, {}]

        response = None
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=2500)
            # Calculate the total time taken for both operations
            total_duration = f'{(time.time() - start_time) * 1000:.2f}'
            print(f'Total tcp connection duration: {total_duration} ms')
            resp = response.text
            location = IPChecker.detect_cloudflare_location(host, port, resp, str(total_duration))
            if location is None:
                return [False, {}]
            return [True, location]
        except Exception as e:
            print(f">>> Connection failed of: {e}")
            return [False, {}]
        finally:
            if response:
                response.close()

    @staticmethod
    def check_if_cf_tls_proxy(ip: str, port: str):
        context = ssl.create_default_context()
        with socket.create_connection((ip, port)) as sock:
            with context.wrap_socket(sock, server_hostname="www.cloudflare.com") as ssock:
                cert = ssock.getpeercert()
                if 'subject' in cert:
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    # 检查证书的颁发者信息和主题信息是否包含Cloudflare相关的字符串
                    if 'cloudflare' in str(subject) or 'cloudflare' in str(issuer):
                        return True
                return False

    @staticmethod
    # Function to get the ping and jitter of an IP address
    def get_ping(ip: str, acceptable_ping: int):
        """
        Args:
        ip (str): IP of Cloudflare Network to test its upload speed.
        acceptable_ping (float): The minimum acceptable download speed.

        Returns:
        int: The latency in milliseconds.
        int: The jitter in milliseconds.
        """

        # Calculate the timeout for requested minimum ping time
        timeout = int(acceptable_ping / 1000)
        try:
            # Start the timer for the download request
            start_time = time.time()
            # Get response time of the ping request
            response_time = ping3.ping(ip, timeout=timeout)
            # Calculate spent time for fallback
            duration = int((time.time() - start_time) * 1000)
            # Calculate the ping in milliseconds
            ping = int(response_time * 1000) if response_time is not None and response_time > 0 else duration
        except Exception as e:
            ping = -1

        # Return ping and jitter in milliseconds
        return ping

    @staticmethod
    # Function to get the latency of an IP address
    def get_latency_jitter(ip: str, acceptable_latency: float, enable_ssl: bool = True) -> []:
        """
        Args:
        ip (str): IP of Cloudflare Network to test its upload speed.
        acceptable_latency (float): The minimum acceptable download speed.

        Returns:
        int: The latency in milliseconds.
        """

        openssl_is_active = enable_ssl

        # An small data to download to calculate latency
        download_size = 1000
        # Calculate the timeout for requested minimum latency
        timeout = acceptable_latency / 1000 * 1.5
        # Set the URL for the download request
        url = f"https://speed.cloudflare.com/__down?bytes={download_size}"
        # Set the headers for the download request
        headers = {'Host': 'speed.cloudflare.com'}
        # Set the parameters for the download request
        if openssl_is_active:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}", 'alpn': 'h2,http/1.1', 'utls': 'random'}
        else:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}"}

        latency = 0
        jitter = 0
        last_latency = 0
        try:
            for i in range(3):
                # Start the timer for the download request
                start_time = time.time()
                # Send the download request and get the response
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
                # Calculate the latency in milliseconds
                current_latency = int((time.time() - start_time) * 1000)
                latency = latency + current_latency
                timeout = acceptable_latency / 1000

                if i > 0:
                    jitter = jitter + abs(current_latency - last_latency)

                last_latency = current_latency

            latency = int(latency / 4)
            jitter = int(jitter / 3)
        except requests.exceptions.RequestException as e:
            # If there was an exception, set latency to 99999 and jitter to -1
            latency = 99999
            jitter = -1

        # Return latency in milliseconds
        return latency, jitter

    @staticmethod
    # Function to get the download speed of an IP address
    def get_download_speed(ip: str, data_size: int, min_speed: float, enable_ssl: bool = True):
        """
        Args:
        ip (str): IP of Cloudflare Network to test its upload speed.
        size (int): Size of sample data to download for speed test.
        min_speed (float): The minimum acceptable download speed.

        Returns:
        float: The download speed in Mbps.
        """

        openssl_is_active = enable_ssl

        # Convert size from KB to bytes
        download_size = data_size * 1024
        # Convert minimum speed from Mbps to bytes/s
        min_speed_bytes = min_speed * 125000  # 1 Mbps = 125000 bytes/s
        # Calculate the timeout for the download request
        timeout = download_size / min_speed_bytes
        # Set the URL for the download request
        url = f"https://speed.cloudflare.com/__down?bytes={download_size}"
        # Set the headers for the download request
        headers = {'Host': 'speed.cloudflare.com'}
        # Set the parameters for the download request
        if openssl_is_active:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}", 'alpn': 'h2,http/1.1', 'utls': 'random'}
        else:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}"}
        try:
            # Start the timer for the download request
            start_time = time.time()
            # Send the download request and get the response
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            # Calculate the download time
            download_time = time.time() - start_time
            # Calculate the download speed in Mbps
            download_speed = round(download_size / download_time * 8 / 1000000, 2)
        except requests.exceptions.RequestException as e:
            # If there was an exception, set download speed to 0
            download_speed = 0

            # Return the download speed in Mbps
        return download_speed

    @staticmethod
    # Function to get the upload speed of an IP address
    def get_upload_speed(ip: str, data_size: int, min_speed: float, enable_ssl: bool = True):
        """
        Args:
        ip (str): IP of Cloudflare Network to test its upload speed.
        size (int): Size of sample data to upload for speed test.
        min_speed (float): The minimum acceptable upload speed.

        Returns:
        float: The upload speed in Mbps.
        """

        openssl_is_active = enable_ssl

        # Calculate the upload size, which is 1/4 of the download size to save bandwidth
        upload_size = int(data_size * 1024 / 4)
        # Calculate the minimum speed in bytes per second
        min_speed_bytes = min_speed * 125000  # 1 Mbps = 125000 bytes/s
        # Calculate the timeout for the request based on the upload size and minimum speed
        timeout = upload_size / min_speed_bytes
        # Set the URL, headers, and parameters for the request
        url = 'https://speed.cloudflare.com/__up'
        headers = {'Content-Type': 'multipart/form-data', 'Host': 'speed.cloudflare.com'}
        if openssl_is_active:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}", 'alpn': 'h2,http/1.1', 'utls': 'random'}
        else:
            params = {'resolve': f"speed.cloudflare.com:443:{ip}"}

        # Create a sample file with null bytes of the specified size
        files = {'file': ('sample.bin', b"\x00" * upload_size)}

        try:
            # Send the request and measure the upload time
            start_time = time.time()
            response = requests.post(url, headers=headers, params=params, files=files, timeout=timeout)
            upload_time = time.time() - start_time
            # Calculate the upload speed in Mbps
            upload_speed = round(upload_size / upload_time * 8 / 1000000, 2)
        except requests.exceptions.RequestException as e:
            # If an error occurs, set the upload speed to 0
            upload_speed = 0

            # Return the upload speed in Mbps
        return upload_speed

    import socket

    @staticmethod
    def check_udp_service(ip, port, message, timeout=5):
        """
        检查UDP服务是否可达。

        :param ip: 服务器的IP地址
        :param port: 服务器的端口号
        :param message: 发送到服务器的消息
        :param timeout: 超时时间，单位为秒
        :return: 如果接收到响应，返回响应数据，否则返回None
        """
        client_socket = None
        try:
            # 创建一个UDP套接字
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.settimeout(timeout)

            # 发送消息到指定的IP和端口
            client_socket.sendto(message, (ip, port))

            # 等待服务器响应
            response, server = client_socket.recvfrom(4096)
            return response.decode()

        except socket.timeout:
            print("请求超时")
            return None

        except Exception as e:
            print(f"发生错误: {e}")
            return None

        finally:
            client_socket.close()


if __name__ == '__main__':
    # 使用示例
    ip = '62.210.243.131'  # 目标服务器IP地址
    port = 18702  # 目标服务器端口号
    message = b''  # 发送的消息

    response = IPChecker.check_udp_service(ip, port, message)
    if response:
        print(f"接收到服务器响应: {response}")
    else:
        print("未能接收到服务器响应")
