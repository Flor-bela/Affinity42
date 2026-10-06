import os
import requests
from flask import Flask, request, redirect
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

def calcular_afinidad(perfil_a, perfil_b):
    proyectos_a = {p["name"]: p for p in perfil_a["validated_projects"]}
    proyectos_b = {p["name"]: p for p in perfil_b["validated_projects"]}
    
    comunes = set(proyectos_a.keys()).intersection(set(proyectos_b.keys()))
    
    if not comunes:
        return {"porcentaje_afinidad": 0, "proyectos_en_comun": []}
        
    todos = set(proyectos_a.keys()).union(set(proyectos_b.keys()))
    indice_jaccard = len(comunes) / len(todos)
    
    bonus_tiempo = 0
    for proj in comunes:
        if proyectos_a[proj].get("marked_at") and proyectos_b[proj].get("marked_at"):
            fecha_a = datetime.fromisoformat(proyectos_a[proj]["marked_at"].replace('Z', '+00:00'))
            fecha_b = datetime.fromisoformat(proyectos_b[proj]["marked_at"].replace('Z', '+00:00'))
            
            diferencia_dias = abs((fecha_a - fecha_b).days)
            if diferencia_dias <= 30:
                bonus_tiempo += 0.05
            
    afinidad_final = min((indice_jaccard + bonus_tiempo) * 100, 100)
    
    return {
        "porcentaje_afinidad": round(afinidad_final, 2),
        "proyectos_en_comun": list(comunes)
    }

@app.route('/login')
def login():
    uid = os.getenv('UID')
    redirect_uri = 'http://localhost:3000/callback'
    url_autorizacion = f"https://api.intra.42.fr/oauth/authorize?client_id={uid}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(url_autorizacion)

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
            
            # Madrid id 22?? 
            campus_id = 22 
            
            perfil_a = {
                "login": user_data.get("login"),
                "validated_projects": [
                    {"name": p["project"]["name"], "final_mark": p.get("final_mark"), "marked_at": p.get("marked_at")}
                    for p in user_data.get("projects_users", [])
                    if p.get("validated?") is True and 21 in p.get("cursus_ids", [])
                ]
            }

            locations_url = f'https://api.intra.42.fr/v2/campus/{campus_id}/locations?filter[active]=true'
            locations_response = requests.get(locations_url, headers=headers)
            
            if locations_response.status_code != 200:
                return f"Fallo al obtener ubicaciones del campus: {locations_response.text}", 500
                
            active_locations = locations_response.json()
            resultados = []

            for loc in active_locations[:10]: # solo 10 por ahora
                other_login = loc['user']['login']
                
                if other_login == perfil_a["login"]:
                    continue

                other_response = requests.get(f'https://api.intra.42.fr/v2/users/{other_login}', headers=headers)
                
                if other_response.status_code == 200:
                    other_data = other_response.json()
                    
                    # grade: cadete
                    es_cadete = any(c.get("cursus", {}).get("id") == 21 for c in other_data.get("cursus_users", []))
                    if not es_cadete:
                        continue
                    
                    perfil_b = {
                        "login": other_login,
                        "validated_projects": [
                            {"name": p["project"]["name"], "final_mark": p.get("final_mark"), "marked_at": p.get("marked_at")}
                            for p in other_data.get("projects_users", [])
                            if p.get("validated?") is True
                        ]
                    }
                    
                    afinidad = calcular_afinidad(perfil_a, perfil_b)
                    
                    resultados.append({
                        "usuario": other_login,
                        "puesto": loc.get('host'),
                        "afinidad": afinidad
                    })
            
            return {
                "mi_perfil": perfil_a["login"],
                "campus_usado": campus_id,
                "resultados_afinidad": resultados
            }
        
        return "Fallo al obtener los datos del perfil", 500
        
    return "Fallo al obtener el token de 42", 500

if __name__ == '__main__':
    app.run(port=3000)