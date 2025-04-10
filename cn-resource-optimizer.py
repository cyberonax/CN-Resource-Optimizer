import streamlit as st
import itertools
import pandas as pd
from io import BytesIO

# ---------------------------
# Resource Data Definition
# ---------------------------
resources = {
    "Aluminum": {"population_bonus": 0, "land_bonus": 0, "infra_cost_reduction": 7, "soldier_efficiency": 20},
    "Cattle": {"population_bonus": 5, "land_bonus": 0, "land_cost_reduction": 10},
    "Coal": {"population_bonus": 0, "land_bonus": 15, "infra_cost_reduction": 4, "soldier_efficiency": 8},
    "Fish": {"population_bonus": 8, "land_cost_reduction": 5},
    "Furs": {"population_bonus": 0, "income_bonus": 3.5},
    "Gems": {"population_bonus": 0, "income_bonus": 1.5, "happiness": 2.5},
    "Gold": {"population_bonus": 0, "income_bonus": 3.0},
    "Iron": {"population_bonus": 0, "infra_cost_reduction": 5},
    "Lead": {"population_bonus": 0},
    "Lumber": {"population_bonus": 0, "infra_cost_reduction": 6},
    "Marble": {"population_bonus": 0, "infra_cost_reduction": 10},
    "Oil": {"population_bonus": 0, "soldier_efficiency": 10},
    "Pigs": {"population_bonus": 3.5, "soldier_efficiency": 15},
    "Rubber": {"population_bonus": 0, "land_bonus": 20, "land_cost_reduction": 10, "infra_cost_reduction": 3},
    "Silver": {"population_bonus": 0, "income_bonus": 2.0, "happiness": 2},
    "Spices": {"population_bonus": 0, "land_bonus": 8, "happiness": 2},
    "Sugar": {"population_bonus": 3, "happiness": 1},
    "Uranium": {"population_bonus": 0},
    "Water": {"population_bonus": 0, "happiness": 2.5},
    "Wheat": {"population_bonus": 8}
}

# ---------------------------
# Helper Function to Evaluate a Combination
# ---------------------------
def evaluate_combination(combo, metric_weights):
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
    total_score = sum(scores[key] * metric_weights.get(key, 0) for key in scores)
    result = {"combo": combo}
    result.update(scores)
    result["score"] = total_score
    return result

# ---------------------------
# Caching the computation of combinations
# ---------------------------
@st.cache_data(show_spinner=True)
def compute_combinations(metric_weights):
    resource_names = list(resources.keys())
    # Generate all combinations of 12 resources out of the available ones.
    combinations = itertools.combinations(resource_names, 12)
    evaluated = [evaluate_combination(combo, metric_weights) for combo in combinations]
    df = pd.DataFrame(evaluated)
    # Convert the combo tuple to a human-readable string
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
Adjust the weights below and press **Calculate** to see the top combinations.
    """
)

# Sidebar for metric weights
st.sidebar.header("Metric Weights")
population_weight = st.sidebar.number_input("Population Bonus Weight", value=2.0, min_value=0.0, step=0.1)
land_weight = st.sidebar.number_input("Land Bonus Weight", value=1.0, min_value=0.0, step=0.1)
infra_weight = st.sidebar.number_input("Infrastructure Cost Reduction Weight", value=1.0, min_value=0.0, step=0.1)
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
    
    # Provide an option to download the full results as an Excel file
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name="Results")
        writer.close()  # Use writer.close() for newer versions of Pandas
        processed_data = output.getvalue()
        return processed_data
    
    excel_data = to_excel(df_results)
    st.download_button(
        label="Download Results",
        data=excel_data,
        file_name="CyberNations_Optimal_Resource_Combinations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
