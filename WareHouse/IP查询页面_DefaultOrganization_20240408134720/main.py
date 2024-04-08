'''
This is the main file of the console program to query IP address information.
'''
import requests
class IPQueryError(Exception):
    pass
def get_ip_info(ip):
    """
    Function to query IP address information using the ip-api.com API.
    Args:
        ip (str): The IP address to query.
    Returns:
        dict: The IP address information as a dictionary.
    Raises:
        IPQueryError: If an error occurs while querying or parsing the response.
    """
    url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for any HTTP errors
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        raise IPQueryError(f"Error occurred while querying IP address: {e}")
    except ValueError as e:
        raise IPQueryError(f"Error occurred while parsing response JSON: {e}")
def print_ip_info(ip_info):
    """
    Function to print the IP address information.
    Args:
        ip_info (dict): The IP address information as a dictionary.
    """
    try:
        if ip_info is None:
            print("No IP address information available.")
            return
        print("IP Address Information:")
        print(f"IP: {ip_info['query']}")
        print(f"Country: {ip_info['country']}")
        print(f"Region: {ip_info['regionName']}")
        print(f"City: {ip_info['city']}")
        print(f"ISP: {ip_info['isp']}")
        print(f"Organization: {ip_info['org']}")
        print(f"AS: {ip_info['as']}")
        print(f"Latitude: {ip_info['lat']}")
        print(f"Longitude: {ip_info['lon']}")
    except IPQueryError as e:
        print(f"Error occurred while printing IP address information: {e}")
def main():
    """
    Main function to run the console program.
    """
    ip = input("Enter IP address: ")
    try:
        ip_info = get_ip_info(ip)
        print_ip_info(ip_info)
    except IPQueryError as e:
        print(f"Error occurred while querying IP address: {e}")
if __name__ == "__main__":
    main()