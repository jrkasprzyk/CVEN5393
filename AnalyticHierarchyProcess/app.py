"""
AHP Streamlit App
Parses gluc/ahp YAML format and computes weights + consistency ratios using ahpy.
"""

import streamlit as st
import yaml
import ahpy
import pandas as pd
from fractions import Fraction
from numpy import isnan, isinf
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AHP Calculator", page_icon="⚖️", layout="wide")
st.title("Analytic Hierarchy Process (AHP) Calculator")
st.caption(
    "This is a [streamlit](https://streamlit.io/) implementation of the "
    "[ipub](https://ipub.com/dev-corner/apps/ahp/) AHP calculator. "
    "The tool accepts the [gluc/ahp](https://github.com/gluc/ahp) YAML file format, "
    "then uses [ahpy](https://github.com/ahpy/ahpy) to compute weights and consistency ratios. "
    "Developed for [CVEN 5393, Water Resources Systems and Management](https://www.colorado.edu/lab/krg/teaching/cven-5393-water-resource-systems-and-management) at CU Boulder; "
    "for educational purposes only."
)

# ── Helper: parse pairwise list from gluc/ahp YAML ───────────────────────────


def parse_fraction(value):
    """Convert '1/3' strings or numeric values to float."""
    try:
        if isinstance(value, str):
            if '/' in value:
                # Handle fractions like "1/3"
                frac = Fraction(value)
                result = float(frac)
            else:
                # Handle regular numeric strings
                result = float(value)
        else:
            # Handle numeric types directly
            result = float(value)
        
        # Validate result is reasonable for AHP (typically 1/9 to 9)
        if not (1e-6 <= abs(result) <= 1e6):
            raise ValueError(f"Comparison value {result} is outside reasonable AHP range (1/9 to 9)")
        
        return result
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        raise ValueError(f"Invalid comparison value '{value}': {e}")


def extract_comparisons(pairwise_list):
    """
    Convert gluc/ahp pairwise list:
      - [A, B, 3]   →  {('A','B'): 3.0}
      - [A, B, 1/3] →  {('A','B'): 0.333}
    ahpy convention: if A preferred over B by 3, value > 1.
    If B preferred over A, gluc uses 1/3 for [A,B,1/3], which ahpy also expects < 1.
    """
    comparisons = {}
    for i, row in enumerate(pairwise_list):
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ValueError(
                f"Invalid pairwise entry at index {i}: '{row}'. Expected [ItemA, ItemB, value].")
        a, b, val = row[0], row[1], row[2]
        parsed_val = parse_fraction(val)
        # Validate AHP scale (typically 1-9 or reciprocals)
        if parsed_val <= 0 or parsed_val > 9:
            st.warning(
                f"⚠️ Pairwise value {parsed_val} is outside typical AHP scale (1-9)." 
                f"Results may be unreliable.")
        comparisons[(str(a), str(b))] = parsed_val
    return comparisons


def parse_pairwise_function(func_code, alternatives_data, criterion_name):
    """
    Parse and evaluate R pairwiseFunction to generate comparisons.
    Example: function(a1, a2) min(9, max(1/9, a1$`Taste`/a2$`Taste`))
    
    Converts R syntax to Python and evaluates for all alternative pairs.
    Returns dict of comparisons {(alt1, alt2): value}.
    """
    if not alternatives_data:
        raise ValueError(f"pairwiseFunction requires alternatives data")
    
    # Validate that alternatives have the required attributes
    sample_alt = next(iter(alternatives_data.values()))
    if not isinstance(sample_alt, dict):
        raise ValueError(f"Alternatives must be objects with attributes, not just names")
    
    # Extract function body (everything after "function(a1, a2)")
    body_match = re.search(r'function\s*\(\s*a1\s*,\s*a2\s*\)\s*(.*)', func_code.strip())
    if not body_match:
        raise ValueError(f"Could not parse pairwiseFunction: {func_code}")
    
    body = body_match.group(1).strip()
    
    # Convert R syntax to Python:
    # a1$`ColumnName` or a1$ColumnName → alternatives_data[a1]['ColumnName']
    body = re.sub(r'a([12])\$`([^`]+)`', r"alternatives_data[a\1]['\2']", body)
    body = re.sub(r'a([12])\$([a-zA-Z_][a-zA-Z0-9_]*)', r"alternatives_data[a\1]['\2']", body)
    
    # Get list of alternatives
    alt_names = list(alternatives_data.keys())
    comparisons = {}
    
    try:
        for i, alt1 in enumerate(alt_names):
            for alt2 in alt_names[i+1:]:  # Only compare each pair once
                # Safe evaluation context
                local_scope = {
                    'a1': alt1,
                    'a2': alt2,
                    'alternatives_data': alternatives_data,
                    'min': min,
                    'max': max,
                }
                
                try:
                    value = eval(body, {"__builtins__": {}}, local_scope)
                    
                    # Handle potential numerical issues
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"Function must return a number, got {type(value)}")
                    
                    # Check for NaN, infinity
                    if not (0 < value < float('inf')):
                        raise ValueError(f"Invalid comparison value: {value}")
                    
                    value = parse_fraction(value)
                    
                    if value <= 0 or value > 9:
                        st.warning(
                            f"⚠️ Pairwise value {value} (from {alt1} vs {alt2}) is outside AHP scale.")
                    
                    comparisons[(str(alt1), str(alt2))] = value
                except Exception as e:
                    raise ValueError(f"Error computing {alt1} vs {alt2}: {e}")
    except Exception as e:
        raise ValueError(f"Error evaluating pairwiseFunction: {e}")
    
    return comparisons


def extract_comparisons(pairwise_list):
    """
    Convert gluc/ahp pairwise list:
      - [A, B, 3]   →  {('A','B'): 3.0}
      - [A, B, 1/3] →  {('A','B'): 0.333}
    ahpy convention: if A preferred over B by 3, value > 1.
    If B preferred over A, gluc uses 1/3 for [A,B,1/3], which ahpy also expects < 1.
    """
    comparisons = {}
    for i, row in enumerate(pairwise_list):
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ValueError(
                f"Invalid pairwise entry at index {i}: '{row}'. Expected [ItemA, ItemB, value].")
        a, b, val = row[0], row[1], row[2]
        parsed_val = parse_fraction(val)
        # Validate AHP scale (typically 1-9 or reciprocals)
        if parsed_val <= 0 or parsed_val > 9:
            st.warning(
                f"⚠️ Pairwise value {parsed_val} is outside typical AHP scale (1-9)." 
                f"Results may be unreliable.")
        comparisons[(str(a), str(b))] = parsed_val
    return comparisons


def build_ahpy_model(goal_node, alternatives_data=None, parent_name=None):
    """
    Recursively walk the gluc/ahp goal tree and build ahpy Compare objects.
    Supports both 'pairwise' (list) and 'pairwiseFunction' (R code) formats.
    Returns a list of Compare objects.
    """
    results = []
    name = goal_node.get("name", parent_name or "Goal")

    # Criteria-level pairwise (children comparisons)
    children = goal_node.get("children", {})
    prefs = goal_node.get("preferences", {})
    
    pairwise = prefs.get("pairwise", []) if prefs else []
    pairwise_func = prefs.get("pairwiseFunction") if prefs else None

    if children:
        comparisons = None
        
        # Validate that we have children to compare
        if len(children) < 2:
            st.warning(f"⚠️ Node '{name}' has {len(children)} children, but AHP requires at least 2 for meaningful comparisons.")
        
        # Try pairwiseFunction first, then pairwise
        if pairwise_func:
            if not alternatives_data:
                raise ValueError(f"pairwiseFunction in '{name}' requires alternatives data")
            try:
                comparisons = parse_pairwise_function(pairwise_func, alternatives_data, name)
            except Exception as e:
                st.error(f"Error parsing pairwiseFunction for '{name}': {e}")
                return results
        elif pairwise:
            try:
                comparisons = extract_comparisons(pairwise)
            except Exception as e:
                st.error(f"Error parsing pairwise comparisons for '{name}': {e}")
                return results
        else:
            st.warning(
                f"⚠️ Node '{name}' has children but no comparison method specified. "
                f"Please provide either a 'pairwise' list or a 'pairwiseFunction'. Skipping.")
        
        if comparisons:
            # Validate that comparisons cover all children
            compared_items = set()
            for (a, b) in comparisons.keys():
                compared_items.add(a)
                compared_items.add(b)
            
            missing_items = set(children.keys()) - compared_items
            if missing_items:
                st.warning(f"⚠️ Some children of '{name}' are not compared: {missing_items}")
            
            try:
                compare = ahpy.Compare(name=name, comparisons=comparisons)
                results.append(compare)
            except Exception as e:
                st.error(f"Error creating AHP comparison for '{name}': {e}")
                return results

        # Recurse into children
        for child_name, child_node in children.items():
            if isinstance(child_node, dict) and "preferences" in child_node:
                child_node["name"] = child_name
                results.extend(build_ahpy_model(child_node, alternatives_data, child_name))

    return results


def get_yaml_input():
    """
    Handle user input from sidebar (predefined example, file upload, or pasted content).
    Returns YAML as a string.
    """
    st.sidebar.header("📂 Input")
    input_mode = st.sidebar.radio(
        "Input method",
        [
            "Load predefined example",
            "Upload .yaml file",
            "Paste .yaml content"
        ]
    )

    if input_mode == "Upload .yaml file":
        uploaded = st.sidebar.file_uploader(
            "Upload your .yaml file", type=["yaml"])
        if uploaded:
            return uploaded.read().decode("utf-8")
        return ""

    elif input_mode == "Paste .yaml content":
        return st.sidebar.text_area("Paste YAML here", height=300)

    else:  # Load predefined example
        return """
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
yaml_text = get_yaml_input()

if yaml_text.strip():
    try:
        # Parse YAML — resolve anchors automatically
        data = yaml.safe_load(yaml_text)
        
        # Validate that we got a dictionary
        if not isinstance(data, dict):
            st.error("YAML must contain a dictionary/object at the top level.")
            st.stop()
        
        # Validate required top-level structure
        if not any(key.lower() in ['goal', 'alternatives'] for key in data.keys()):
            st.error("YAML must contain at least a 'Goal' or 'goal' key, and optionally 'Alternatives' or 'alternatives'.")
            st.stop()

        goal = data.get("Goal", data.get("goal"))
        if not goal:
            st.error(
                "Could not find a 'Goal' key in the YAML. Please check your file.")
            st.stop()

        # Read alternative names directly from the top-level Alternatives key
        alternatives_data = data.get(
            "Alternatives", data.get("alternatives", {})) or {}
        alternative_names = set(str(k) for k in alternatives_data.keys())

        if not alternative_names:
            st.error(
                "Could not find an 'Alternatives' key in the YAML, or it was empty.")
            st.info(f"Top-level keys found in your YAML: {list(data.keys())}")
            st.stop()

        # Build ahpy Compare objects
        compares = build_ahpy_model(goal, alternatives_data)

        if not compares:
            st.error(
                "No pairwise comparisons found. "
                "Check that your YAML has 'preferences:' sections with either "
                " 'pairwise:' or 'pairwiseFunction:'.")
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

        # Create a two-column layout for displaying results side-by-side
        # st.columns([1, 1]) divides the screen into two equal-width columns
        # The 'with' statement is a context manager that places all content inside it
        # into the specified column. This creates a clean side-by-side layout:
        # left column shows criteria weights and consistency, right shows alternative rankings
        col1, col2 = st.columns([1, 1])

        # Left column: displays the weights of each criterion and its consistency ratio
        with col1:
            st.markdown("### Criteria Weights")
            crit_weights = compares[0].local_weights
            # Sort criteria by weight (highest first) BEFORE formatting
            sorted_crit = sorted(crit_weights.items(), key=lambda x: x[1], reverse=True)
            crit_df = pd.DataFrame(
                {"Criterion": [c[0] for c in sorted_crit],
                 "Weight": [f"{c[1]:.4f}" for c in sorted_crit],
                 "Weight %": [f"{c[1]*100:.1f}%" for c in sorted_crit]}
            ).reset_index(drop=True)
            st.dataframe(crit_df, width='stretch', hide_index=True)
            # Store sorted criteria order for consistency ratios table later
            sorted_criteria_order = [c[0] for c in sorted_crit]

            # Calculate and display the consistency ratio (measures how consistent
            # the pairwise comparisons are)
            cr = compares[0].consistency_ratio
            if cr is not None:
                color = "🟢" if cr <= 0.1 else "🔴"
                st.metric(f"{color} Consistency Ratio (Goal)", f"{cr:.4f}",
                          help="CR ≤ 0.10 is generally considered acceptable.")
            else:
                st.info("Only 2 criteria — consistency ratio not applicable.")

        # Right column: displays the overall rankings of alternatives based on their global weights
        with col2:
            st.markdown("### Global Alternative Rankings")
            # Compute global weights for alternatives by aggregating across criteria
            alt_weights = {}
            total_criteria_weight = 0
            
            if children_compares:
                for criterion in children_compares:
                    crit_weight = crit_weights.get(criterion.name, 0)
                    total_criteria_weight += crit_weight
                    
                    # Get local weights of alternatives within this criterion
                    alt_local_weights = criterion.local_weights
                    for alt_name, alt_local_weight in alt_local_weights.items():
                        if alt_name not in alt_weights:
                            alt_weights[alt_name] = 0
                        alt_weights[alt_name] += crit_weight * alt_local_weight

            # Validate that weights sum to approximately 1 (within numerical precision)
            if abs(total_criteria_weight - 1.0) > 1e-6:
                st.warning(f"⚠️ Criteria weights sum to {total_criteria_weight:.6f}, not 1.0. Results may be unreliable.")

            # Filter to only the declared alternatives
            if alternative_names:
                alt_weights = {
                    k: v for k, v in alt_weights.items() if k in alternative_names}
                
                # Check for alternatives that weren't evaluated in any criteria
                missing_alts = alternative_names - set(alt_weights.keys())
                if missing_alts:
                    st.warning(f"⚠️ Alternatives {missing_alts} were not found in any criteria comparisons.")
                
                # Sort alternatives by weight (highest first) BEFORE formatting
                sorted_alts = sorted(alt_weights.items(), key=lambda x: x[1], reverse=True)
                alt_df = pd.DataFrame(
                    {"Alternative": [a[0] for a in sorted_alts],
                     "Global Weight": [f"{a[1]:.4f}" for a in sorted_alts],
                     "Score %": [f"{a[1]*100:.1f}%" for a in sorted_alts]}
                ).reset_index(drop=True)
                alt_df.index = alt_df.index + 1  # rank from 1
                st.dataframe(alt_df, width='stretch')

                winner = alt_df.iloc[0]["Alternative"]
                st.success(f"🏆 Recommended choice: **{winner}**")
            else:
                st.info(
                    "No separate alternatives detected — showing criteria weights only.")

        # Per-criterion consistency ratios (ordered same as Criteria Weights table)
        if children_compares:
            st.markdown("### Per-Criterion Consistency Ratios")
            cr_rows = []
            # Build a dict of consistency ratios keyed by criterion name
            cr_dict = {c.name: c.consistency_ratio for c in children_compares}
            # Iterate in same order as Criteria Weights table
            for crit_name in sorted_criteria_order:
                if crit_name in cr_dict:
                    cr_val = cr_dict[crit_name]
                    if cr_val is not None:
                        # Validate consistency ratio is reasonable
                        if not isinstance(cr_val, (int, float)) or isnan(cr_val) or isinf(cr_val):
                            status = "❌ Invalid"
                            cr_ratio_display = "Error"
                        elif cr_val < 0.001:
                            status = "✅ Excellent (less than 0.001)"
                            cr_ratio_display = f"{cr_val:.4f}"
                        elif cr_val <= 0.10:
                            status = "✅ Good (less than or equal to 0.10)"
                            cr_ratio_display = f"{cr_val:.4f}"
                        else:
                            status = "⚠️ Poor (greater than 0.10)"
                            cr_ratio_display = f"{cr_val:.4f}"
                    else:
                        status = "—"
                        cr_ratio_display = "N/A"
                    
                    cr_rows.append({
                        "Criterion": crit_name,
                        "Consistency Ratio": cr_ratio_display,
                        "Status": status
                    })
            st.dataframe(pd.DataFrame(cr_rows),
                         width='stretch', hide_index=True)

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
