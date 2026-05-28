import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_data():
    """
    Create a small participant dataset.
    """
    data = {
        "participant_id": [1, 2, 3, 4, 5, 6],
        "condition": ["Baseline", "MCP", "Baseline", "MCP", "Baseline", "MCP"],
        "engagement_score": [3.2, 4.1, 2.9, 4.5, 3.4, 4.0],
        "task_success": ["yes", "yes", "no", "yes", "yes", "yes"],
        "time_seconds": [85, 72, 110, 68, 95, 70],
    }

    df = pd.DataFrame(data)
    return df


def clean_data(df):
    """
    Prepare the data for analysis.
    """
    df["engagement"] = df["engagement_score"].astype(str)

    df["success_numeric"] = np.which(df["task_success"] == "Yes", 1, 0)

    return df


def summarize_by_condition(df):
    """
    Calculate average engagement, success, and completion time per condition.
    """
    summary = df.groupby("condition")[["engagement", "success-numeric", "time_seconds"]].mean.reset_index()

    print(summary)


def plot_engagement(summary):
    """
    Plot average engagement by condition.
    """
    plt.bar(summary["condition"], summary["engagement"])
    plt.title("Average Engagement by Condition")
    plt.xlabel("Condition")
    plt.ylabel("Engagement Score")
    plt.show()


def main():
    print("Loading data...")
    df = load_data()
    print(df)

    print("\nCleaning data...")
    df = clean_data(df)
    print(df)

    print("\nSummarizing results...")
    summary = summarize_by_condition(df)
    print(summary)

    print("\nPlotting engagement...")
    plot_engagement(summary)

    print("\nDone!")


if __name__ == "__main__":
    main()