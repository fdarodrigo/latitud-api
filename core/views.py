# No seu arquivo views.py do app "core"
from urllib.parse import urlparse
import httpx
import aiohttp
import asyncio
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
from .models import Imovel
import re

from urllib.parse import urlparse

import time

import googlemaps

def has_token(url):
    url_parts = urlparse(url.decode('utf-8')) if isinstance(url, bytes) else urlparse(url)
    path_parts = url_parts.path.decode('utf-8').split('/') if isinstance(url_parts.path, bytes) else url_parts.path.split('/')

    if len(path_parts) > 4 and path_parts[4] is not None:
        print('aqui > ', path_parts[4])
        return path_parts[4]
    else:
        print('aqui > ', 'nada')
        False
    # O token está entre o 7º e o 8º parâmetro
    """ if len(path_parts) >= 8:
        print('true')
        return path_parts[7] != ''
    else:
        print('false')
        return False """
    
def process_description(description):
    # Remove case sensitive
    description = description.lower()

    # Substitui espaços por '-'
    description = description.replace(' ', '-')

    # Remove a potência 2 quando for 'm2'
    description = re.sub(r'(\d+)\s*m²', r'\1', description)

    return description



async def wait_and_get_image_url(session, url_imagem_html):
    # Aguarda até que a URL esteja no formato correto
    for _ in range(10):  # Tentativas em um intervalo de 1 segundo
        # Verifica se a tag 'img' existe e possui o atributo 'data-src'
        if url_imagem_html and 'data-src' in url_imagem_html.find(class_='js-carousel-image').attrs:
            data_src = url_imagem_html.find(class_='js-carousel-image')['data-src']
            print('Deu certo > ', data_src)
        else:
            data_src = None
            print('Não deu certo > ', data_src)
        # Verifica se a URL está no formato desejado com o token
        token = has_token(data_src)
        if token:
            print(f"Token encontrado: {token}")
            # Monta a URL com os valores fixos
            action = "crop"
            width = "360"
            height = "240"
            description = url_imagem_html.find('img')['alt'] if url_imagem_html and url_imagem_html.find('img') else None
            description = process_description(description)

            full_url = f"https://resizedimgs.vivareal.com/{action}/{width}x{height}/named.images.sp/{token}/{description}.jpg"
            print('URL COMPLETA > ', full_url)
            return full_url
        else:
            print("Token não encontrado.")
            print("Ainda não deu certo de novo")

        await asyncio.sleep(1)  # Aguarda 1 segundo antes de verificar novamente

    return None  # Retorna None se a URL não estiver no formato correto após 10 segundos





async def web_scrape(request):
    google_maps_api_key = 'AIzaSyD4-3Bwj1uGRs3ukl2pfEQOkjiXi75GRCo'  # Substitua pelo sua chave
    gmaps = googlemaps.Client(key=google_maps_api_key)


    base_url = 'https://www.vivareal.com.br/aluguel/ceara/fortaleza/'

    # Número máximo de páginas que você deseja percorrer
    max_pages = 3

    result = {'data': [], 'status': 'NOK'}

    for page_number in range(1, max_pages + 1):
        url = f'{base_url}?pagina={page_number}#onde=Brasil,Ceará,Fortaleza,,,,,,BR>Ceara>NULL>Fortaleza,,,'

        response = requests.get(url)

        # Verifica se a resposta foi bem-sucedida (código 200)
        if response.status_code == 200:
            result['status'] = 'OK'

            soup = BeautifulSoup(response.text, 'html.parser')

            # Realize o parsing da página HTML e colete as informações necessárias
            imoveis_html = soup.select('.js-results-list article')
            if len(imoveis_html) == 0:
                print("Não há imóveis com a propriedade 'data-type' de valor 'property'")
            else:
                print("Foram encontrados", len(imoveis_html), "imóveis")

            async with httpx.AsyncClient() as client:
                for imovel_html in imoveis_html:
                    #print(imovel_html.prettify())
                    # Coleta as informações

                    # Verifica se a informação de área está presente
                    area_html = imovel_html.find(class_='property-card__detail-area')
                    area = int(area_html.find(class_='js-property-card-detail-area').text.strip()) if area_html and area_html.find(class_='js-property-card-value') else None

                    quartos_html = imovel_html.find(class_='js-property-detail-rooms')
                    quartos_text = quartos_html.find(class_='js-property-card-value').text.strip() if quartos_html else None
                    quartos = int(quartos_text) if quartos_text != '--' else None


                    banheiros_html = imovel_html.find(class_='js-property-detail-bathroom')
                    banheiros_text = banheiros_html.find(class_='js-property-card-value').text.strip() if banheiros_html else None
                    banheiros = int(banheiros_text) if banheiros_text and banheiros_text != '--' else None


                    vagas_html = imovel_html.find(class_='js-property-detail-garages')
                    vagas_text = vagas_html.find(class_='js-property-card-value').text.strip() if vagas_html else None
                    vagas = int(vagas_text) if vagas_text and vagas_text != '--' else None


                    valor_aluguel_html = imovel_html.find('div', class_='js-property-card__price-small')
                    valor_aluguel_text = valor_aluguel_html.find('p') if valor_aluguel_html else None
                    if valor_aluguel_text:
                        valor_aluguel_text = valor_aluguel_text.text.strip()
                        valor_aluguel_match = re.search(r'\d+\.\d+', valor_aluguel_text)
                        if valor_aluguel_match:
                            valor_aluguel = format(float(valor_aluguel_match.group(0)), '.3f')
                        else: 
                            valor_aluguel = None
                    else:
                        valor_aluguel = None

                    url_imagem_html = imovel_html.find(class_='carousel__item-wrapper')
                    url_imagem = await wait_and_get_image_url(client, url_imagem_html)

                    url_detalhes_html = imovel_html.find(class_='property-card__content-link')
                    url_detalhes = url_detalhes_html['href'] if url_detalhes_html else None

                    amenidades_html = imovel_html.find_all(class_='amenities__item')
                    amenidades = [amenidade.text.strip() for amenidade in amenidades_html]

                    description = url_imagem_html.find('img')['alt'] if url_imagem_html and url_imagem_html.find('img') else None

                    endereco = imovel_html.find(class_='property-card__address').text.strip()

                    geocode_result = gmaps.geocode(endereco)

                    # Verifique se a geocodificação foi bem-sucedida
                    if geocode_result:
                        # Obtenha as coordenadas
                        coords = geocode_result[0]['geometry']['location']
                        lat = coords['lat']
                        lng = coords['lng']

                        # Adicione as coordenadas ao resultado
                        result['data'].append({
                            'endereco': endereco,
                            'quartos': quartos,
                            'banheiros': banheiros,
                            'vagas': vagas,
                            'area': area,
                            'valor_aluguel': valor_aluguel,
                            'url_imagem': url_imagem,
                            'url_detalhes': url_detalhes,
                            'amenidades': amenidades,
                            'descricao': description,
                            'coords': {'lat': lat, 'lng': lng}  # Adiciona as coordenadas
                        })

    # Retorna o objeto JSON
    return JsonResponse(result)

# Restante do código...
