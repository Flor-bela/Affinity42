import os
import requests
import time
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


            active_locations = []
            page = 1
            while True:
                loc_url = f'https://api.intra.42.fr/v2/campus/{campus_id}/locations?filter[active]=true&page[size]=100&page[number]={page}'
                res = requests.get(loc_url, headers=headers)
                if res.status_code != 200:
                    break
                data = res.json()
                if not data:
                    break
                active_locations.extend(data)
                page += 1
                time.sleep(0.5) # Evitar Rate Limit de 42 (2 req/sec)


            user_info = {}
            for loc in active_locations:
                uid = loc['user']['id']
                login = loc['user']['login']
                if login == perfil_a["login"]:
                    continue
                user_info[uid] = {"login": login, "puesto": loc['host'], "projects": []}

            user_ids = list(user_info.keys())
            chunk_size = 50
            
            for i in range(0, len(user_ids), chunk_size):
                chunk = user_ids[i:i + chunk_size]
                ids_str = ",".join(map(str, chunk))
                
                p_page = 1
                while True:
                    p_url = f"https://api.intra.42.fr/v2/projects_users?filter[user_id]={ids_str}&filter[cursus]=21&filter[validated]=true&page[size]=100&page[number]={p_page}"
                    p_res = requests.get(p_url, headers=headers)
                    if p_res.status_code != 200:
                        break
                    
                    p_data = p_res.json()
                    if not p_data:
                        break
                        
                    for pu in p_data:
                        uid = pu['user']['id']
                        if uid in user_info:
                            user_info[uid]["projects"].append({
                                "name": pu["project"]["name"],
                                "final_mark": pu.get("final_mark"),
                                "marked_at": pu.get("marked_at")
                            })
                            
                    p_page += 1
                    time.sleep(0.5)

            # 4. Calcular afinidades
            resultados = []
            for uid, info in user_info.items():
                if not info["projects"]:
                    continue # Probablemente de piscina o sin proyectos en cursus 21
                
                perfil_b = {
                    "login": info["login"],
                    "validated_projects": info["projects"]
                }
                
                afinidad = calcular_afinidad(perfil_a, perfil_b)
                
                resultados.append({
                    "login": info["login"],
                    "afinidad": afinidad["porcentaje_afinidad"],
                    "puesto": info["puesto"],
                    "proyectos_en_comun": afinidad["proyectos_en_comun"]
                })

            # 5. Ordenar y sacar el top 10
            resultados.sort(key=lambda x: x["afinidad"], reverse=True)
            top_10_frontend = resultados[:10]

            return {
                "mi_perfil": perfil_a["login"],
                "campus_usado": campus_id,
                "resultados_afinidad": top_10_frontend
            }

        return "Fallo al obtener los datos del perfil", 500

    return "Fallo al obtener el token de 42", 500

if __name__ == '__main__':
    app.run(port=3000)