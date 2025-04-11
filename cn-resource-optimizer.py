import streamlit as st
import itertools
import pandas as pd
from io import BytesIO

# ---------------------------
# Updated Resource Data Definition
# ---------------------------
resources = {
    "Aluminum": {
        "population_bonus": 0,
        "land_bonus": 0,
        "infra_cost_reduction": 7,  # -7% infra purchase cost (aircraft cost reduction of -8% omitted)
        "soldier_efficiency": 20    # +20% soldier efficiency
    },
    "Cattle": {
        "population_bonus": 5,      # +5% citizens
        "land_bonus": 0,
        "land_cost_reduction": 10   # -10% land purchase cost
    },
    "Coal": {
        "population_bonus": 0,
        "land_bonus": 15,           # +15% purchased land area
        "infra_cost_reduction": 4,  # -4% infra purchase cost
        "soldier_efficiency": 8     # +8% soldier efficiency
    },
    "Fish": {
        "population_bonus": 8,      # +8% citizens
        "land_cost_reduction": 5    # -5% land purchase cost
    },
    "Furs": {
        "population_bonus": 0,
        "income_bonus": 3.5         # +$3.50 daily income (natural growth multiplier omitted)
    },
    "Gems": {
        "population_bonus": 0,
        "income_bonus": 1.5,        # +$1.50 daily income
        "happiness": 2.5            # +2.5 happiness
    },
    "Gold": {
        "population_bonus": 0,
        "income_bonus": 3.0         # +$3.00 daily income (tech cost reduction of 5% omitted)
    },
    "Iron": {
        "population_bonus": 0,
        "infra_cost_reduction": 5   # -5% infra purchase cost (other soldier/tank/upkeep effects omitted)
    },
    "Lead": {
        "population_bonus": 0      # Effects on missiles, aircraft, tanks, soldier upkeep, etc. omitted
    },
    "Lumber": {
        "population_bonus": 0,
        "infra_cost_reduction": 6   # -6% infra purchase cost (infra upkeep -8% omitted)
    },
    "Marble": {
        "population_bonus": 0,
        "infra_cost_reduction": 10  # -10% infra purchase cost
    },
    "Oil": {
        "population_bonus": 0,
        "soldier_efficiency": 10    # +10% soldier efficiency (other cost reductions, +1.5 happiness omitted)
    },
    "Pigs": {
        "population_bonus": 3.5,    # +3.5% citizens
        "soldier_efficiency": 15    # +15% soldier efficiency (soldier upkeep reduction omitted)
    },
    "Rubber": {
        "population_bonus": 0,
        "land_bonus": 20,           # +20% purchased land area
        "land_cost_reduction": 10,   # -10% land purchase cost
        "infra_cost_reduction": 3    # -3% infra purchase cost (triple sale value and aircraft cost omitted)
    },
    "Silver": {
        "population_bonus": 0,
        "income_bonus": 2.0,        # +$2.00 daily income
        "happiness": 2              # +2 happiness
    },
    "Spices": {
        "population_bonus": 0,
        "land_bonus": 8,            # +8% purchased land area
        "happiness": 2              # +2 happiness
    },
    "Sugar": {
        "population_bonus": 3,      # +3% citizens
        "happiness": 1              # +1 happiness
    },
    "Uranium": {
        "population_bonus": 0       # -3% infra upkeep (conditional nuclear effects omitted)
    },
    "Water": {
        "population_bonus": 0,
        "happiness": 2.5            # +2.5 happiness (other effects omitted)
    },
    "Wheat": {
        "population_bonus": 8       # +8% citizens
    },
    "Wine": {
        "population_bonus": 0,
        "happiness": 3              # +3 happiness
    }
}

# ---------------------------
# Bonus Resource Definitions and Benefits
# ---------------------------
def get_bonus_resources(combo):
    bonus = []
    combo_set = set(combo)
    
    # Beer: Requires Water, Wheat, Lumber, and Aluminum.
    if {"Water", "Wheat", "Lumber", "Aluminum"}.issubset(combo_set):
        bonus.append("Beer")
    
    # Construction: Requires Lumber, Iron, Marble, and Aluminum.
    if {"Lumber", "Iron", "Marble", "Aluminum"}.issubset(combo_set):
        bonus.append("Construction")
    
    # Fast Food: Requires Cattle, Sugar, Spices, and Pigs.
    if {"Cattle", "Sugar", "Spices", "Pigs"}.issubset(combo_set):
        bonus.append("Fast Food")
    
    # Fine Jewelry: Requires Gold, Silver, Gems, and Coal.
    if {"Gold", "Silver", "Gems", "Coal"}.issubset(combo_set):
        bonus.append("Fine Jewelry")
    
    # Microchips: Requires Gold, Lead, and Oil.
    if {"Gold", "Lead", "Oil"}.issubset(combo_set):
        bonus.append("Microchips")
    
    # Scholars: Requires Lumber and Lead.
    if {"Lumber", "Lead"}.issubset(combo_set):
        bonus.append("Scholars")
    
    # Steel: Requires Coal and Iron.
    if {"Coal", "Iron"}.issubset(combo_set):
        bonus.append("Steel")
    
    # Additional bonus resource from the full spec which uses Wine:
    # Affluent Population: Requires Fine Jewelry, Fish, Furs, and Wine.
    if {"Fine Jewelry", "Fish", "Furs", "Wine"}.issubset(combo_set.union(get_bonus_resources(combo))):
        # Note: This check is a bit circular because "Fine Jewelry" is a bonus itself.
        # In a complete model, you would check if the combo triggers Fine Jewelry, then include Wine etc.
        # Here, we simplify by checking that the main resources for Fine Jewelry are present along with Fish, Furs, and Wine.
        if {"Gold", "Silver", "Gems", "Coal"}.issubset(combo_set) and {"Fish", "Furs", "Wine"}.issubset(combo_set):
            bonus.append("Affluent Population")
    
    return bonus

# Define bonus effects to add to the overall score.
bonus_values = {
    "Beer": {"happiness": 2},           # +2 happiness
    "Construction": {"infra_cost_reduction": 5},  # +5 infra reduction
    "Fast Food": {"happiness": 2},        # +2 happiness
    "Fine Jewelry": {"happiness": 3},     # +3 happiness
    "Microchips": {"happiness": 2},       # +2 happiness
    "Scholars": {"income_bonus": 3.0},    # +$3.00 income bonus
    "Steel": {"infra_cost_reduction": 2}, # +2 infra reduction
    "Affluent Population": {"population_bonus": 5}  # +5% citizens
}

# ---------------------------
# Helper Function to Evaluate a Combination
# ---------------------------
def evaluate_combination(combo, metric_weights):
    # Calculate base resource contributions
    scores = {
        "population_bonus": 0,
        "land_bonus": 0,
        "infra_cost_reduction": 0,
        "soldier_efficiency": 0,
        "income_bonus": 0,
        "happiness": 0
    }
    for r in combo:
        for key in scores:
            scores[key] += resources[r].get(key, 0)
    
    # Compute primary score using user-defined weights.
    total_score = sum(scores[key] * metric_weights.get(key, 0) for key in scores)
    
    # Get triggered bonus resources.
    bonus_list = get_bonus_resources(combo)
    
    # Sum bonus contributions (if any)
    bonus_score = 0
    for bonus in bonus_list:
        for attr, bonus_val in bonus_values.get(bonus, {}).items():
            bonus_score += bonus_val * metric_weights.get(attr, 0)
    
    total_score += bonus_score

    result = {"combo": combo}
    result.update(scores)
    result["score"] = total_score
    result["bonus_resources"] = ", ".join(bonus_list) if bonus_list else ""
    return result

# ---------------------------
# Caching the Computation of Combinations
# ---------------------------
@st.cache_data(show_spinner=True)
def compute_combinations(metric_weights):
    resource_names = list(resources.keys())
    # Generate all combinations of 12 resources.
    combinations = itertools.combinations(resource_names, 12)
    evaluated = [evaluate_combination(combo, metric_weights) for combo in combinations]
    df = pd.DataFrame(evaluated)
    # Convert the combo tuple to a human-readable string.
    df["combo"] = df["combo"].apply(lambda x: ", ".join(x))
    df = df.sort_values(by="score", ascending=False)
    return df

# ---------------------------
# Streamlit UI Layout
# ---------------------------
st.title("CyberNations Optimal Resource Combination Finder")
st.markdown(
    """
This app computes optimal 12-resource combinations for CyberNations based on the metric weights you choose.
Adjust the weights below and click **Calculate** to see the top combinations along with any triggered bonus resources.
Bonus resources now add extra points to the overall score.
    """
)

# Sidebar for metric weights
st.sidebar.header("Metric Weights")
population_weight = st.sidebar.number_input("Population Bonus Weight", value=2.0, min_value=0.0, step=0.1)
land_weight = st.sidebar.number_input("Land Bonus Weight", value=1.0, min_value=0.0, step=0.1)
infra_weight = st.sidebar.number_input("Infra Cost Reduction Weight", value=1.0, min_value=0.0, step=0.1)
soldier_eff_weight = st.sidebar.number_input("Soldier Efficiency Weight", value=2.0, min_value=0.0, step=0.1)
income_weight = st.sidebar.number_input("Income Bonus Weight", value=1.5, min_value=0.0, step=0.1)
happiness_weight = st.sidebar.number_input("Happiness Weight", value=1.0, min_value=0.0, step=0.1)

metric_weights = {
    "population_bonus": population_weight,
    "land_bonus": land_weight,
    "infra_cost_reduction": infra_weight,
    "soldier_efficiency": soldier_eff_weight,
    "income_bonus": income_weight,
    "happiness": happiness_weight
}

if st.sidebar.button("Calculate"):
    with st.spinner("Computing combinations. This might take a few moments..."):
        df_results = compute_combinations(metric_weights)
    
    st.success("Calculation completed!")
    
    # Display the top 10 combinations
    st.subheader("Top 10 Resource Combinations")
    st.dataframe(df_results.head(10))
    
    # Function to convert DataFrame to Excel file in memory.
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name="Results")
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    
    excel_data = to_excel(df_results)
    st.download_button(
        label="Download Results",
        data=excel_data,
        file_name="CyberNations_Optimal_Resource_Combinations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
