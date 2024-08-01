#How to connect to an API using Python

import requests

base_url = "https://pokeapi.co/api/v2"


def get_pokemon_info(name):
 url = f"{base_url}/pokemon/{name}"
 response = requests.get(url)

 if response.status_code == 200:
  pokemon_data = response.json()
  return pokemon_data
 else:
  print("Error: Failed to retrieve Pokemon data {response.status_code}")


pokemon_name = "ditto"
pokemon_info = get_pokemon_info(pokemon_name)

if pokemon_info:
 print(f"Name: {pokemon_info['name'].capitalize()}")
 print(f"ID: {pokemon_info['id']}")
 print(f"Height: {pokemon_info['height']}")
 print(f"Types: {pokemon_info['types']}")
