from pandas import DataFrame


def print_frame_stats(df: DataFrame):
    """
    Prints out the calculated stats from generate_frame_stats in a formatted
    and readable way.
    """
    print("== BOOST AND SPEED STATS " + "=" * 52)
    print(df.to_string(index=True))
    print("=" * 60 + "\n")
