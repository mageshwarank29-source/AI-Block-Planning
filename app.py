# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from modules.optimizer import optimize_blocks


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Railway Block Planning",
    page_icon="🚆",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0e1117;
    }

    .stMetric {
        background-color: #171a21;
        padding: 15px;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.title("🚆 AI-Powered Automatic Block Planning")

st.markdown(
    """
    ### Indian Railways Block Planning System

    **AI + Optimization for safer and more efficient maintenance block allocation**
    """
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

MAINTENANCE_FILE = DATA_DIR / "maintenance.csv"
BLOCKS_FILE = DATA_DIR / "blocks.csv"
TRAINS_FILE = DATA_DIR / "trains.csv"


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    maintenance = pd.read_csv(MAINTENANCE_FILE)
    blocks = pd.read_csv(BLOCKS_FILE)
    trains = pd.read_csv(TRAINS_FILE)

    return maintenance, blocks, trains


try:

    maintenance, blocks, trains = load_data()

except Exception as e:

    st.error("❌ Could not load the CSV files.")

    st.error(str(e))

    st.stop()


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_maintenance = [
    "task_id",
    "department",
    "asset_type",
    "location",
    "corridor",
    "duration_hours",
    "criticality",
    "urgency",
    "overdue",
    "safety_impact",
    "status"
]

required_blocks = [
    "block_id",
    "corridor",
    "start_time",
    "end_time",
    "available"
]

required_trains = [
    "train_id",
    "train_type",
    "corridor",
    "start_time",
    "end_time"
]


missing_maintenance = [
    col for col in required_maintenance
    if col not in maintenance.columns
]

missing_blocks = [
    col for col in required_blocks
    if col not in blocks.columns
]

missing_trains = [
    col for col in required_trains
    if col not in trains.columns
]


if missing_maintenance:

    st.error(
        "❌ Missing columns in maintenance.csv: "
        + ", ".join(missing_maintenance)
    )

    st.stop()


if missing_blocks:

    st.error(
        "❌ Missing columns in blocks.csv: "
        + ", ".join(missing_blocks)
    )

    st.stop()


if missing_trains:

    st.error(
        "❌ Missing columns in trains.csv: "
        + ", ".join(missing_trains)
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

maintenance["corridor"] = (
    maintenance["corridor"]
    .astype(str)
    .str.strip()
    .str.upper()
)

blocks["corridor"] = (
    blocks["corridor"]
    .astype(str)
    .str.strip()
    .str.upper()
)

trains["corridor"] = (
    trains["corridor"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# PRIORITY CALCULATION
# ============================================================

def calculate_priority(row):

    criticality_scores = {
        "High": 40,
        "Medium": 25,
        "Low": 10
    }

    urgency_scores = {
        "High": 30,
        "Medium": 20,
        "Low": 10
    }

    overdue_scores = {
        "Yes": 15,
        "No": 0
    }

    safety_scores = {
        "High": 15,
        "Medium": 10,
        "Low": 5
    }

    criticality = str(
        row["criticality"]
    ).strip().title()

    urgency = str(
        row["urgency"]
    ).strip().title()

    overdue = str(
        row["overdue"]
    ).strip().title()

    safety = str(
        row["safety_impact"]
    ).strip().title()

    score = 0

    score += criticality_scores.get(
        criticality,
        0
    )

    score += urgency_scores.get(
        urgency,
        0
    )

    score += overdue_scores.get(
        overdue,
        0
    )

    score += safety_scores.get(
        safety,
        0
    )

    return score


maintenance["priority"] = maintenance.apply(
    calculate_priority,
    axis=1
)


# ============================================================
# DASHBOARD METRICS
# ============================================================

total_tasks = len(maintenance)

high_priority_tasks = len(
    maintenance[
        maintenance["priority"] >= 70
    ]
)

available_blocks = len(
    blocks[
        blocks["available"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(
            ["yes", "true", "1"]
        )
    ]
)

total_trains = len(trains)


# ============================================================
# METRICS DISPLAY
# ============================================================

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "📋 Pending Tasks",
        total_tasks
    )


with col2:

    st.metric(
        "🔥 High Priority",
        high_priority_tasks
    )


with col3:

    st.metric(
        "🟢 Available Blocks",
        available_blocks
    )


with col4:

    st.metric(
        "🚆 Scheduled Trains",
        total_trains
    )


# ============================================================
# MAINTENANCE TASKS
# ============================================================

st.markdown("---")

st.subheader("📋 Maintenance Tasks")


maintenance_display = maintenance.copy()

maintenance_display = maintenance_display[
    [
        "task_id",
        "department",
        "asset_type",
        "location",
        "corridor",
        "duration_hours",
        "priority",
        "status"
    ]
]


maintenance_display.columns = [
    "Task ID",
    "Department",
    "Asset",
    "Location",
    "Corridor",
    "Duration (hrs)",
    "Priority",
    "Status"
]


st.dataframe(
    maintenance_display,
    width="stretch",
    hide_index=True
)


# ============================================================
# AUTOMATIC BLOCK PLANNING
# ============================================================

st.markdown("---")

st.subheader("🤖 Automatic Block Planning")


st.write(
    """
    The AI planner analyzes maintenance priority,
    railway corridors, block duration, block availability
    and train schedules to generate an optimized
    maintenance plan.
    """
)


if st.button(
    "🚀 Generate Automatic Block Plan",
    type="primary"
):

    with st.spinner(
        "Optimizing railway blocks..."
    ):

        try:

            result = optimize_blocks(
                maintenance,
                blocks,
                trains
            )

            st.session_state[
                "assigned_df"
            ] = result

            st.success(
                f"✅ Optimization completed! "
                f"{len(result)} task(s) assigned."
            )

        except Exception as e:

            st.error(
                "❌ Optimization failed."
            )

            st.exception(e)


# ============================================================
# DISPLAY OPTIMIZED PLAN
# ============================================================

if "assigned_df" in st.session_state:

    assigned_df = (
        st.session_state["assigned_df"]
        .copy()
    )

    if (
        assigned_df is not None
        and not assigned_df.empty
    ):

        # ====================================================
        # AUTOMATIC BLOCK ALLOCATION
        # ====================================================

        st.markdown("---")

        st.subheader(
            "📋 Automatic Block Allocation"
        )


        allocation_display = (
            assigned_df.copy()
        )


        allocation_display = (
            allocation_display.rename(
                columns={
                    "task_id": "Task ID",
                    "department": "Department",
                    "asset_type": "Asset",
                    "location": "Location",
                    "corridor": "Corridor",
                    "priority": "Priority",
                    "duration_hours": "Duration (hrs)",
                    "block_id": "Block ID",
                    "block_start": "Block Start",
                    "block_end": "Block End",
                    "status": "Status"
                }
            )
        )


        # Alternative optimizer column names
        if "start_time" in allocation_display.columns:

            allocation_display = (
                allocation_display.rename(
                    columns={
                        "start_time":
                        "Block Start"
                    }
                )
            )


        if "end_time" in allocation_display.columns:

            allocation_display = (
                allocation_display.rename(
                    columns={
                        "end_time":
                        "Block End"
                    }
                )
            )


        wanted_columns = [
            "Task ID",
            "Department",
            "Asset",
            "Location",
            "Corridor",
            "Priority",
            "Duration (hrs)",
            "Block ID",
            "Block Start",
            "Block End",
            "Status"
        ]


        existing_columns = [
            col
            for col in wanted_columns
            if col in allocation_display.columns
        ]


        allocation_display = (
            allocation_display[
                existing_columns
            ]
        )


        st.dataframe(
            allocation_display,
            width="stretch",
            hide_index=True
        )


        # ====================================================
        # RAILWAY BLOCK TIMELINE
        # ====================================================

        st.markdown("---")

        st.subheader(
            "🚆 Railway Block Timeline"
        )


        st.write(
            "Visual representation of the "
            "automatically allocated railway "
            "maintenance blocks."
        )


        # Create separate copy
        timeline_df = (
            assigned_df.copy()
        )


        # ----------------------------------------------------
        # Normalize column names
        # ----------------------------------------------------

        timeline_df = (
            timeline_df.rename(
                columns={
                    "task_id": "Task ID",
                    "department": "Department",
                    "asset_type": "Asset",
                    "location": "Location",
                    "corridor": "Corridor",
                    "priority": "Priority",
                    "duration_hours": "Duration",
                    "block_id": "Block ID",
                    "block_start": "Block Start",
                    "block_end": "Block End"
                }
            )
        )


        # Support alternative names
        if "start_time" in timeline_df.columns:

            timeline_df[
                "Block Start"
            ] = timeline_df[
                "start_time"
            ]


        if "end_time" in timeline_df.columns:

            timeline_df[
                "Block End"
            ] = timeline_df[
                "end_time"
            ]


        # ----------------------------------------------------
        # Required timeline columns
        # ----------------------------------------------------

        required_timeline_columns = [
            "Task ID",
            "Department",
            "Asset",
            "Location",
            "Corridor",
            "Priority",
            "Block ID",
            "Block Start",
            "Block End"
        ]


        missing_timeline_columns = [
            col
            for col in required_timeline_columns
            if col not in timeline_df.columns
        ]


        if missing_timeline_columns:

            st.warning(
                "⚠️ Timeline is missing columns: "
                + ", ".join(
                    missing_timeline_columns
                )
            )

        else:

            try:

                # ------------------------------------------------
                # Convert block time
                # ------------------------------------------------

                timeline_df["Start"] = (
                    pd.to_datetime(
                        timeline_df[
                            "Block Start"
                        ].astype(str),
                        format="%H:%M"
                    )
                )


                timeline_df["End"] = (
                    pd.to_datetime(
                        timeline_df[
                            "Block End"
                        ].astype(str),
                        format="%H:%M"
                    )
                )


                # ------------------------------------------------
                # Create Plotly timeline
                # ------------------------------------------------

                fig = px.timeline(
                    timeline_df,
                    x_start="Start",
                    x_end="End",
                    y="Corridor",
                    color="Department",

                    hover_data=[
                        "Task ID",
                        "Asset",
                        "Location",
                        "Block ID",
                        "Priority"
                    ],

                    title=(
                        "Optimized Railway "
                        "Block Allocation"
                    )
                )


                # Reverse Y axis
                fig.update_yaxes(
                    autorange="reversed"
                )


                # Format time
                fig.update_xaxes(
                    tickformat="%H:%M",
                    title="Time"
                )


                fig.update_layout(
                    height=450,
                    xaxis_title="Time",
                    yaxis_title="Railway Corridor",
                    legend_title="Department"
                )


                st.plotly_chart(
                    fig,
                    width="stretch"
                )


            except Exception as e:

                st.error(
                    "❌ Timeline could not be generated."
                )

                st.error(str(e))


        # ====================================================
        # UNASSIGNED TASKS
        # ====================================================

        st.markdown("---")

        st.subheader(
            "⚠️ Tasks Not Assigned"
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # We use the ORIGINAL maintenance dataframe
        # for all task IDs.
        # ----------------------------------------------------

        all_task_ids = set(
            maintenance[
                "task_id"
            ]
            .astype(str)
        )


        # Find task ID from optimizer output
        if "task_id" in assigned_df.columns:

            assigned_task_ids = set(
                assigned_df[
                    "task_id"
                ]
                .astype(str)
            )

        elif "Task ID" in assigned_df.columns:

            assigned_task_ids = set(
                assigned_df[
                    "Task ID"
                ]
                .astype(str)
            )

        else:

            assigned_task_ids = set()


        # Determine unassigned tasks
        unassigned_ids = (
            all_task_ids
            - assigned_task_ids
        )


        if unassigned_ids:

            unassigned = maintenance[
                maintenance[
                    "task_id"
                ]
                .astype(str)
                .isin(unassigned_ids)
            ].copy()


            unassigned_display = (
                unassigned[
                    [
                        "task_id",
                        "department",
                        "corridor",
                        "duration_hours",
                        "priority"
                    ]
                ].copy()
            )


            unassigned_display.columns = [
                "Task ID",
                "Department",
                "Corridor",
                "Duration (hrs)",
                "Priority"
            ]


            st.dataframe(
                unassigned_display,
                width="stretch",
                hide_index=True
            )


            st.info(
                """
                Some tasks could not be assigned because
                no suitable block was available after
                checking corridor, duration, availability
                and train conflict constraints.
                """
            )

        else:

            st.success(
                "🎉 All maintenance tasks were "
                "successfully assigned!"
            )


    else:

        st.warning(
            "⚠️ No tasks were assigned."
        )


# ============================================================
# AVAILABLE BLOCKS
# ============================================================

st.markdown("---")

st.subheader(
    "🟢 Available Railway Blocks"
)


available_df = blocks[
    blocks[
        "available"
    ]
    .astype(str)
    .str.strip()
    .str.lower()
    .isin(
        ["yes", "true", "1"]
    )
].copy()


available_display = (
    available_df[
        [
            "block_id",
            "corridor",
            "start_time",
            "end_time",
            "available"
        ]
    ].copy()
)


available_display.columns = [
    "Block ID",
    "Corridor",
    "Start Time",
    "End Time",
    "Available"
]


st.dataframe(
    available_display,
    width="stretch",
    hide_index=True
)


# ============================================================
# TRAIN SCHEDULE
# ============================================================

st.markdown("---")

st.subheader(
    "🚆 Train Schedule"
)


train_display = trains.copy()


train_display.columns = [
    "Train ID",
    "Train Type",
    "Corridor",
    "Start Time",
    "End Time"
]


st.dataframe(
    train_display,
    width="stretch",
    hide_index=True
)


# ============================================================
# DEPARTMENT SUMMARY
# ============================================================

st.markdown("---")

st.subheader(
    "🏢 Department Summary"
)


department_summary = (
    maintenance
    .groupby("department")
    .agg(
        Total_Tasks=(
            "task_id",
            "count"
        ),

        Average_Priority=(
            "priority",
            "mean"
        ),

        Total_Duration=(
            "duration_hours",
            "sum"
        )
    )
    .reset_index()
)


department_summary[
    "Average_Priority"
] = (
    department_summary[
        "Average_Priority"
    ]
    .round(1)
)


department_summary.columns = [
    "Department",
    "Total Tasks",
    "Average Priority",
    "Total Duration (hrs)"
]


st.dataframe(
    department_summary,
    width="stretch",
    hide_index=True
)


# ============================================================
# PRIORITY DISTRIBUTION
# ============================================================

st.markdown("---")

st.subheader(
    "📊 Maintenance Priority Distribution"
)


priority_chart = px.bar(
    maintenance,
    x="task_id",
    y="priority",
    color="department",

    title="Task Priority Scores",

    labels={
        "task_id": "Task ID",
        "priority": "Priority Score",
        "department": "Department"
    }
)


priority_chart.update_layout(
    height=400
)


st.plotly_chart(
    priority_chart,
    width="stretch"
)


# ============================================================
# HOW THE SYSTEM WORKS
# ============================================================

st.markdown("---")

st.subheader(
    "🧠 How the AI Planner Works"
)


st.markdown(
    """
    **1️⃣ Data Integration**

    Maintenance tasks, railway blocks and train schedules
    are loaded from structured CSV data.

    **2️⃣ Priority Calculation**

    Each maintenance task receives a priority score based
    on criticality, urgency, overdue status and safety impact.

    **3️⃣ Constraint Checking**

    The system checks corridor compatibility, maintenance
    duration, block availability and train conflicts.

    **4️⃣ Optimization**

    Google OR-Tools selects an optimized combination of
    blocks to maximize the total priority of assigned tasks.

    **5️⃣ Visualization**

    The final plan is displayed as a table and railway
    timeline for easy decision-making.
    """
)


# ============================================================
# PLANNING RULES
# ============================================================

st.subheader(
    "📌 Planning Rules"
)


st.markdown(
    """
    - ✅ Task and block must belong to the same corridor.
    - ✅ Block must be available.
    - ✅ Block duration must be sufficient.
    - ✅ One block cannot be assigned to multiple tasks.
    - ✅ Train movement conflicts are avoided.
    - ✅ Higher-priority tasks are preferred.
    - ✅ OR-Tools performs the final optimization.
    """
)


# ============================================================
# PROTOTYPE NOTE
# ============================================================

st.markdown("---")

st.subheader(
    "ℹ️ Prototype Information"
)


st.info(
    """
    This prototype currently uses structured demonstration
    data for maintenance tasks, railway blocks and train
    schedules.

    The architecture can later be connected to authorized
    railway data sources and real-time operational systems.
    """
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🚆 AI-Powered Automatic Block Planning System | "
    "SIH Prototype | Python + Streamlit + OR-Tools"
)