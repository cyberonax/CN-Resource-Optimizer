import streamlit as st, itertools, pandas as pd
from io import BytesIO

# Set default sidebar width using custom CSS.
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 800px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Main Resource Definitions (simplified values) ---
resources = {
    "Aluminum": {"population_bonus": 0, "land_bonus": 0, "infra_cost_reduction": 7, "soldier_efficiency": 20, "tech_cost_reduction": 0},
    "Cattle": {"population_bonus": 5, "land_bonus": 0, "land_cost_reduction": 10, "tech_cost_reduction": 0},
    "Coal": {"population_bonus": 0, "land_bonus": 15, "infra_cost_reduction": 4, "soldier_efficiency": 8, "tech_cost_reduction": 0},
    "Fish": {"population_bonus": 8, "land_cost_reduction": 5, "tech_cost_reduction": 0},
    "Furs": {"population_bonus": 0, "income_bonus": 3.5, "tech_cost_reduction": 0},
    "Gems": {"population_bonus": 0, "income_bonus": 1.5, "happiness": 2.5, "tech_cost_reduction": 0},
    "Gold": {"population_bonus": 0, "income_bonus": 3.0, "tech_cost_reduction": 5},
    "Iron": {"population_bonus": 0, "infra_cost_reduction": 5, "tech_cost_reduction": 0},
    "Lead": {"population_bonus": 0, "tech_cost_reduction": 0},
    "Lumber": {"population_bonus": 0, "infra_cost_reduction": 6, "tech_cost_reduction": 0},
    "Marble": {"population_bonus": 0, "infra_cost_reduction": 10, "tech_cost_reduction": 0},
    "Oil": {"population_bonus": 0, "soldier_efficiency": 10, "happiness": 1.5, "tech_cost_reduction": 0},
    "Pigs": {"population_bonus": 3.5, "soldier_efficiency": 15, "tech_cost_reduction": 0},
    "Rubber": {"population_bonus": 0, "land_bonus": 20, "land_cost_reduction": 10, "infra_cost_reduction": 3, "tech_cost_reduction": 0},
    "Silver": {"population_bonus": 0, "income_bonus": 2.0, "happiness": 2, "tech_cost_reduction": 0},
    "Spices": {"population_bonus": 0, "land_bonus": 8, "happiness": 2, "tech_cost_reduction": 0},
    "Sugar": {"population_bonus": 3, "happiness": 1, "tech_cost_reduction": 0},
    "Uranium": {"population_bonus": 0, "tech_cost_reduction": 0},
    "Water": {"population_bonus": 0, "happiness": 2.5, "tech_cost_reduction": 0},
    "Wheat": {"population_bonus": 8, "tech_cost_reduction": 0},
    "Wine": {"population_bonus": 0, "happiness": 3, "tech_cost_reduction": 0}
}

# --- Bonus Resource Detection & Benefits ---
def get_bonus_resources(combo):
    s = set(combo)
    bonus = []
    if {"Water", "Wheat", "Lumber", "Aluminum"}.issubset(s): bonus.append("Beer")
    if {"Lumber", "Iron", "Marble", "Aluminum"}.issubset(s): bonus.append("Construction")
    if {"Cattle", "Sugar", "Spices", "Pigs"}.issubset(s): bonus.append("Fast Food")
    if {"Gold", "Silver", "Gems", "Coal"}.issubset(s): bonus.append("Fine Jewelry")
    if {"Gold", "Lead", "Oil"}.issubset(s): bonus.append("Microchips")
    if {"Lumber", "Lead"}.issubset(s): bonus.append("Scholars")
    if {"Coal", "Iron"}.issubset(s): bonus.append("Steel")
    # Additional bonus resources:
    if {"Fish", "Furs", "Wine"}.issubset(s) and "Fine Jewelry" in bonus:
        bonus.append("Affluent Population")
    if {"Oil", "Rubber"}.issubset(s) and "Construction" in bonus:
        bonus.append("Asphalt")
    if "Asphalt" in bonus and "Steel" in bonus:
        bonus.append("Automobiles")
    if {"Construction", "Microchips", "Steel"}.issubset(s) or ({"Construction", "Microchips", "Steel"}.issubset(set(bonus))):
        bonus.append("Radiation Cleanup")
    return bonus

bonus_values = {
    "Beer": {"happiness": 2},
    "Construction": {"infra_cost_reduction": 5},
    "Fast Food": {"happiness": 2},
    "Fine Jewelry": {"happiness": 3},
    "Microchips": {"happiness": 2, "tech_cost_reduction": 8},
    "Scholars": {"income_bonus": 3.0},
    "Steel": {"infra_cost_reduction": 2},
    "Affluent Population": {"population_bonus": 5},
    "Asphalt": {"infra_cost_reduction": 5},
    "Automobiles": {"happiness": 3},
    "Radiation Cleanup": {"happiness": 1}
}

# --- Evaluate Combination ---
def evaluate_combination(combo, weights):
    keys = ["population_bonus", "land_bonus", "infra_cost_reduction", "soldier_efficiency", "income_bonus", "happiness", "tech_cost_reduction"]
    scores = {k: sum(resources[r].get(k, 0) for r in combo) for k in keys}
    base = sum(scores[k] * weights.get(k, 0) for k in keys)
    bonus_list = get_bonus_resources(combo)
    bonus_score = sum(bonus_values.get(b, {}).get(k, 0) * weights.get(k, 0)
                      for b in bonus_list for k in bonus_values.get(b, {}))
    total = base + bonus_score
    return {"combo": combo, **scores, "score": total, "bonus_resources": ", ".join(bonus_list) if bonus_list else ""}

@st.cache_data(show_spinner=True)
def compute_combinations(weights, require_uranium=True, desired_bonus_filter=None):
    # Generate all 12-resource combinations and filter if Uranium is required.
    combos = itertools.combinations(list(resources.keys()), 12)
    if require_uranium:
        combos = (c for c in combos if "Uranium" in c)
    evaluated = [evaluate_combination(c, weights) for c in combos]
    df = pd.DataFrame(evaluated)
    df["combo"] = df["combo"].apply(lambda x: ", ".join(x))
    # Filter by desired bonus resources, if provided.
    if desired_bonus_filter:
        def bonus_filter(row):
            if not row["bonus_resources"]:
                return False
            bonus_set = set(map(str.strip, row["bonus_resources"].split(",")))
            return set(desired_bonus_filter).issubset(bonus_set)
        df = df[df.apply(bonus_filter, axis=1)]
    return df.sort_values(by="score", ascending=False)

# --- Session State Initialization for Weights and Mode ---
if 'population_bonus' not in st.session_state:
    st.session_state.population_bonus = 2.0
if 'land_bonus' not in st.session_state:
    st.session_state.land_bonus = 2.0
if 'infra_cost_reduction' not in st.session_state:
    st.session_state.infra_cost_reduction = 1.0
if 'soldier_efficiency' not in st.session_state:
    st.session_state.soldier_efficiency = 1.0
if 'income_bonus' not in st.session_state:
    st.session_state.income_bonus = 1.5
if 'happiness' not in st.session_state:
    st.session_state.happiness = 1.0
if 'tech_cost_reduction' not in st.session_state:
    st.session_state.tech_cost_reduction = 1.0
if 'mode' not in st.session_state:
    st.session_state.mode = "Peace"
if 'nation_level_option' not in st.session_state:
    st.session_state.nation_level_option = "Default"

# --- Define Functions for Preset Configurations ---
def set_default_mode():
    st.session_state.population_bonus = 3.0
    st.session_state.land_bonus = 1.5
    st.session_state.infra_cost_reduction = 0.5
    st.session_state.soldier_efficiency = 0.5
    st.session_state.income_bonus = 2.0
    st.session_state.happiness = 3.0
    st.session_state.tech_cost_reduction = 1.0
    st.session_state.mode = "Default"

def set_peace_mode():
    set_default_mode()  # Start with default values.
    st.session_state.mode = "Peace"

def set_war_mode():
    st.session_state.population_bonus = 1.0
    st.session_state.land_bonus = 1.0
    st.session_state.infra_cost_reduction = 2.0
    st.session_state.soldier_efficiency = 3.0
    st.session_state.income_bonus = 1.0
    st.session_state.happiness = 0.5
    st.session_state.tech_cost_reduction = 2.0
    st.session_state.mode = "War"

def set_level_a():
    st.session_state.population_bonus = 2.0
    st.session_state.land_bonus = 2.0
    st.session_state.infra_cost_reduction = 1.5
    st.session_state.soldier_efficiency = 1.0
    st.session_state.income_bonus = 1.5
    st.session_state.happiness = 1.0
    st.session_state.tech_cost_reduction = 3.0

def set_level_b():
    st.session_state.population_bonus = 2.5
    st.session_state.land_bonus = 2.0
    st.session_state.infra_cost_reduction = 2.0
    st.session_state.soldier_efficiency = 1.0
    st.session_state.income_bonus = 1.5
    st.session_state.happiness = 1.0
    st.session_state.tech_cost_reduction = 1.5

def set_level_c():
    st.session_state.population_bonus = 3.0
    st.session_state.land_bonus = 2.0
    st.session_state.infra_cost_reduction = 2.5
    st.session_state.soldier_efficiency = 1.0
    st.session_state.income_bonus = 1.5
    st.session_state.happiness = 1.0
    st.session_state.tech_cost_reduction = 1.0

# --- Streamlit UI ---
st.title("Cyber Nations | Optimal Resource Combination Finder")

# Sidebar Controls
st.sidebar.markdown("## Settings")

# Row with Generate, Peace Mode, and War Mode Buttons.
col_gen, col_peace, col_war = st.sidebar.columns(3)

with col_gen:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    generate_pressed = st.button("GO")
    st.markdown("</div>", unsafe_allow_html=True)

with col_peace:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.button("Peace Mode", on_click=set_peace_mode)
    st.markdown("</div>", unsafe_allow_html=True)

with col_war:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.button("War Mode", on_click=set_war_mode)
    st.markdown("</div>", unsafe_allow_html=True)

# Show the "Use Custom Weightings" checkbox only if not in War mode.
if st.session_state.mode != "War":
    use_custom = st.sidebar.checkbox("Use Custom Weightings Instead of Nation Level Presets", value=False, key="use_custom")
else:
    use_custom = False

if st.session_state.mode in ["Peace", "Default"] and not use_custom:
    # Radio options include Default, Level A, Level B, and Level C.
    selected_level = st.sidebar.radio("Nation Level (Peace Mode)",
                                      ["Default", "Level A", "Level B", "Level C"],
                                      key="nation_level_option")
    if selected_level == "Default":
        set_default_mode()
    elif selected_level == "Level A":
        set_level_a()
    elif selected_level == "Level B":
        set_level_b()
    elif selected_level == "Level C":
        set_level_c()

# Weighting inputs, arranged in two columns.
st.sidebar.markdown("### Adjust Weighting Metrics")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.number_input("Population Bonus Weight", value=st.session_state.population_bonus, step=0.1, key="population_bonus")
    st.number_input("Land Bonus Weight", value=st.session_state.land_bonus, step=0.1, key="land_bonus")
    st.number_input("Infra Cost Reduction Weight", value=st.session_state.infra_cost_reduction, step=0.1, key="infra_cost_reduction")
with col2:
    st.number_input("Soldier Efficiency Weight", value=st.session_state.soldier_efficiency, step=0.1, key="soldier_efficiency")
    st.number_input("Income Bonus Weight", value=st.session_state.income_bonus, step=0.1, key="income_bonus")
    st.number_input("Happiness Weight", value=st.session_state.happiness, step=0.1, key="happiness")
    st.number_input("Tech Cost Reduction Weight", value=st.session_state.tech_cost_reduction, step=0.1, key="tech_cost_reduction")

# Bonus filter selection (default is empty).
st.sidebar.markdown("### Bonus Filter")
desired_bonuses = st.sidebar.multiselect("Select Desired Bonus Resources", list(bonus_values.keys()), default=[])

# Uranium toggle.
require_uranium = st.sidebar.checkbox("Require Uranium in combinations", value=True)

# Build the weights dictionary from session state.
weights = {
    "population_bonus": st.session_state.population_bonus,
    "land_bonus": st.session_state.land_bonus,
    "infra_cost_reduction": st.session_state.infra_cost_reduction,
    "soldier_efficiency": st.session_state.soldier_efficiency,
    "income_bonus": st.session_state.income_bonus,
    "happiness": st.session_state.happiness,
    "tech_cost_reduction": st.session_state.tech_cost_reduction
}

# If the generate button (in the presets row) is pressed, compute the combinations.
if generate_pressed:
    with st.spinner("Generating combinations..."):
        df_results = compute_combinations(weights, require_uranium, desired_bonus_filter=desired_bonuses)
    st.success("Combinations generated!")
    st.subheader("Top 10 Optimal Resource Combinations")
    st.dataframe(df_results.head(10))
    
    # Option to download the results.
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name="Results")
        writer.close()
        return output.getvalue()
    
    st.download_button("Download Results", data=to_excel(df_results),
                       file_name="CyberNations_Optimal_Resource_Combinations.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
