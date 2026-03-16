import streamlit as st
from nba_api.stats.endpoints import leagueleaders
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time

st.set_page_config(page_title="NBA Player Comparator", page_icon="🏀", layout="wide")

NBA_BLUE = "#1D428A"
NBA_RED  = "#C8102E"

@st.cache_data
def load_data():
    leaders = leagueleaders.LeagueLeaders(season='2024-25')
    df = leaders.get_data_frames()[0]
    df['PPG'] = (df['PTS'] / df['GP']).round(1)
    df['APG'] = (df['AST'] / df['GP']).round(1)
    df['RPG'] = (df['REB'] / df['GP']).round(1)
    df['SPG'] = (df['STL'] / df['GP']).round(1)
    df['BPG'] = (df['BLK'] / df['GP']).round(1)
    df['FG%'] = (df['FG_PCT'] * 100).round(1)
    df['3P%'] = (df['FG3_PCT'] * 100).round(1)
    df['FT%'] = (df['FT_PCT'] * 100).round(1)
    return df

df = load_data()
player_names = sorted(df['PLAYER'].tolist())

st.title("🏀 NBA Player Comparator — 2024-25 Season")
st.markdown("Compare any two NBA players across key performance metrics.")

col1, col2 = st.columns(2)
with col1:
    name1 = st.selectbox("Player 1", player_names, index=player_names.index("Nikola Jokić"))
with col2:
    name2 = st.selectbox("Player 2", player_names, index=player_names.index("Giannis Antetokounmpo"))

if name1 == name2:
    st.warning("Please select two different players.")
    st.stop()

p1 = df[df['PLAYER'] == name1].iloc[0]
p2 = df[df['PLAYER'] == name2].iloc[0]

metrics = ['PPG', 'APG', 'RPG', 'SPG', 'BPG', 'FG%', '3P%', 'FT%']
labels  = ['Points', 'Assists', 'Rebounds', 'Steals', 'Blocks', 'FG%', '3P%', 'FT%']
v1 = [p1[m] for m in metrics]
v2 = [p2[m] for m in metrics]

# ── Stat cards ──
st.markdown("---")
cols = st.columns(len(metrics))
for i, (m, l) in enumerate(zip(metrics, labels)):
    with cols[i]:
        winner = NBA_BLUE if p1[m] >= p2[m] else NBA_RED
        st.metric(label=l, value=p1[m], delta=round(p1[m] - p2[m], 1))

# ── Charts ──
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor('#0a0a0a')

ax = axes[0]
ax.set_facecolor('#0a0a0a')
x     = range(len(labels))
width = 0.35
bars1 = ax.bar([i - width/2 for i in x], v1, width, color=NBA_BLUE, alpha=0.9, label=name1)
bars2 = ax.bar([i + width/2 for i in x], v2, width, color=NBA_RED,  alpha=0.9, label=name2)

for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height()}', ha='center', va='bottom', color='white', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height()}', ha='center', va='bottom', color='white', fontsize=8)

ax.set_xticks(list(x))
ax.set_xticklabels(labels, color='white', fontsize=10)
ax.set_ylabel('Value', color='white')
ax.set_title('Stat Comparison', color='white', fontsize=13, fontweight='bold')
ax.tick_params(colors='white')
ax.spines[:].set_color('#333333')
ax.legend(facecolor='#1a1a1a', labelcolor='white')

radar_metrics = ['PPG', 'APG', 'RPG', 'SPG', 'BPG', 'FG%']
radar_labels  = ['Points', 'Assists', 'Rebounds', 'Steals', 'Blocks', 'FG%']
N      = len(radar_metrics)
angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
angles += angles[:1]

def normalize(metric):
    col = df[metric]
    mn, mx = col.min(), col.max()
    return [(v - mn) / (mx - mn) if mx > mn else 0 for v in [p1[metric], p2[metric]]]

ax2 = plt.subplot(122, polar=True)
ax2.set_facecolor('#0a0a0a')
ax2.spines['polar'].set_color('#333333')
ax2.tick_params(colors='white')
ax2.set_xticks(angles[:-1])
ax2.set_xticklabels(radar_labels, color='white', fontsize=10)
ax2.yaxis.set_visible(False)

for idx, (player, color) in enumerate([(p1, NBA_BLUE), (p2, NBA_RED)]):
    vals  = [normalize(m)[idx] for m in radar_metrics]
    vals += vals[:1]
    ax2.plot(angles, vals, color=color, linewidth=2)
    ax2.fill(angles, vals, color=color, alpha=0.15)

p1_patch = mpatches.Patch(color=NBA_BLUE, label=name1)
p2_patch = mpatches.Patch(color=NBA_RED,  label=name2)
ax2.legend(handles=[p1_patch, p2_patch], loc='upper right',
           bbox_to_anchor=(1.3, 1.1), facecolor='#1a1a1a', labelcolor='white')
ax2.set_title('Normalized Radar', color='white', fontsize=13, fontweight='bold', pad=15)

plt.suptitle(f"{name1}  vs  {name2}", color='white', fontsize=15, fontweight='bold')
plt.tight_layout()
st.pyplot(fig)

# ── Raw stats table ──
st.markdown("---")
st.subheader("Full Stats")
display = pd.DataFrame({
    'Stat': labels,
    name1: v1,
    name2: v2,
    'Edge': [name1 if a >= b else name2 for a, b in zip(v1, v2)]
})
st.dataframe(display, use_container_width=True, hide_index=True)
