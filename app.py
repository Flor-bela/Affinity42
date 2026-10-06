from datetime import datetime
import streamlit as st
from api.forty_two import (
    fetch_logged_in_user,
    fetch_campus_peers,
    get_authorization_url,
    exchange_code_for_token,
)

st.set_page_config(page_title="Affinity42", page_icon="⚡", layout="wide")

def calcular_afinidad(proyectos_lista_a, proyectos_lista_b):
    proyectos_a = {p["name"]: p for p in proyectos_lista_a if p.get("name")}
    proyectos_b = {p["name"]: p for p in proyectos_lista_b if p.get("name")}
    
    comunes = set(proyectos_a.keys()).intersection(set(proyectos_b.keys()))
    
    if not comunes:
        return 0, []
        
    todos = set(proyectos_a.keys()).union(set(proyectos_b.keys()))
    indice_jaccard = len(comunes) / len(todos)
    
    bonus_tiempo = 0
    for proj in comunes:
        if proyectos_a[proj].get("marked_at") and proyectos_b[proj].get("marked_at"):
            try:
                # Recorte a 19 caracteres para evitar errores de parseo con la 'Z' y milisegundos
                fecha_a = datetime.fromisoformat(str(proyectos_a[proj]["marked_at"]).replace('Z', '+00:00')[:19])
                fecha_b = datetime.fromisoformat(str(proyectos_b[proj]["marked_at"]).replace('Z', '+00:00')[:19])
                
                diferencia_dias = abs((fecha_a - fecha_b).days)
                if diferencia_dias <= 30:
                    bonus_tiempo += 0.05
            except (ValueError, TypeError):
                pass
                
    afinidad_final = min((indice_jaccard + bonus_tiempo) * 100, 100)
    
    return round(afinidad_final, 2), list(comunes)


# --- OAuth2 Session Authentication Flow ---

if "user_token" not in st.session_state:
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.session_state["user_token"] = exchange_code_for_token(code)
        st.query_params.clear()
        st.rerun()

if "user_token" not in st.session_state:
    st.title("🤝 Affinity42")
    st.caption("Active Madrid campus ranked by affinity.")
    st.write("Please log in with your 42 Intra account to view campus affinity scores.")

    auth_url = get_authorization_url()
    st.markdown(f"[👉 **Login with 42 Intra**]({auth_url})")
    st.stop()


# --- App Execution (Logged In) ---

st.title("🤝 Affinity42")
st.caption("Active Madrid campus ranked by affinity.")

# Fetch active campus peers with populated project lists
peers = fetch_campus_peers(use_fake=False)
user = fetch_logged_in_user(use_fake=False, user_token=st.session_state["user_token"])

# Sidebar User Info
st.sidebar.markdown(f"### 👤 {user.get('displayname', user.get('login'))}")
st.sidebar.caption(f"@{user.get('login')}")

### 21 es el codigo de proyectos solo del cursus!!!
user_projects = []
for pu in user.get("projects_users", []):
    if 21 in pu.get("cursus_ids", []) and pu.get("validated?") is True:
        proj_name = pu.get("project", {}).get("name")
        if proj_name:
            user_projects.append({"name": proj_name, "marked_at": pu.get("marked_at")})

st.sidebar.write(f"**Your Student Projects ({len(user_projects)}):**")
for proj in user_projects:
    st.sidebar.info(f"⚪ `{proj['name']}`")

# Process & Rank Peers
ranked_peers = []
for peer in peers:
    peer_projects = []
    for pu in peer.get("projects_users", peer.get("projects", [])):
        cursus = pu.get("cursus_ids", [])
        is_validated = pu.get("validated?", True)
        
        if not cursus or 21 in cursus:
            if is_validated:
                proj_name = pu.get("project", {}).get("name") or pu.get("name")
                if proj_name:
                    peer_projects.append({"name": proj_name, "marked_at": pu.get("marked_at")})

    score, matches = calcular_afinidad(user_projects, peer_projects)
    
    ranked_peers.append({
        "login": peer.get("login"),
        "displayname": peer.get("displayname", peer.get("login")),
        "host": peer.get("host", "f1r2p3"),
        "score": score,
        "matches": matches,
    })

ranked_peers.sort(key=lambda x: x["score"], reverse=True)

# Render List View
st.subheader(f"Campus Peers Online ({len(ranked_peers)})")

for peer in ranked_peers:
    with st.container(border=True):
        col_info, col_bar = st.columns([3, 2], vertical_alignment="center")

        with col_info:
            st.markdown(f"### {peer['displayname']} `@{peer['login']}`")
            st.caption(f"📍 Location: **{peer['host']}**")

            if peer["matches"]:
                badges = " ".join([f"`{m}`" for m in peer["matches"]])
                st.markdown(f"**Overlapping Projects:** {badges}")
            else:
                st.caption("No directly overlapping student projects.")

        with col_bar:
            score = peer["score"]
            st.markdown(f"**Affinity: `{score}%`**")
            st.progress(score / 100.0)