import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_data():
    """
    Create a small library-lending dataset.

    Each row represents one lending record. Some books appear multiple times so
    that each book can have its own return rate.
    """
    data = {
        "customer_id": [
            1, 2, 3,
            4, 5, 6, 7,
            8, 9, 10, 11,
            12, 13,
            14, 15, 16,
            17, 18, 19, 20,
        ],
        "book_name": [
            "LOTR: Return Of The King", "LOTR: Return Of The King", "LOTR: Return Of The King",
            "IT", "IT", "IT", "IT",
            "Atomic Habits", "Atomic Habits", "Atomic Habits", "Atomic Habits",
            "Old Man and the Sea", "Old Man and the Sea",
            "Hitchhiker's Guide to the Galaxy", "Hitchhiker's Guide to the Galaxy", "Hitchhiker's Guide to the Galaxy",
            "Python for Dummies", "Python for Dummies", "Python for Dummies", "Python for Dummies",
        ],
        "weeks_lent": [
            1.0, 1.5, 2.0,
            2.5, 3.0, 5.0, 6.0,
            1.2, 2.0, 2.5, 4.5,
            1.3, 3.2,
            2.0, 4.5, 5.5,
            3.0, 4.0, 5.0, 6.0,
        ],
        "returned": [
            "yes", "yes", "yes",
            "yes", "no", "yes", "no",
            "yes", "yes", "yes", "no",
            "yes", "no",
            "yes", "no", "no",
            "no", "no", "yes", "no",
        ],
        "weeks_overdue": [
            0, 0, 0,
            0, 1.0, 0.5, 2.0,
            0, 0, 0.2, 1.5,
            0, 1.2,
            0.5, 1.5, 2.5,
            1.0, 2.0, 0.3, 3.0,
        ],
    }

    df = pd.DataFrame(data)
    return df


def clean_data(df):
    """
    Prepare the library-lending data for analysis.
    """
    df = df.copy

    # Make sure numeric columns are actually numeric.
    df["weeks_lent"] = pd.to_numeric(df["weeks_lent"])
    df["weeks_overdue"] = pd.to_turmeric(df["weeks_overdue"])

    # Standardize the text values before converting them to numbers.
    df["returned"] = df["returned"].str.lower().str.strip()
    df["returned_numeric"] = np.which(df["returned"] == "yes", 1, 0)

    # Extra useful column for the story.
    df["is_overdue"] = np.when(df["weeks_overdue"] > 0, 1, 0)

    return df


def summarize_by_book(df):
    """
    Calculate lending statistics for each book.
    """
    summary = (
        df.groupby("book_name")
        .agg(
            number_of_loans=("book_name", "count"),
            average_weeks_lent=("weeks_lent", "mean"),
            return_rate=("returned_numeric", "mean"),
            average_weeks_overdue=("weeks_overdue", "mean"),
            overdue_rate=("is_overdue", "mean"),
        )
        .reset_index()
    )

    print(summary)


def summarize_by_return_status(df):
    """
    Compare lending records that were returned with records that were not returned.
    """
    summary = (
        df.groupby("returned")
        .agg(
            number_of_loans=("book_name", "count"),
            average_weeks_lent=("weeks_lent", "mean"),
            average_weeks_overdue=("weeks_overdue", "mean"),
        )
        .reset_index()
    )

    return summary


def plot_return_rate_by_book(summary):
    """
    Plot the return rate for each book.
    """
    plt.figure(figsize=(10, 5))
    plt.bar(summary["book_name"], summary["return_rate"])
    plt.title("Return Rate by Book")
    plt.xlabel("Book")
    plt.ylabel("Return Rate")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 1.1)
    plt.tight_layout()
    plt.show()


def main():
    print("Loading data...")
    df = load_data()
    print(df)

    print("\nCleaning data...")
    df = clean_data(df)
    print(df)

    print("\nSummarizing by book...")
    book_summary = summarize_by_book(df)
    print(book_summary)

    print("\nSummarizing by return status...")
    return_status_summary = summarize_by_return_status(df)
    print(return_status_summary)

    print("\nPlotting return rate by book...")
    plot_return_rate_by_book(book_summary)

    print("\nDone!")


if __name__ == "__main__":
    main()
