def trim_data(data, year, history = 3):
    """Trim the data to a certain number of years

    Args:
        data (dict): The data to trim
        year (int): The end year
        history (int, optional): Number of years to keep from the past. Defaults to 3.

    Returns:
        dict: The trimmed data
    """
    keep_years = set(range(year - history, year+1))
    all_years = set(data.keys())
    all_years = {int(i) for i in all_years if i.isnumeric()}
    del_years = all_years - keep_years
    for del_year in del_years:
        del data[str(del_year)]
    return data