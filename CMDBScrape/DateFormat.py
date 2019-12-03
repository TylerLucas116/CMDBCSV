def date_format(date):
    truncated_date = date[:10]
    delim = '-'
    split_date = truncated_date.split(delim)
    format_date = split_date[1] + "/" + split_date[2] + "/" + split_date[0]
    return format_date
    