import math
from datetime import datetime, date
import streamlit as st
from api.forty_two import (
    fetch_logged_in_user,
    fetch_campus_peers,
    get_authorization_url,
    exchange_code_for_token,
)

st.set_page_config(page_title="Affinity42", page_icon="⚡", layout="wide")

# 42 Core Cursus Project Complexity Weights (1.0 to 3.0 scale)
PROJECT_WEIGHTS = {
    # Tier 1: Foundation
    "libft": 1.0,
    "ft_printf": 1.0,
    "get_next_line": 1.0,
    "born2beroot": 1.2,
    
    # Tier 2: Intermediate
    "so_long": 1.5,
    "fdf": 1.5,
    "fract-ol": 1.5,
    "pipex": 1.8,
    "push_swap": 1.8,
    "minitalk": 1.8,
    
    # Tier 3: Core Milestones
    "minishell": 2.5,
    "philosophers": 2.2,
    "cub3d": 2.5,
    "miniRT": 2.5,
    "netpractice": 1.8,
    
    # Tier 4: Advanced C++ & Systems
    "cpp module 00": 1.2, "cpp module 01": 1.2, "cpp module 02": 1.2,
    "cpp module 03": 1.2, "cpp module 04": 1.2, "cpp module 05": 1.5,
    "cpp module 06": 1.5, "cpp module 07": 1.5, "cpp module 08": 1.8, "cpp module 09": 1.8,
    "ft_containers": 2.5,
    "webserv": 3.0,
    "ft_irc": 2.8,
    "ft_transcendence": 3.0,
}


def compute_affinity(user_projects: list[str], peer_projects: list[dict]) -> tuple[int, list[str]]:
    """Calculates an improved affinity score based on project complexity, status, and recency."""
    if not user_projects:
        return 0, []

    # Map normalized user project names
    user_map = {p.strip().lower(): p for p in user_projects if p}
    matching = []
    accumulated_weight = 0.0
    total_user_capacity = sum(PROJECT_WEIGHTS.get(p.strip().lower(), 1.5) for p in user_projects)

    today = date.today()

    for p in peer_projects:
        p_name = p.get("name")
        if not p_name:
            continue

        p_key = str(p_name).strip().lower()
        if p_key in user_map:
            matching.append(user_map[p_key])
            
            # Base weight for project complexity
            base_weight = PROJECT_WEIGHTS.get(p_key, 1.5)
            
            # Recency multiplier for validated projects
            recency_mult = 1.0
            if p.get("validated_at"):
                try:
                    val_date = datetime.strptime(p["validated_at"], "%Y-%m-%d").date()
                    days_ago = max(0, (today - val_date).days)
                    # Decays over ~6 months down to a baseline of 0.5x
                    recency_mult = 0.5 + (0.5 * (1 / (1 + days_ago / 180)))
                except ValueError:
                    recency_mult = 1.0

            # Bonus if peer is actively working on the same project
            status_bonus = 1.5 if p.get("status") == "in_progress" else 1.0

            accumulated_weight += base_weight * recency_mult * status_bonus

    if total_user_capacity == 0:
        return 0, []

    # Logarithmic scaling to prevent rapid saturation while keeping score 0-100%
    raw_ratio = accumulated_weight / total_user_capacity
    scaled_score = (math.log1p(raw_ratio) / math.log1p(2.0)) * 100.0

    final_score = min(int(round(scaled_score)), 100)
    return final_score, list(set(matching))


# --- OAuth2 Session Authentication Flow ---

if "user_token" not in st.session_state:
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.session_state["user_token"] = exchange_code_for_token(code)
        st.query_params.clear()
        st.rerun()

if "user_token" not in st.session_state:
    st.title("⚡ Affinity42")
    st.caption("Active Madrid campus alumni ranked by project affinity.")
    st.write("Please log in with your 42 Intra account to view campus affinity scores.")

    auth_url = get_authorization_url()
    st.markdown(f"[👉 **Login with 42 Intra**]({auth_url})")
    st.stop()


# --- App Execution (Logged In) ---

st.title("⚡ Affinity42")
st.caption("Active Madrid campus alumni ranked by project affinity.")

# Fetch active campus peers with populated project lists
peers = fetch_campus_peers(use_fake=False)
user = fetch_logged_in_user(use_fake=False, user_token=st.session_state["user_token"])

# Sidebar User Info
st.sidebar.markdown(f"### 👤 {user.get('displayname', user.get('login'))}")
st.sidebar.caption(f"@{user.get('login')}")

# Extract user's student projects (excluding Piscine)
raw_projects = user.get("projects_users", [])
user_projects = []

for pu in raw_projects:
    cursus_ids = pu.get("cursus_ids", [])
    proj_obj = pu.get("project", {})
    proj_name = proj_obj.get("name") if isinstance(proj_obj, dict) else str(pu)

    if 9 not in cursus_ids and proj_name:
        p_lower = str(proj_name).lower()
        if not (p_lower.startswith("c ") or p_lower.startswith("shell") or "piscine" in p_lower):
            user_projects.append(proj_name)

# Fallback if profile uses current_projects key
if not user_projects and "current_projects" in user:
    user_projects = user.get("current_projects", [])

st.sidebar.write(f"**Your Student Projects ({len(user_projects)}):**")
for proj in user_projects:
    st.sidebar.info(f"🏷️ `{proj}`")

# Process & Rank Peers
ranked_peers = []
for peer in peers:
    score, matches = compute_affinity(user_projects, peer.get("projects", []))
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