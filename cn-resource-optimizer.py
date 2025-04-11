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
def compute_combinations(weights):
    evaluated = [evaluate_combination(c, weights) for c in itertools.combinations(list(resources.keys()), 12)]
    df = pd.DataFrame(evaluated)
    df["combo"] = df["combo"].apply(lambda x: ", ".join(x))
    return df.sort_values(by="score", ascending=False)

# --- Streamlit UI ---
st.title("CyberNations Optimal Resource Combination Finder")
st.markdown("""
Adjust the metric weights below and click **Calculate** to see optimal 12-resource combinations along with their triggered bonus resources.
Bonus effects—including technology cost reduction—are integrated into the overall score.
""")

# Sidebar input, including tech cost reduction slider
weights = {
    "population_bonus": st.sidebar.number_input("Population Bonus Weight", value=2.0, step=0.1),
    "land_bonus": st.sidebar.number_input("Land Bonus Weight", value=2.0, step=0.1),
    "infra_cost_reduction": st.sidebar.number_input("Infra Cost Reduction Weight", value=1.0, step=0.1),
    "soldier_efficiency": st.sidebar.number_input("Soldier Efficiency Weight", value=1.0, step=0.1),
    "income_bonus": st.sidebar.number_input("Income Bonus Weight", value=1.5, step=0.1),
    "happiness": st.sidebar.number_input("Happiness Weight", value=1.0, step=0.1),
    "tech_cost_reduction": st.sidebar.number_input("Tech Cost Reduction Weight", value=1, step=0.1)
}

if st.sidebar.button("Calculate"):
    with st.spinner("Computing combinations..."):
        df_results = compute_combinations(weights)
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
