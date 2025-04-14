import streamlit as st, itertools, pandas as pd
from io import BytesIO

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
    bonus_score = sum(bonus_values.get(b, {}).get(k, 0) * weights.get(k, 0) for b in bonus_list for k in bonus_values.get(b, {}))
    total = base + bonus_score
    return {"combo": combo, **scores, "score": total, "bonus_resources": ", ".join(bonus_list) if bonus_list else ""}

@st.cache_data(show_spinner=True)
def compute_combinations(weights, require_uranium=True, desired_bonus_filter=None):
    # Generate all 12-resource combinations and filter if Uranium is required
    combos = itertools.combinations(list(resources.keys()), 12)
    if require_uranium:
        combos = (c for c in combos if "Uranium" in c)
    evaluated = [evaluate_combination(c, weights) for c in combos]
    df = pd.DataFrame(evaluated)
    df["combo"] = df["combo"].apply(lambda x: ", ".join(x))
    # --- Filter by desired bonus resources if provided ---
    if desired_bonus_filter:
        def bonus_filter(row):
            if not row["bonus_resources"]:
                return False
            bonus_set = set(map(str.strip, row["bonus_resources"].split(",")))
            return set(desired_bonus_filter).issubset(bonus_set)
        df = df[df.apply(bonus_filter, axis=1)]
    return df.sort_values(by="score", ascending=False)

# --- Optimize Weights Function ---
def optimize_weights(desired_bonuses):
    """
    Compute a suggested weight configuration based on the selected bonus resources.
    This function starts with a baseline weight of 1.0 for all metrics,
    then adds the bonus contribution values for each selected bonus.
    """
    # Baseline weights
    new_weights = {
        "population_bonus": 1.0,
        "land_bonus": 1.0,
        "infra_cost_reduction": 1.0,
        "soldier_efficiency": 1.0,
        "income_bonus": 1.0,
        "happiness": 1.0,
        "tech_cost_reduction": 1.0
    }
    for bonus in desired_bonuses:
        bonus_metrics = bonus_values.get(bonus, {})
        for key, value in bonus_metrics.items():
            new_weights[key] += value
    return new_weights

# --- Initialize Session State for Weight Parameters and Mode ---
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
    st.session_state.mode = "Peace"  # Default mode is Peace Mode
if 'nation_level_option' not in st.session_state:
    st.session_state.nation_level_option = "Level A"  # Default for Peace Mode

# --- Define Functions for Preset Weight Configurations ---

def set_peace_mode():
    st.session_state.population_bonus = 3.0    # Focus on citizen growth (default for Peace Mode)
    st.session_state.land_bonus = 1.5          # Modest land bonus
    st.session_state.infra_cost_reduction = 0.5  # Lower priority for construction speed
    st.session_state.soldier_efficiency = 0.5    # Minimal military focus
    st.session_state.income_bonus = 2.0        # Higher emphasis on income
    st.session_state.happiness = 3.0           # Emphasis on happiness
    st.session_state.tech_cost_reduction = 1.0  # Average technology benefit
    st.session_state.mode = "Peace"            # Set mode to Peace

def set_war_mode():
    st.session_state.population_bonus = 1.0    # Lower emphasis on growing citizens
    st.session_state.land_bonus = 1.0          # Moderate land bonus
    st.session_state.infra_cost_reduction = 2.0  # Enhanced infrastructure efficiency for rapid buildup
    st.session_state.soldier_efficiency = 3.0    # Maximum military focus
    st.session_state.income_bonus = 1.0        # Income is less prioritized
    st.session_state.happiness = 0.5           # Happiness is lower priority
    st.session_state.tech_cost_reduction = 2.0  # Greater focus on reducing tech cost
    st.session_state.mode = "War"              # Set mode to War

# New functions for nation-level presets (for Peace Mode only)
def set_level_a():
    # For Level A (<1000 Days Old Tech Sellers)
    st.session_state.population_bonus = 2.0      # Lower emphasis on citizen growth compared to buyers
    st.session_state.land_bonus = 2.0              # Standard land bonus remains
    st.session_state.infra_cost_reduction = 1.5     # Moderate infrastructure upkeep benefits
    st.session_state.soldier_efficiency = 1.0       # Standard military metric
    st.session_state.income_bonus = 1.5            # Standard income bonus
    st.session_state.happiness = 1.0               # Standard happiness bonus
    st.session_state.tech_cost_reduction = 3.0     # High priority on tech cost reduction, critical for sellers

def set_level_b():
    # For Level B (1000-2000 Days Old Tech Buyers)
    st.session_state.population_bonus = 2.5      # Increased citizen growth priority
    st.session_state.land_bonus = 2.0              # Standard land bonus
    st.session_state.infra_cost_reduction = 2.0     # Higher emphasis on cheaper infrastructure upkeep
    st.session_state.soldier_efficiency = 1.0       # Standard military metric
    st.session_state.income_bonus = 1.5            # Standard income bonus
    st.session_state.happiness = 1.0               # Standard happiness bonus
    st.session_state.tech_cost_reduction = 1.5     # Moderate tech benefit (buyers need less tech cost reduction)

def set_level_c():
    # For Level C (>2000 Days Old Tech Buyers)
    st.session_state.population_bonus = 3.0      # High priority on expanding the citizen base
    st.session_state.land_bonus = 2.0              # Standard land bonus
    st.session_state.infra_cost_reduction = 2.5     # Emphasis on cheaper infrastructure upkeep
    st.session_state.soldier_efficiency = 1.0       # Standard military metric
    st.session_state.income_bonus = 1.5            # Standard income bonus
    st.session_state.happiness = 1.0               # Standard happiness bonus
    st.session_state.tech_cost_reduction = 1.0     # Minimal emphasis on tech cost reduction, buyers benefit less here

# --- Streamlit UI ---
st.title("Cyber Nations | Optimal Resource Combination Finder")

# Create two tabs: one for computing resource combinations and one for optimizing weight selections
tabs = st.tabs(["Optimize Resource Combinations", "Optimize Weights"])

# --- Sidebar for Mode Presets and Custom Weighting Toggle ---
st.sidebar.markdown("### Mode Presets")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.button("Peace Mode", on_click=set_peace_mode)
with col2:
    st.button("War Mode", on_click=set_war_mode)

# Custom weighting toggle: if checked, nation level presets are disabled and manual weightings are used.
use_custom = st.sidebar.checkbox("Use Custom Weightings Instead of Nation Level Presets", value=False, key="use_custom")

# Show nation level selection only for Peace Mode if not using custom weightings
if st.session_state.mode == "Peace" and not use_custom:
    selected_level = st.sidebar.radio("Nation Level (Peace Mode)", ["Level A", "Level B", "Level C"], key="nation_level_option")
    if selected_level == "Level A":
        set_level_a()
    elif selected_level == "Level B":
        set_level_b()
    elif selected_level == "Level C":
        set_level_c()

# --- Tab 1: Resource Combinations ---
with tabs[0]:
    st.markdown("""
    Adjust the metric weights below and click **Calculate** to see optimal 12-resource combinations along with their triggered bonus resources.
    Bonus effects are integrated into the overall score.
    """)
    st.sidebar.markdown("### Adjust Weighting Metrics")
    # The number inputs now use the session state values as their defaults.
    st.sidebar.number_input("Population Bonus Weight", value=st.session_state.population_bonus, step=0.1, key="population_bonus")
    st.sidebar.number_input("Land Bonus Weight", value=st.session_state.land_bonus, step=0.1, key="land_bonus")
    st.sidebar.number_input("Infra Cost Reduction Weight", value=st.session_state.infra_cost_reduction, step=0.1, key="infra_cost_reduction")
    st.sidebar.number_input("Soldier Efficiency Weight", value=st.session_state.soldier_efficiency, step=0.1, key="soldier_efficiency")
    st.sidebar.number_input("Income Bonus Weight", value=st.session_state.income_bonus, step=0.1, key="income_bonus")
    st.sidebar.number_input("Happiness Weight", value=st.session_state.happiness, step=0.1, key="happiness")
    st.sidebar.number_input("Tech Cost Reduction Weight", value=st.session_state.tech_cost_reduction, step=0.1, key="tech_cost_reduction")
    
    # --- Add Uranium Toggle ---
    require_uranium = st.sidebar.checkbox("Require Uranium in combinations", value=True)
    
    # --- Build Weights Dictionary from Session State ---
    # If an optimized configuration is present, use it; otherwise, use the individual widget values.
    if "optimized_weights" in st.session_state:
        weights = st.session_state.optimized_weights
    else:
        weights = {
            "population_bonus": st.session_state.population_bonus,
            "land_bonus": st.session_state.land_bonus,
            "infra_cost_reduction": st.session_state.infra_cost_reduction,
            "soldier_efficiency": st.session_state.soldier_efficiency,
            "income_bonus": st.session_state.income_bonus,
            "happiness": st.session_state.happiness,
            "tech_cost_reduction": st.session_state.tech_cost_reduction
        }
    
    if st.sidebar.button("Calculate"):
        with st.spinner("Computing combinations..."):
            df_results = compute_combinations(weights, require_uranium)
        st.success("Calculation completed!")
        st.subheader("Top 10 Resource Combinations")
        st.dataframe(df_results.head(10))
        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name="Results")
            writer.close()
            return output.getvalue()
        st.download_button("Download Results", data=to_excel(df_results),
                           file_name="CyberNations_Optimal_Resource_Combinations.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Tab 2: Optimize Weights ---
with tabs[1]:
    st.header("Optimize Weight Selections Based on Desired Bonus Resources")
    st.markdown("Select the bonus resources you want to emphasize. Clicking **Optimize Weights** will suggest a weight configuration based on the bonus contributions defined in the bonus resource benefits.")
    desired_bonuses = st.multiselect("Select Desired Bonus Resources", list(bonus_values.keys()))
    if st.button("Optimize Weights", key="optimize_weights"):
        new_weights = optimize_weights(desired_bonuses)
        st.write("### Suggested Weight Configuration:")
        st.write(new_weights)
        # Instead of updating individual session state keys, store the optimized configuration separately.
        st.session_state.optimized_weights = new_weights
        st.success("Optimized weights have been saved!")
    
    # --- Generate Combinations with Optimized Weights ---
    if st.button("Generate Combinations", key="generate_combinations"):
        # Use the optimized weights if available; otherwise, use the widget values.
        if "optimized_weights" in st.session_state:
            weights = st.session_state.optimized_weights
        else:
            weights = {
                "population_bonus": st.session_state.population_bonus,
                "land_bonus": st.session_state.land_bonus,
                "infra_cost_reduction": st.session_state.infra_cost_reduction,
                "soldier_efficiency": st.session_state.soldier_efficiency,
                "income_bonus": st.session_state.income_bonus,
                "happiness": st.session_state.happiness,
                "tech_cost_reduction": st.session_state.tech_cost_reduction
            }
        require_uranium = st.checkbox("Require Uranium in combinations (for optimized calculation)", value=True, key="opt_generate_uranium")
        with st.spinner("Generating combinations with optimized weights..."):
            df_results = compute_combinations(weights, require_uranium, desired_bonus_filter=desired_bonuses)
        st.success("Optimized combinations generated!")
        st.subheader("Top 10 Optimized Resource Combinations")
        st.dataframe(df_results.head(10))
        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name="OptimizedResults")
            writer.close()
            return output.getvalue()
        st.download_button("Download Optimized Results", data=to_excel(df_results),
                           file_name="CyberNations_Optimized_Resource_Combinations.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
