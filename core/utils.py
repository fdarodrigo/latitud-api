import requests

def get_coordinates(endereço):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key=YOUR_API_KEY'.format(endereço)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['geometry']['location']
    return None

def fazer_web_scraping_do_imovel(url):
    # Faça web scraping do imóvel