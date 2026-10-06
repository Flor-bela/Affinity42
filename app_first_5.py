import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: Código no recibido", 400

    data = {
        'grant_type': 'authorization_code',
        'client_id': os.getenv('UID'),
        'client_secret': os.getenv('SECRET'),
        'code': code,
        'redirect_uri': 'http://localhost:3000/callback'
    }

    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        user_response = requests.get('https://api.intra.42.fr/v2/me', headers=headers)
        if user_response.status_code != 200:
            return "Fallo al obtener los datos del perfil", 500
        
        user_data = user_response.json()
        
        # Extraemos el ID de tu campus principal
        campus_id = user_data.get('campus')[0].get('id')

        # Consultamos las ubicaciones activas de tu campus
        locations_response = requests.get(f'https://api.intra.42.fr/v2/campus/{campus_id}/locations?filter[active]=true', headers=headers)
        if locations_response.status_code != 200:
            return "Fallo al obtener las ubicaciones del campus", 500
            
        locations = locations_response.json()
        
        active_users = [
            {
                "login": loc['user']['login'],
                "computer": loc.get('host')
            } 
            for loc in locations[:5]
        ]
        
        response_data = {
            "my_login": user_data.get("login"),
            "campus_id": campus_id,
            "active_users_sample": active_users,
            "total_active": len(locations)
        }
        
        return response_data
        
    return "Fallo al obtener el token de 42", 500

if __name__ == '__main__':
    app.run(port=3000)