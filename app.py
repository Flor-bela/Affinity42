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
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            
            profile_summary = {
                "login": user_data.get("login"),
                "location": user_data.get("location"),
                "image": user_data.get("image", {}).get("link"),
                "validated_projects": [
                    {
                        "name": p["project"]["name"],
                        "final_mark": p.get("final_mark")
                    }
                    for p in user_data.get("projects_users", [])
                    if p.get("validated?") is True
                ]
            }
            
            return profile_summary
        
        return "Fallo al obtener los datos del perfil", 500
        
    return "Fallo al obtener el token de 42", 500

if __name__ == '__main__':
    app.run(port=3000)