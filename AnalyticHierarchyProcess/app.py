"""
AHP Streamlit App
Parses gluc/ahp YAML format and computes weights + consistency ratios using ahpy.
"""

import streamlit as st
import yaml
import ahpy
import pandas as pd
from fractions import Fraction

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AHP Calculator", page_icon="⚖️", layout="wide")
st.title("⚖️ Analytic Hierarchy Process (AHP) Calculator")
st.caption("Accepts the [gluc/ahp](https://github.com/gluc/ahp) YAML file format.")

# ── Helper: parse pairwise list from gluc/ahp YAML ───────────────────────────
def parse_fraction(value):
    """Convert '1/3' strings or numeric values to float."""
    if isinstance(value, str) and '/' in value:
        return float(Fraction(value))
    return float(value)

def extract_comparisons(pairwise_list):
    """
    Convert gluc/ahp pairwise list:
      - [A, B, 3]   →  {('A','B'): 3.0}
      - [A, B, 1/3] →  {('A','B'): 0.333}
    ahpy convention: if A preferred over B by 3, value > 1.
    If B preferred over A, gluc uses 1/3 for [A,B,1/3], which ahpy also expects < 1.
    """
    comparisons = {}
    for row in pairwise_list:
        a, b, val = row[0], row[1], row[2]
        comparisons[(str(a), str(b))] = parse_fraction(val)
    return comparisons

def build_ahpy_model(goal_node, parent_name=None):
    """
    Recursively walk the gluc/ahp goal tree and build ahpy Compare objects.
    Returns a list of (Compare object, parent_name) tuples.
    """
    results = []
    name = goal_node.get("name", parent_name or "Goal")

    # Criteria-level pairwise (children comparisons)
    children = goal_node.get("children", {})
    prefs = goal_node.get("preferences", {})
    pairwise = prefs.get("pairwise", []) if prefs else []

    if pairwise and children:
        comparisons = extract_comparisons(pairwise)
        compare = ahpy.Compare(name=name, comparisons=comparisons)
        results.append(compare)

        # Recurse into children
        for child_name, child_node in children.items():
            if isinstance(child_node, dict) and "preferences" in child_node:
                child_node["name"] = child_name
                results.extend(build_ahpy_model(child_node, child_name))

    return results

# ── Sidebar: input ────────────────────────────────────────────────────────────
st.sidebar.header("📂 Input")
input_mode = st.sidebar.radio("Input method", ["Upload .ahp file", "Paste YAML", "Load example"])

yaml_text = ""

if input_mode == "Upload .ahp file":
    uploaded = st.sidebar.file_uploader("Upload your .ahp file", type=["ahp", "yaml", "yml"])
    if uploaded:
        yaml_text = uploaded.read().decode("utf-8")

elif input_mode == "Paste YAML":
    yaml_text = st.sidebar.text_area("Paste YAML here", height=300)

elif input_mode == "Load example":
    yaml_text = """
Version: 2.0

Alternatives: &alternatives
  Accord Sedan:
  Accord Hybrid:
  Pilot:
  CR-V:
  Element:
  Odyssey:

Goal:
  name: Buy a Car
  preferences:
    pairwise:
      - [Cost, Safety, 3]
      - [Cost, Style, 7]
      - [Safety, Style, 5]
  children:
    Cost:
      preferences:
        pairwise:
          - [Accord Sedan, Accord Hybrid, 1/2]
          - [Accord Sedan, Pilot, 3]
          - [Accord Sedan, CR-V, 2]
          - [Accord Sedan, Element, 4]
          - [Accord Sedan, Odyssey, 3]
          - [Accord Hybrid, Pilot, 5]
          - [Accord Hybrid, CR-V, 4]
          - [Accord Hybrid, Element, 7]
          - [Accord Hybrid, Odyssey, 5]
          - [Pilot, CR-V, 1/3]
          - [Pilot, Element, 1/2]
          - [Pilot, Odyssey, 1/3]
          - [CR-V, Element, 2]
          - [CR-V, Odyssey, 1]
          - [Element, Odyssey, 1/2]
      children: *alternatives
    Safety:
      preferences:
        pairwise:
          - [Accord Sedan, Accord Hybrid, 1]
          - [Accord Sedan, Pilot, 5]
          - [Accord Sedan, CR-V, 7]
          - [Accord Sedan, Element, 9]
          - [Accord Sedan, Odyssey, 1/3]
          - [Accord Hybrid, Pilot, 5]
          - [Accord Hybrid, CR-V, 7]
          - [Accord Hybrid, Element, 9]
          - [Accord Hybrid, Odyssey, 1/3]
          - [Pilot, CR-V, 2]
          - [Pilot, Element, 9]
          - [Pilot, Odyssey, 1/7]
          - [CR-V, Element, 9]
          - [CR-V, Odyssey, 1/8]
          - [Element, Odyssey, 1/9]
      children: *alternatives
    Style:
      preferences:
        pairwise:
          - [Accord Sedan, Accord Hybrid, 1]
          - [Accord Sedan, Pilot, 7]
          - [Accord Sedan, CR-V, 5]
          - [Accord Sedan, Element, 9]
          - [Accord Sedan, Odyssey, 6]
          - [Accord Hybrid, Pilot, 7]
          - [Accord Hybrid, CR-V, 5]
          - [Accord Hybrid, Element, 9]
          - [Accord Hybrid, Odyssey, 6]
          - [Pilot, CR-V, 1/6]
          - [Pilot, Element, 3]
          - [Pilot, Odyssey, 1/3]
          - [CR-V, Element, 7]
          - [CR-V, Odyssey, 5]
          - [Element, Odyssey, 1/5]
      children: *alternatives
"""

# ── Main: run analysis ────────────────────────────────────────────────────────
if yaml_text.strip():
    try:
        # Parse YAML — resolve anchors automatically
        data = yaml.safe_load(yaml_text)

        goal = data.get("Goal", data.get("goal"))
        if not goal:
            st.error("Could not find a 'Goal' key in the YAML. Please check your file.")
            st.stop()

        # Read alternative names directly from the top-level Alternatives key
        alternatives_data = data.get("Alternatives", data.get("alternatives", {})) or {}
        alternative_names = set(str(k) for k in alternatives_data.keys())

        if not alternative_names:
            st.error("Could not find an 'Alternatives' key in the YAML, or it was empty.")
            st.info(f"Top-level keys found in your YAML: {list(data.keys())}")
            st.stop()

        # Build ahpy Compare objects
        compares = build_ahpy_model(goal)

        if not compares:
            st.error("No pairwise comparisons found. Check that your YAML has 'preferences: pairwise:' sections.")
            st.stop()

        # Link children to parent
        # The first compare is the top-level goal; subsequent ones are criteria
        target = compares[0]
        children_compares = compares[1:]
        if children_compares:
            target.add_children(children_compares)

        # ── Results ──────────────────────────────────────────────────────────
        goal_name = goal.get("name", "Goal")
        st.subheader(f"Results: {goal_name}")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Criteria Weights")
            crit_weights = compares[0].local_weights
            crit_df = pd.DataFrame(
                {"Criterion": list(crit_weights.keys()),
                 "Weight": [f"{v:.4f}" for v in crit_weights.values()],
                 "Weight %": [f"{v*100:.1f}%" for v in crit_weights.values()]}
            ).sort_values("Weight %", ascending=False).reset_index(drop=True)
            st.dataframe(crit_df, use_container_width=True, hide_index=True)

            cr = compares[0].consistency_ratio
            if cr is not None:
                color = "🟢" if cr <= 0.1 else "🔴"
                st.metric(f"{color} Consistency Ratio (Goal)", f"{cr:.4f}",
                          help="CR ≤ 0.10 is generally considered acceptable.")
            else:
                st.info("Only 2 criteria — consistency ratio not applicable.")

        with col2:
            st.markdown("### Global Alternative Rankings")
            global_weights = target.global_weights
            # Filter to only the declared alternatives
            if alternative_names:
                alt_weights = {k: v for k, v in global_weights.items() if k in alternative_names}
            else:
                # Fallback: exclude criteria names if no Alternatives key found
                criteria_names = set(crit_weights.keys())
                alt_weights = {k: v for k, v in global_weights.items() if k not in criteria_names}

            if alt_weights:
                alt_df = pd.DataFrame(
                    {"Alternative": list(alt_weights.keys()),
                     "Global Weight": [f"{v:.4f}" for v in alt_weights.values()],
                     "Score %": [f"{v*100:.1f}%" for v in alt_weights.values()]}
                ).sort_values("Score %", ascending=False).reset_index(drop=True)
                alt_df.index = alt_df.index + 1  # rank from 1
                st.dataframe(alt_df, use_container_width=True)

                winner = alt_df.iloc[0]["Alternative"]
                st.success(f"🏆 Recommended choice: **{winner}**")
            else:
                st.info("No separate alternatives detected — showing criteria weights only.")

        # Per-criterion consistency ratios
        if children_compares:
            st.markdown("### Per-Criterion Consistency Ratios")
            cr_rows = []
            for c in children_compares:
                cr_val = c.consistency_ratio
                cr_rows.append({
                    "Criterion": c.name,
                    "Consistency Ratio": f"{cr_val:.4f}" if cr_val is not None else "N/A",
                    "Status": "✅ OK" if (cr_val is not None and cr_val <= 0.1) else ("⚠️ High" if cr_val is not None else "—")
                })
            st.dataframe(pd.DataFrame(cr_rows), use_container_width=True, hide_index=True)

        # Raw YAML preview
        with st.expander("View parsed YAML"):
            st.code(yaml_text, language="yaml")

    except Exception as e:
        st.error(f"Error processing AHP model: {e}")
        st.exception(e)

else:
    st.info("👈 Choose an input method in the sidebar to get started.")
    st.markdown("""
    **Supported format:** the `gluc/ahp` YAML format (`.ahp` files).
    
    The file should have:
    - An `Alternatives` section listing your options
    - A `Goal` section with a hierarchy of criteria and `pairwise:` comparison lists
    
    Each pairwise entry is `[ItemA, ItemB, ratio]` where ratio > 1 means A is preferred over B.
    """)
