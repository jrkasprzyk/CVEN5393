"""
AHP Streamlit App
Parses gluc/ahp YAML format and computes weights + consistency ratios using ahpy.
"""

import streamlit as st
import streamlit.components.v1 as components
import yaml
import ahpy
import pandas as pd
import itertools
import json
from fractions import Fraction
from numpy import isnan, isinf
import re

WEIGHT_SUM_WARNING_TOLERANCE = 1e-3

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


def parse_name_list(raw_text):
    """Parse comma-separated or line-separated names into an ordered unique list."""
    tokens = []
    for line in raw_text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        tokens.extend([part for part in parts if part])

    seen = set()
    names = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            names.append(token)
    return names


def format_pairwise_value(value):
    """Render guided-builder values in gluc/ahp-friendly form."""
    rounded_int = round(value)
    if abs(value - rounded_int) < 1e-9:
        return str(int(rounded_int))

    reciprocal = round(1.0 / value)
    if reciprocal > 0 and abs(value - (1.0 / reciprocal)) < 1e-9:
        return f"1/{int(reciprocal)}"

    return f"{value:.6g}"


def yaml_quote(text):
    """Quote strings only when needed for YAML compatibility."""
    if re.fullmatch(r"[A-Za-z0-9 _./()-]+", text):
        lowered = text.strip().lower()
        if lowered not in {"null", "true", "false", "yes", "no", "on", "off"}:
            return text
    return "'" + text.replace("'", "''") + "'"


def render_guided_yaml(goal_name, alternatives, criteria_pairwise, criterion_alt_pairwise):
    """Render YAML that matches the gluc/ahp structure used by the app examples."""
    lines = [
        "Version: 2.0",
        "",
        "Alternatives: &alternatives",
    ]

    for alternative in alternatives:
        lines.append(f"  {yaml_quote(alternative)}:")

    lines.extend([
        "",
        "Goal:",
        f"  name: {yaml_quote(goal_name)}",
        "  preferences:",
        "    pairwise:",
    ])

    for item_a, item_b, value in criteria_pairwise:
        lines.append(
            f"      - [{yaml_quote(item_a)}, {yaml_quote(item_b)}, {format_pairwise_value(value)}]"
        )

    lines.append("  children:")

    for criterion, comparisons in criterion_alt_pairwise.items():
        lines.extend([
            f"    {yaml_quote(criterion)}:",
            "      preferences:",
            "        pairwise:",
        ])
        for item_a, item_b, value in comparisons:
            lines.append(
                f"          - [{yaml_quote(item_a)}, {yaml_quote(item_b)}, {format_pairwise_value(value)}]"
            )
        lines.append("      children: *alternatives")

    return "\n".join(lines) + "\n"


def render_copy_to_clipboard_button(text, button_text="Copy YAML to clipboard"):
        """Render a small browser-side copy button for generated YAML text."""
        button_id = f"copy_yaml_{abs(hash(text))}"
        payload = json.dumps(text)
        html = f"""
        <div style=\"margin: 0.25rem 0 0.75rem 0;\">
            <button
                id=\"{button_id}\"
                style=\"padding: 0.45rem 0.8rem; border: 1px solid #d0d7de; border-radius: 0.5rem; background: white; cursor: pointer;\"
            >
                {button_text}
            </button>
            <span id=\"{button_id}_status\" style=\"margin-left: 0.6rem; font-family: sans-serif; font-size: 0.9rem;\"></span>
        </div>
        <script>
            const copyButton = document.getElementById({json.dumps(button_id)});
            const status = document.getElementById({json.dumps(button_id + '_status')});
            copyButton.addEventListener('click', async () => {{
                try {{
                    await navigator.clipboard.writeText({payload});
                    status.textContent = 'Copied';
                }} catch (error) {{
                    status.textContent = 'Clipboard blocked by browser';
                }}
            }});
        </script>
        """
        components.html(html, height=48)


    # TODO: Guided builder follow-ups:
    # - Add a compact mode for larger criteria sets.
    # - Let users edit the generated YAML inline before analysis.
    # - Support multi-level hierarchies instead of a single criteria layer.
def build_pairwise_from_prompts(items, section_key, title):
    """Collect pairwise preferences for items using guided sidebar prompts."""
    comparisons = []
    pairings = list(itertools.combinations(items, 2))

    st.markdown(f"#### {title}")
    st.caption("Choose which item is preferred in each pair and by how much (Saaty 1-9 scale).")

    scale_values = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    scale_help = {
        1: "Equal",
        3: "Moderate",
        5: "Strong",
        7: "Very strong",
        9: "Extreme",
    }

    for idx, (item_a, item_b) in enumerate(pairings):
        row_col1, row_col2 = st.columns([2, 1])
        with row_col1:
            preferred = st.selectbox(
                f"{item_a} vs {item_b}",
                [item_a, item_b],
                key=f"{section_key}_pref_{idx}",
            )
        with row_col2:
            intensity = st.selectbox(
                f"Intensity for {item_a} vs {item_b}",
                scale_values,
                index=2,
                key=f"{section_key}_int_{idx}",
                help="1 = equal, 3 = moderate, 5 = strong, 7 = very strong, 9 = extreme",
                label_visibility="hidden",
            )

        value = float(intensity)
        if preferred == item_b:
            value = 1.0 / value

        descriptor = scale_help.get(intensity, f"Level {intensity}")
        st.caption(f"Preferred: {preferred} ({descriptor.lower()})")

        comparisons.append([item_a, item_b, value])

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
    
    pair_errors = []

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

            value = None
            try:
                value = eval(body, {"__builtins__": {}}, local_scope)
            except Exception:
                # Fallback: evaluate reversed pair then invert.
                reverse_scope = {
                    'a1': alt2,
                    'a2': alt1,
                    'alternatives_data': alternatives_data,
                    'min': min,
                    'max': max,
                }
                try:
                    reverse_value = eval(body, {"__builtins__": {}}, reverse_scope)
                    reverse_value = float(reverse_value)
                    if reverse_value > 0:
                        value = 1.0 / reverse_value
                except Exception as e:
                    pair_errors.append(f"{alt1} vs {alt2}: {e}")
                    continue

            try:
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Function must return a number, got {type(value)}")

                if not (0 < value < float('inf')):
                    raise ValueError(f"Invalid comparison value: {value}")

                value = parse_fraction(value)

                if value <= 0 or value > 9:
                    st.warning(
                        f"⚠️ Pairwise value {value} (from {alt1} vs {alt2}) is outside AHP scale.")

                comparisons[(str(alt1), str(alt2))] = value
            except Exception as e:
                pair_errors.append(f"{alt1} vs {alt2}: {e}")

    if not comparisons:
        raise ValueError(
            f"Error evaluating pairwiseFunction: no valid comparisons generated for '{criterion_name}'.")

    if pair_errors:
        st.warning(
            f"⚠️ Some pairwiseFunction pairs in '{criterion_name}' were skipped: {len(pair_errors)} pair(s).")
    
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


def build_ahpy_model(goal_node, alternatives_data=None, parent_name=None, collector=None):
    """
    Recursively walk the gluc/ahp goal tree and build ahpy Compare objects.
    Supports both 'pairwise' (list) and 'pairwiseFunction' (R code) formats.
    Returns the root Compare object with children properly attached.
    """
    name = goal_node.get("name", parent_name or "Goal")

    # Criteria-level pairwise (children comparisons)
    children = goal_node.get("children", {})
    prefs = goal_node.get("preferences", {})
    
    pairwise = prefs.get("pairwise", []) if prefs else []
    pairwise_func = prefs.get("pairwiseFunction") if prefs else None

    if collector is None:
        collector = []

    compare_obj = None
    
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
                return None
        elif pairwise:
            try:
                comparisons = extract_comparisons(pairwise)
            except Exception as e:
                st.error(f"Error parsing pairwise comparisons for '{name}': {e}")
                return None
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
                compare_obj = ahpy.Compare(name=name, comparisons=comparisons)
                collector.append(compare_obj)
            except Exception as e:
                st.error(f"Error creating AHP comparison for '{name}': {e}")
                return None

        # Recurse into children and build child Compare objects.
        # Only descend into nodes that are actually compared at this level.
        child_compares = []
        if comparisons:
            compared_items = set()
            for a, b in comparisons.keys():
                compared_items.add(a)
                compared_items.add(b)

            for child_name in compared_items:
                child_node = children.get(child_name)
                if isinstance(child_node, dict) and "preferences" in child_node:
                    child_node_copy = child_node.copy()
                    child_node_copy["name"] = child_name
                    child_compare = build_ahpy_model(
                        child_node_copy, alternatives_data, child_name, collector)
                    if child_compare is not None:
                        child_compares.append(child_compare)

        # Add child Compare objects to this Compare object.
        # Some ahpy versions may return a new Compare object instead of mutating in place.
        if compare_obj is not None and child_compares:
            try:
                maybe_updated = compare_obj.add_children(child_compares)
                if maybe_updated is not None:
                    compare_obj = maybe_updated
            except Exception as e:
                st.error(f"Error attaching child comparisons to '{name}': {e}")
                return compare_obj

    return compare_obj


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
            "Paste .yaml content",
            "Guided Builder"
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

    elif input_mode == "Guided Builder":
        st.sidebar.markdown("Build a YAML model from prompts.")
        goal_name = st.sidebar.text_input("Goal name", value="Choose the Best Option")
        alternatives_raw = st.sidebar.text_area(
            "Alternatives (comma or newline separated)",
            value="Option A\nOption B\nOption C",
            height=120,
        )
        criteria_raw = st.sidebar.text_area(
            "Criteria (comma or newline separated)",
            value="Cost\nQuality\nRisk",
            height=120,
        )

        alternatives = parse_name_list(alternatives_raw)
        criteria = parse_name_list(criteria_raw)

        st.sidebar.caption("Note: Guided Builder currently only supports "
                           "a single goal with criteria and alternatives (no subcriteria)."
                           " There is also no support for pairwiseFunction, only direct pairwise comparisons.")
        
        if len(alternatives) < 2:
            st.warning("Add at least 2 alternatives in the Guided Builder.")
            return ""
        if len(criteria) < 2:
            st.warning("Add at least 2 criteria in the Guided Builder.")
            return ""

        st.subheader("Guided YAML Builder")
        criteria_pairwise = build_pairwise_from_prompts(
            criteria,
            section_key="goal_criteria",
            title="Step 1: Compare Criteria",
        )

        criterion_alt_pairwise = {}
        for criterion in criteria:
            criterion_alt_pairwise[criterion] = build_pairwise_from_prompts(
                alternatives,
                section_key=f"alts_{criterion}",
                title=f"Step 2: Compare Alternatives for '{criterion}'",
            )

        yaml_text = render_guided_yaml(
            goal_name,
            alternatives,
            criteria_pairwise,
            criterion_alt_pairwise,
        )
        st.markdown("#### Generated YAML Preview")
        render_copy_to_clipboard_button(yaml_text)
        st.code(yaml_text, language="yaml")
        suggested_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", goal_name.strip()) or "ahp_model"
        downloaded = st.download_button(
            "Download YAML",
            data=yaml_text,
            file_name=f"{suggested_name}.yaml",
            mime="application/x-yaml",
            help="Save the generated YAML file for reuse.",
        )
        if downloaded:
            st.success(f"Downloaded: {suggested_name}.yaml")
        return yaml_text

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
        compare_catalog = []
        root_compare = build_ahpy_model(goal, alternatives_data, collector=compare_catalog)

        if root_compare is None:
            st.error(
                "No pairwise comparisons found. "
                "Check that your YAML has 'preferences:' sections with either "
                " 'pairwise:' or 'pairwiseFunction:'.")
            st.stop()

        # The root_compare now has all children properly attached (when supported by ahpy)
        compares = [root_compare]

        # Prefer the explicit catalog of created Compare objects.
        # Fallback to root-only list if nothing was collected.
        all_compares = compare_catalog if compare_catalog else [root_compare]
        
        # Remove the root compare from all_compares for consistency ratios
        children_and_intermediate_compares = all_compares[1:]

        compare_by_name = {c.name: c for c in all_compares}

        def collect_alternative_weights_from_yaml(goal_subtree, path_weight=1.0):
            """Accumulate alternative weights by traversing YAML hierarchy with Compare lookup."""
            alt_totals = {}
            leaf_weight_sum = 0.0

            node_name = goal_subtree.get("name")
            node_compare = compare_by_name.get(node_name)
            if node_compare is None:
                return alt_totals, leaf_weight_sum

            # Leaf Compare that ranks alternatives
            if node_compare.local_weights and any(k in alternative_names for k in node_compare.local_weights.keys()):
                leaf_weight_sum += path_weight
                for alt_name, alt_local_weight in node_compare.local_weights.items():
                    if alt_name in alternative_names:
                        alt_totals[alt_name] = alt_totals.get(alt_name, 0.0) + path_weight * alt_local_weight
                return alt_totals, leaf_weight_sum

            # Internal criteria node: recurse through YAML children that are criteria
            children = goal_subtree.get("children", {}) or {}
            for child_name, child_node in children.items():
                if isinstance(child_node, dict) and "preferences" in child_node:
                    child_weight = node_compare.local_weights.get(child_name, 0.0)
                    child_subtree = child_node.copy()
                    child_subtree["name"] = child_name
                    child_alt_totals, child_leaf_sum = collect_alternative_weights_from_yaml(
                        child_subtree, path_weight * child_weight)
                    leaf_weight_sum += child_leaf_sum
                    for alt_name, alt_val in child_alt_totals.items():
                        alt_totals[alt_name] = alt_totals.get(alt_name, 0.0) + alt_val

            return alt_totals, leaf_weight_sum

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
            # Compute global weights for alternatives by traversing YAML criteria tree
            goal_for_weights = goal.copy()
            goal_for_weights["name"] = goal_name
            alt_weights, total_criteria_weight = collect_alternative_weights_from_yaml(goal_for_weights, 1.0)

            # Validate that weights sum to approximately 1 (within numerical precision)
            if abs(total_criteria_weight - 1.0) > WEIGHT_SUM_WARNING_TOLERANCE:
                st.warning(
                    f"⚠️ Criteria weights sum to {total_criteria_weight:.6f}, not 1.0. "
                    f"Differences above {WEIGHT_SUM_WARNING_TOLERANCE:.3f} are flagged; results may be unreliable."
                )

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
                
                if sorted_alts:
                    alt_df = pd.DataFrame(
                        {"Alternative": [a[0] for a in sorted_alts],
                         "Global Weight": [f"{a[1]:.4f}" for a in sorted_alts],
                         "Score %": [f"{a[1]*100:.1f}%" for a in sorted_alts]}
                    ).reset_index(drop=True)
                    alt_df.index = alt_df.index + 1  # rank from 1
                    st.dataframe(alt_df, width='stretch')
                    st.caption("Note: Small deviations from 1.0 are expected due to floating-point rounding.")

                    winner = alt_df.iloc[0]["Alternative"]
                    st.success(f"🏆 Recommended choice: **{winner}**")
                else:
                    st.warning("⚠️ No alternative weights were calculated. Check that alternatives are properly compared in all leaf criteria.")
            else:
                st.info(
                    "No separate alternatives detected — showing criteria weights only.")

        # Per-criterion consistency ratios
        if children_and_intermediate_compares:
            st.markdown("### Per-Criterion Consistency Ratios")
            cr_rows = []
            # Build a dict of consistency ratios keyed by criterion name
            cr_dict = {c.name: c.consistency_ratio for c in children_and_intermediate_compares}
            # Sort criteria by name for consistent ordering
            sorted_criteria_names = sorted(cr_dict.keys())
            
            for crit_name in sorted_criteria_names:
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

        # Persistent debug panel for hierarchy and weight diagnostics
        with st.expander("Debug Output"):
            st.markdown("### Model Summary")
            st.write(f"Goal: {goal_name}")
            st.write(f"Top-level criteria count: {len(crit_weights)}")
            st.write(f"Top-level criteria weights: {dict(crit_weights)}")
            st.write(f"Total Compare objects in hierarchy: {len(all_compares)}")

            st.markdown("### Alternatives")
            st.write(f"Declared alternatives ({len(alternative_names)}): {sorted(list(alternative_names))}")
            st.write(f"Alternatives with computed weights ({len(alt_weights)}): {sorted(list(alt_weights.keys()))}")
            st.write(f"Missing alternatives ({len(missing_alts)}): {sorted(list(missing_alts))}")

            st.markdown("### Weight Diagnostics")
            st.write(f"Total leaf path weight sum: {total_criteria_weight:.6f}")
            st.write(f"Alternative weight sum: {sum(alt_weights.values()):.6f}")
            st.write(f"Ranked alternatives count: {len(sorted_alts)}")

            # Collect true leaf criteria from YAML hierarchy (not from Compare.children)
            def _collect_yaml_leaf_criteria(goal_subtree, path_prefix=""):
                node_name = goal_subtree.get("name", "")
                current_path = f"{path_prefix} > {node_name}" if path_prefix else node_name
                children = goal_subtree.get("children", {}) or {}
                criteria_children = {
                    child_name: child_node
                    for child_name, child_node in children.items()
                    if isinstance(child_node, dict) and "preferences" in child_node
                }

                # Leaf criterion: has a Compare and no criteria-children beneath it
                if not criteria_children:
                    return [
                        {
                            "name": node_name,
                            "path": current_path,
                            "compare": compare_by_name.get(node_name),
                        }
                    ]

                leaves = []
                for child_name, child_node in criteria_children.items():
                    child_subtree = child_node.copy()
                    child_subtree["name"] = child_name
                    leaves.extend(_collect_yaml_leaf_criteria(child_subtree, current_path))
                return leaves

            goal_for_debug = goal.copy()
            goal_for_debug["name"] = goal_name
            leaf_nodes = _collect_yaml_leaf_criteria(goal_for_debug)
            leaf_rows = []
            for leaf in leaf_nodes:
                compare_obj = leaf.get("compare")
                local = dict(compare_obj.local_weights) if compare_obj and compare_obj.local_weights else {}
                overlaps_alts = [k for k in local.keys() if k in alternative_names]
                leaf_rows.append({
                    "Leaf Node": leaf.get("name"),
                    "Path": leaf.get("path"),
                    "Compare Found": compare_obj is not None,
                    "Has Alt Weights": bool(overlaps_alts),
                    "Alt Keys Found": overlaps_alts,
                    "Local Weights": local,
                })

            st.markdown("### Leaf Nodes")
            st.dataframe(pd.DataFrame(leaf_rows), width='stretch', hide_index=True)

            # Detailed contribution audit: path_weight * local_alt_weight at each leaf
            def _collect_contribution_rows(goal_subtree, path_weight=1.0, path_prefix=""):
                rows = []
                node_name = goal_subtree.get("name", "")
                current_path = f"{path_prefix} > {node_name}" if path_prefix else node_name
                node_compare = compare_by_name.get(node_name)
                if node_compare is None:
                    return rows

                children = goal_subtree.get("children", {}) or {}
                criteria_children = {
                    child_name: child_node
                    for child_name, child_node in children.items()
                    if isinstance(child_node, dict) and "preferences" in child_node
                }

                # Leaf criterion: emit one contribution row per alternative
                if not criteria_children:
                    if node_compare.local_weights:
                        for alt_name, alt_local_weight in node_compare.local_weights.items():
                            if alt_name in alternative_names:
                                rows.append({
                                    "Leaf Criterion": node_name,
                                    "Path": current_path,
                                    "Path Weight": path_weight,
                                    "Alternative": alt_name,
                                    "Local Alt Weight": float(alt_local_weight),
                                    "Contribution": path_weight * float(alt_local_weight),
                                })
                    return rows

                # Internal criterion: recurse to child criteria
                for child_name, child_node in criteria_children.items():
                    child_weight = float(node_compare.local_weights.get(child_name, 0.0))
                    child_subtree = child_node.copy()
                    child_subtree["name"] = child_name
                    rows.extend(_collect_contribution_rows(
                        child_subtree,
                        path_weight * child_weight,
                        current_path,
                    ))

                return rows

            contribution_rows = _collect_contribution_rows(goal_for_debug, 1.0)
            contrib_df = pd.DataFrame(contribution_rows)
            if not contrib_df.empty:
                contrib_df = contrib_df.sort_values(
                    by=["Alternative", "Leaf Criterion"]
                ).reset_index(drop=True)
                st.markdown("### Contribution Breakdown")
                st.dataframe(contrib_df, width='stretch', hide_index=True)

                contrib_sum_df = contrib_df.groupby("Alternative", as_index=False)["Contribution"].sum()
                contrib_sum_df = contrib_sum_df.sort_values(
                    by="Contribution", ascending=False
                ).reset_index(drop=True)
                st.markdown("### Contribution Sums By Alternative")
                st.dataframe(contrib_sum_df, width='stretch', hide_index=True)
            else:
                st.markdown("### Contribution Breakdown")
                st.info("No contribution rows were generated.")

        with st.expander("Acknowledgements and Limitations"):
            st.markdown("""
            - This tool is provided for educational purposes only. For high-stakes or operational decisions, consult a qualified decision-analysis professional or use software designed for production decision support.
            - This software is provided "as is" and "as available," without warranties of any kind, whether express, implied, or statutory, including implied warranties of merchantability, fitness for a particular purpose, title, non-infringement, accuracy, completeness, reliability, availability, and performance.
            - To the maximum extent permitted by applicable law, the authors, instructors, contributors, and affiliated institutions disclaim liability for any direct, indirect, incidental, consequential, special, exemplary, or punitive damages, and for any loss of data, business, profits, opportunities, or decision quality arising from or related to the use of, or inability to use, this tool or its outputs.
            - This tool relies on the `ahpy` library for AHP calculations. That library, like any software dependency, may have limitations when handling complex hierarchies, unusual inputs, or edge cases.
            - YAML input must follow the expected structure. Formatting or schema errors may prevent successful parsing or lead to incorrect results.
            - Consistency ratios are calculated from the comparisons you provide. If the input is incomplete, contradictory, or highly inconsistent, the resulting weights and rankings may be unreliable.
            - This tool assumes that all criteria and alternatives are compared appropriately at the relevant levels of the hierarchy. Missing or misapplied comparisons can affect the validity of the results.
            - Review consistency ratios carefully, and revise pairwise comparisons when they indicate poor consistency (for example, when CR > 0.10).
            - Guided Builder is a simplified interface for generating YAML. It may not support all use cases or complex hierarchies, so advanced models may still require manual YAML editing.
            - Thanks to Lauren Way who provided an example analysis with the Guided Builder, which helped shape the design and functionality of this tool.
            """)
    
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
