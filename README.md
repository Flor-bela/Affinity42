Affinity42 🤝 (Project for Hackathon 42442 (Liga Nexus), 42Madrid)

*Affinity42* is a tool designed to help students at 42 find compatible peers, reinforcing the school's peer-to-peer philosophy. By analyzing completed cursus projects and their completion timestamps, Affinity42 calculates and visualizes an Affinity Index to match students with similar profiles, work rhythms, and fresh knowledge. Beyond forming future project teams, it connects students who have tackled the same challenges around the same time, making it easier to share struggles, exchange insights, and build a supportive community.

---

### 1. Team, Roles, and Time Tracking
| 42 Login | Team Member | Role & Responsibilities | Hours Invested |
| -------- | ----------- | ----------------------- | -------------- |
| `dstanimi` | Dobrin | Frontend. Streamlit architecture, API integration and user interface implementation. | `[XX]` hours |
| `durisosa` | Durian | Backend & Data. API integration, and organization. | `[XX]` hours |
| `fda-roch` | Flor | Backend & Data. Algorithm design (Affinity Index), API requests, and data structuring. | `[XX]` hours |
| `luolivei` | Lucas | Frontend & Presentation. Visuals, UI support, and project pitching (PPT). | `[XX]` hours |


---
Project Management:

Ideation & Prototyping: Brainstorming sessions to define the "problem" we wanted to solve and the core metric (Affinity Index).

Task Delegation: Tasks were split between Frontend (Data Visualization) and Backend (Data Gathering & Processing) to allow parallel work, but we all contributed with the ideas for the whole projects.

Version Control & Communication: Coordinated via GitHub for code integration and real-time communication.

---
### 2. The Problem & Our Solution

The "Pain Point"

At 42, choosing the right group for projects (like minishell, cub3d, etc.) is critical for success. However, students often struggle to find partners who share similar knowledge levels, work paces, and availability. Picking a partner randomly or based solely on friendship can lead to uneven workloads or scheduling conflicts.
The Solution: Affinity42
We built a web application that calculates a compatibility score between students. By filtering campus data (specifically Campus Madrid - code 22) and isolating active Cadets (excluding Piscine projects - code 21), we generate an accurate affinity matrix. This allows students to make data-driven decisions when forming teams, ensuring smoother collaboration.

---
### 3. How the Affinity Index Works
The core of our application is the Affinity Index, calculated using two main factors:
1. The Jaccard Index
We use the Jaccard similarity coefficient to measure the intersection of completed projects between two students.
$$J(A,B) = \frac{|A \cap B|}{|A \cup B|}$$

(Number of common projects / Total unique projects between both students)
![Jaccard Similarity](https://storage.googleapis.com/lds-media/images/jaccard_similarity.width-1200.jpg)

2. The "Bonus Time" Metric
Having the same projects is good, but having done them recently means the knowledge is fresh.
If both students finished a common project within 30 days of each other (<= 30 days difference), we add a 0.05 bonus to their index for that project.
Final Calculation
The final affinity index is transformed into a percentage:
$$\text{Final Index} = (\text{Jaccard Index} + \text{Total Bonus Time}) \times 100$$

-> Note: The maximum possible Affinity Index is capped at 100%, regardless of how many time bonuses are applied.

---
### 4. Setup & Installation
Follow these instructions to set up and run the project locally.
Prerequisites
Python 3.9+
42 API Credentials (`CLIENT_ID` and `CLIENT_SECRET`)
Installation Steps
Clone the repository:
```bash
   git clone https://github.com/Flor-bela/Affinity42
   cd Affinity42
   ```
Set up a virtual environment (recommended):
```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
Install the required dependencies:
Make sure you have the `requirements.txt` file which should include `streamlit`, `requests`, and `python-dotenv`.
```bash
   pip install -r requirements.txt
   ```
Environment Variables:
Create a `.env` file in the root directory and add your 42 API credentials:
```env
   UID_42=your_client_id_here
   SECRET_42=your_client_secret_here
   ```
Run the Application:
```bash
   streamlit run app.py
   ```
The app will automatically open in your default web browser (usually at `http://localhost:8501`).

---
### 5. Technical Challenges

42 API Rate Limits:
- Problem: Extracting data for all Cadets in Campus Madrid triggered the API's rate limits (requests per second/hour), causing timeouts.

Solution: We implemented a delay (sleep functions) with import time.

Data Filtering Complexity:
- Problem: Separating Piscine projects from core Cursus projects (code: 21) for each user was returning overlapping data arrays.

Solution: We built a strict filtering function before calculating the Jaccard index, ensuring only projects with `cursus_id == 21` (or the equivalent core cursus ID) were appended to the user's completed list.

Streamlit State Management:
- Problem: The app re-ran the entire script and API calls every time a user clicked a button or adjusted a filter, making it very slow.

Solution: We utilized Streamlit's `@st.cache_data` decorator to cache the heavy API payload and the Affinity Matrix calculation.
