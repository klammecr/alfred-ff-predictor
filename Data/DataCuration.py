# Trim data centered aroun the current year (truth) and keep x years of history. Default 3 years of history
from types import prepare_class


def TrimData(data, year, history = 3):
    keep_years = set(range(year-3, year+1))
    all_years = set(data.keys())
    all_years = {int(i) for i in all_years}
    del_years = all_years - keep_years
    for del_year in del_years:
        del data[str(del_year)]
    return data