import numpy as np

# function to translate granularity in seconds to 
# appropriate pandas date_range frequency
def granularity_to_freq(granularity):
    days = divmod(granularity, 86400) 
    hours = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)
    if (days[0] >= 1):
        return '{}D'.format(days[0])
    elif (hours[0] >=1):
        return '{}H'.format(hours[0])
    elif (minutes[0] >= 1):
        return '{}T'.format(minutes[0])
    else:
        return '{}S'.format(minutes[1])

def okta_to_percent(x):
    if x == 'CLR':
        return np.random.uniform(0, 12)
    elif x == 'FEW':
        return np.random.uniform(13, 37)
    elif x == 'SCT': 
        return np.random.uniform(38, 62)
    elif x == 'BKN': 
        return np.random.uniform(62, 87)
    elif x == 'OVC': 
        return np.random.uniform(88, 100)
    else: 
        return np.nan 