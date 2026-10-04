from datetime import datetime, date
import streamlit as st
from api.forty_two import fetch_logged_in_user, fetch_campus_peers

st.set_page_config(page_title="Affinity42", page_icon="⚡", layout="wide")


def compute_affinity(user_projects: list[str], peer_projects: list[dict]) -> tuple[int, list[str]]:
    """Calculates affinity score and identifies matching projects."""
    user_set = set(user_projects)
    matching = []
    score = 0.0
    today = date.today()

    for p in peer_projects:
        p_name = p.get("name")
        if p_name in user_set:
            matching.append(p_name)
            # Recency-based decay calculation if validation date exists
            if "validated_at" in p:
                val_date = datetime.strptime(p["validated_at"], "%Y-%m-%d").date()
                days_ago = max(0, (today - val_date).days)
                recency_weight = 100 * (1 / (1 + days_ago / 30))
                score += recency_weight
            else:
                score += 50.0

    final_score = min(int(round(score)), 100)
    return final_score, matching


# --- App Execution ---

st.title("⚡ Affinity42")
st.caption("Active Madrid campus alumni ranked by project affinity.")

# Load mock data via API layer
user = fetch_logged_in_user(use_fake=True)
peers = fetch_campus_peers(use_fake=True)

# Sidebar User Info
st.sidebar.markdown(f"### 👤 {user.get('displayname')}")
st.sidebar.caption(f"@{user.get('login')}")
st.sidebar.write("**Your Active Projects:**")
for proj in user.get("current_projects", []):
    st.sidebar.info(f"📂 `{proj}`")

# Process & Rank Peers
ranked_peers = []
for peer in peers:
    score, matches = compute_affinity(user.get("current_projects", []), peer.get("projects", []))
    ranked_peers.append({
        "login": peer.get("login"),
        "displayname": peer.get("displayname"),
        "host": peer.get("host", "f1r2p3"),  # Placeholder cluster host
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
                st.caption("No directly overlapping projects.")

        with col_bar:
            score = peer["score"]
            st.markdown(f"**Affinity: `{score}%`**")
            st.progress(score / 100.0)