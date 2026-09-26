import pandas as pd
from ortools.sat.python import cp_model


def optimize_blocks(maintenance_df, blocks_df, trains_df):

    # ---------------------------------------------------------
    # Priority calculation
    # ---------------------------------------------------------

    def calculate_priority(row):

        score = 0

        score += {
            "High": 30,
            "Medium": 20,
            "Low": 10
        }.get(str(row["criticality"]).strip().title(), 0)

        score += {
            "High": 25,
            "Medium": 15,
            "Low": 5
        }.get(str(row["urgency"]).strip().title(), 0)

        if str(row["overdue"]).strip().lower() == "yes":
            score += 20

        score += {
            "High": 25,
            "Medium": 15,
            "Low": 5
        }.get(str(row["safety_impact"]).strip().title(), 0)

        return score

    maintenance_df = maintenance_df.copy()
    blocks_df = blocks_df.copy()
    trains_df = trains_df.copy()

    maintenance_df["priority_score"] = maintenance_df.apply(
        calculate_priority,
        axis=1
    )

    # ---------------------------------------------------------
    # Convert HH:MM to minutes
    # ---------------------------------------------------------

    def time_to_minutes(time_string):

        hours, minutes = map(
            int,
            str(time_string).strip().split(":")
        )

        return hours * 60 + minutes

    # ---------------------------------------------------------
    # Check train conflict
    # ---------------------------------------------------------

    def has_train_conflict(block, corridor):

        block_start = time_to_minutes(block["start_time"])
        block_end = time_to_minutes(block["end_time"])

        corridor_trains = trains_df[
            trains_df["corridor"].astype(str).str.strip()
            == str(corridor).strip()
        ]

        for _, train in corridor_trains.iterrows():

            train_start = time_to_minutes(train["start_time"])
            train_end = time_to_minutes(train["end_time"])

            # True overlap only
            if block_start < train_end and block_end > train_start:
                return True

        return False

    # ---------------------------------------------------------
    # Find feasible task-block combinations
    # ---------------------------------------------------------

    feasible_pairs = []

    for task_index, task in maintenance_df.iterrows():

        task_corridor = str(task["corridor"]).strip()
        task_duration = float(task["duration_hours"])

        for block_index, block in blocks_df.iterrows():

            block_corridor = str(block["corridor"]).strip()

            # 1. Corridor must match
            if task_corridor != block_corridor:
                continue

            # 2. Block must be available
            if str(block["available"]).strip().lower() != "yes":
                continue

            block_start = time_to_minutes(block["start_time"])
            block_end = time_to_minutes(block["end_time"])

            block_duration = (block_end - block_start) / 60

            # 3. Block must be long enough
            if block_duration < task_duration:
                continue

            # 4. Block must not conflict with trains
            if has_train_conflict(block, task_corridor):
                continue

            feasible_pairs.append(
                (task_index, block_index)
            )

    # ---------------------------------------------------------
    # OR-Tools model
    # ---------------------------------------------------------

    model = cp_model.CpModel()

    variables = {}

    for task_index, block_index in feasible_pairs:

        variables[(task_index, block_index)] = model.NewBoolVar(
            f"x_{task_index}_{block_index}"
        )

    # ---------------------------------------------------------
    # Each task can use maximum one block
    # ---------------------------------------------------------

    for task_index in maintenance_df.index:

        task_variables = [
            variable
            for (t, b), variable in variables.items()
            if t == task_index
        ]

        if task_variables:
            model.Add(
                sum(task_variables) <= 1
            )

    # ---------------------------------------------------------
    # Each block can be used maximum once
    # ---------------------------------------------------------

    for block_index in blocks_df.index:

        block_variables = [
            variable
            for (t, b), variable in variables.items()
            if b == block_index
        ]

        if block_variables:
            model.Add(
                sum(block_variables) <= 1
            )

    # ---------------------------------------------------------
    # Objective
    #
    # Maximize priority first.
    # Also slightly prefer higher-priority tasks.
    # ---------------------------------------------------------

    objective = []

    for (task_index, block_index), variable in variables.items():

        priority = int(
            maintenance_df.loc[
                task_index,
                "priority_score"
            ]
        )

        objective.append(
            priority * variable
        )

    if objective:

        model.Maximize(
            sum(objective)
        )

    # ---------------------------------------------------------
    # Solve
    # ---------------------------------------------------------

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    # ---------------------------------------------------------
    # Create result
    # ---------------------------------------------------------

    results = []

    if status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ]:

        for (task_index, block_index), variable in variables.items():

            if solver.Value(variable) == 1:

                task = maintenance_df.loc[task_index]
                block = blocks_df.loc[block_index]

                results.append({

                    "Task ID":
                        task["task_id"],

                    "Department":
                        task["department"],

                    "Asset":
                        task["asset_type"],

                    "Location":
                        task["location"],

                    "Corridor":
                        task["corridor"],

                    "Priority":
                        task["priority_score"],

                    "Duration (hrs)":
                        task["duration_hours"],

                    "Block ID":
                        block["block_id"],

                    "Block Start":
                        block["start_time"],

                    "Block End":
                        block["end_time"],

                    "Status":
                        "Optimally Assigned"
                })

    return pd.DataFrame(results)