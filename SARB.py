# StudentID_Lab3.py
# BSD3513 - Introduction to Artificial Intelligence
# Lab Report 3: Scholarship Advisory Rule-Based System
#
# Run locally:
#   pip install -r requirements.txt
#   streamlit run StudentID_Lab3.py

import json
import operator
from typing import Any, Dict, List, Tuple

import streamlit as st


# ---------------------------------------------------------------------
# 1. Rule engine
# ---------------------------------------------------------------------

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

# These are the EXACT five rules supplied in the Lab Report 3 brief.
DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0],
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need",
        },
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1],
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need",
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000],
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score",
        },
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5],
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement",
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2],
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records",
        },
    },
]


def evaluate_condition(facts: Dict[str, Any], condition: List[Any]) -> bool:
    """Evaluate one condition in the format [field, operator, comparison_value]."""
    if not isinstance(condition, list) or len(condition) != 3:
        return False

    field, symbol, comparison_value = condition

    if field not in facts or symbol not in OPS:
        return False

    try:
        return OPS[symbol](facts[field], comparison_value)
    except (TypeError, ValueError):
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions in a rule must be true (AND logic)."""
    conditions = rule.get("conditions", [])
    return bool(conditions) and all(
        evaluate_condition(facts, condition) for condition in conditions
    )


def validate_rules(rules: Any) -> Tuple[bool, str]:
    """Check the basic structure of the JSON rule configuration."""
    if not isinstance(rules, list):
        return False, "The rules configuration must be a JSON array."

    required_rule_keys = {"name", "priority", "conditions", "action"}

    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            return False, f"Rule {index} must be a JSON object."

        missing = required_rule_keys - set(rule.keys())
        if missing:
            return False, f"Rule {index} is missing: {', '.join(sorted(missing))}."

        if not isinstance(rule["name"], str) or not rule["name"].strip():
            return False, f"Rule {index} must have a name."

        if not isinstance(rule["priority"], (int, float)):
            return False, f"Rule {index} priority must be numeric."

        if not isinstance(rule["conditions"], list) or not rule["conditions"]:
            return False, f"Rule {index} must contain at least one condition."

        for condition in rule["conditions"]:
            if (
                not isinstance(condition, list)
                or len(condition) != 3
                or condition[1] not in OPS
            ):
                return False, (
                    f"Rule {index} contains an invalid condition. "
                    "Use [field, operator, value]."
                )

        if not isinstance(rule["action"], dict):
            return False, f"Rule {index} action must be a JSON object."

        if "decision" not in rule["action"] or "reason" not in rule["action"]:
            return False, f"Rule {index} action needs decision and reason."

    return True, "All rules have a valid structure."


def run_rules(
    facts: Dict[str, Any], rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Evaluate all rules.
    If several rules match, the rule with the highest priority determines
    the final decision. All matched rules are returned for transparency.
    """
    fired_rules = [rule for rule in rules if rule_matches(facts, rule)]

    fired_rules_sorted = sorted(
        fired_rules,
        key=lambda rule: rule.get("priority", 0),
        reverse=True,
    )

    if not fired_rules_sorted:
        return (
            {
                "decision": "NO_MATCH",
                "reason": (
                    "No supplied rule matched this applicant. "
                    "The case requires manual committee assessment."
                ),
            },
            [],
        )

    selected_action = fired_rules_sorted[0]["action"]
    return selected_action, fired_rules_sorted


# ---------------------------------------------------------------------
# 2. Streamlit page configuration and interface
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Scholarship Advisory System",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Scholarship Advisory System")
st.caption(
    "BSD3513 | Lab Report 3 – Knowledge Representation System | "
    "A transparent rule-based decision support prototype"
)

st.info(
    "This application provides scholarship recommendations using the "
    "five rules specified in the laboratory assignment. Final awards "
    "should be confirmed by the university scholarship committee."
)

# Sidebar: applicant facts
st.sidebar.header("Applicant Information")
st.sidebar.caption("Enter the applicant's details below.")

with st.sidebar.form("applicant_form"):
    applicant_name = st.text_input("Applicant name", value="Applicant 001")

    cgpa = st.number_input(
        "Cumulative GPA (CGPA)",
        min_value=0.0,
        max_value=4.0,
        value=3.70,
        step=0.01,
        format="%.2f",
        help="Enter a CGPA between 0.00 and 4.00.",
    )

    family_income = st.number_input(
        "Monthly family income (RM)",
        min_value=0.0,
        max_value=100000.0,
        value=3000.0,
        step=100.0,
        help="Enter the total monthly family income in Malaysian Ringgit.",
    )

    co_curricular_score = st.number_input(
        "Co-curricular involvement score",
        min_value=0,
        max_value=100,
        value=85,
        step=1,
        help="Enter a score between 0 and 100.",
    )

    community_service_hours = st.number_input(
        "Community service hours",
        min_value=0.0,
        max_value=10000.0,
        value=20.0,
        step=1.0,
    )

    current_semester = st.number_input(
        "Current semester of study",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
    )

    disciplinary_actions = st.number_input(
        "Number of disciplinary actions",
        min_value=0,
        max_value=100,
        value=0,
        step=1,
    )

    evaluate_clicked = st.form_submit_button(
        "Evaluate Scholarship Eligibility",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# 3. JSON rule editor
# ---------------------------------------------------------------------

st.sidebar.divider()
st.sidebar.header("Rule Configuration (JSON)")
st.sidebar.caption(
    "The default editor contains the five rules from the assignment. "
    "You may edit the JSON to test alternative rule configurations."
)

default_json = json.dumps(DEFAULT_RULES, indent=4, ensure_ascii=False)

if "rules_text" not in st.session_state:
    st.session_state.rules_text = default_json

rules_text = st.sidebar.text_area(
    "Edit rules",
    key="rules_text",
    height=430,
)

reset_rules = st.sidebar.button(
    "Restore lecturer's original rules",
    use_container_width=True,
)

if reset_rules:
    st.session_state.rules_text = default_json
    st.rerun()


# ---------------------------------------------------------------------
# 4. Prepare facts and parse the JSON rules
# ---------------------------------------------------------------------

facts = {
    "cgpa": float(cgpa),
    "family_income": float(family_income),
    "co_curricular_score": int(co_curricular_score),
    "community_service_hours": float(community_service_hours),
    "current_semester": int(current_semester),
    "disciplinary_actions": int(disciplinary_actions),
}

try:
    active_rules = json.loads(rules_text)
    rules_valid, validation_message = validate_rules(active_rules)
except json.JSONDecodeError as error:
    active_rules = []
    rules_valid = False
    validation_message = (
        f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
    )

# Main dashboard
metric1, metric2, metric3 = st.columns(3)

metric1.metric("Applicant CGPA", f"{cgpa:.2f} / 4.00")
metric2.metric("Monthly Family Income", f"RM {family_income:,.2f}")
metric3.metric("Co-curricular Score", f"{co_curricular_score} / 100")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Applicant Profile")
    st.write(f"**Applicant:** {applicant_name or 'Not provided'}")
    st.write(f"**Community service hours:** {community_service_hours:g}")
    st.write(f"**Current semester:** {current_semester}")
    st.write(f"**Disciplinary actions:** {disciplinary_actions}")

    with st.expander("View all applicant facts"):
        st.json(facts)

with right:
    st.subheader("Rule Engine Status")

    if rules_valid:
        st.success(validation_message)
        st.write(f"**Number of active rules:** {len(active_rules)}")
        st.write(
            "**Evaluation method:** All conditions within a rule must be "
            "satisfied (AND logic)."
        )
        st.write(
            "**Conflict resolution:** The matching rule with the highest "
            "priority determines the final decision."
        )
    else:
        st.error(validation_message)
        st.warning("Correct the JSON configuration before evaluating.")

st.divider()

# ---------------------------------------------------------------------
# 5. Evaluation results
# ---------------------------------------------------------------------

if evaluate_clicked:
    if not rules_valid:
        st.error("Evaluation stopped because the JSON rules are invalid.")
    else:
        decision, matched_rules = run_rules(facts, active_rules)

        st.subheader("Scholarship Evaluation Result")

        decision_name = decision.get("decision", "NO_MATCH")
        reason = decision.get("reason", "No explanation available.")

        result_col, explanation_col = st.columns([1, 2])

        with result_col:
            if decision_name == "AWARD_FULL":
                st.success(f"### {decision_name}")
            elif decision_name == "AWARD_PARTIAL":
                st.info(f"### {decision_name}")
            elif decision_name == "REVIEW":
                st.warning(f"### {decision_name}")
            elif decision_name == "REJECT":
                st.error(f"### {decision_name}")
            else:
                st.warning(f"### {decision_name}")

        with explanation_col:
            st.markdown("**Decision explanation**")
            st.write(reason)

        st.markdown("#### Rule evaluation details")

        if matched_rules:
            st.write(
                f"**{len(matched_rules)} rule(s) matched.** "
                "The rules below are arranged from highest to lowest priority."
            )

            for rank, rule in enumerate(matched_rules, start=1):
                is_selected = rank == 1
                heading = (
                    f"{rank}. {rule['name']} "
                    f"(Priority: {rule['priority']})"
                )

                with st.expander(
                    heading,
                    expanded=is_selected,
                ):
                    if is_selected:
                        st.success("Selected rule – determines the final decision.")

                    st.write(f"**Decision:** {rule['action']['decision']}")
                    st.write(f"**Reason:** {rule['action']['reason']}")
                    st.write("**Conditions:**")

                    for condition in rule["conditions"]:
                        field, symbol, target = condition
                        actual_value = facts.get(field, "Field not collected")
                        passed = evaluate_condition(facts, condition)

                        status = "PASS" if passed else "NOT MET"
                        st.write(
                            f"- `{field}`: actual value **{actual_value}** "
                            f"{symbol} **{target}** → **{status}**"
                        )
        else:
            st.warning(
                "No rule matched. This applicant should be referred for "
                "manual assessment rather than receiving an invented decision."
            )

        st.caption(
            "Note: Community service hours and current semester are recorded "
            "in the applicant profile, but are not used in the supplied five "
            "rules because the assignment does not specify conditions for them."
        )

else:
    st.subheader("Ready for Evaluation")
    st.write(
        "Complete the applicant information in the sidebar, check the JSON "
        "rules, and click **Evaluate Scholarship Eligibility**."
    )

# ---------------------------------------------------------------------
# 6. Rule reference
# ---------------------------------------------------------------------

with st.expander("View the five original scholarship rules"):
    st.json(DEFAULT_RULES)

st.divider()
st.caption(
    "BSD3513 – Introduction to Artificial Intelligence | "
    "Lab Report 3 | Scholarship Advisory Rule-Based System"
)
