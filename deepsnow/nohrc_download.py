import requests
import os

years = [year for year in range(2002, 2019)]

# stations = ['KADS', 'KAPA', 'KAPF', 'KATT', 'KAUS', 'KBFI', 'WA-KG-68'
#             'KBJC', 'KBKF', 'KBKL', 'KBTV', 'KCHD', 'KCPS', 'KDAL', 'KDLL', 
#             'KEUG', 'KFNL', 'KGOP', 'KLOM', 'KMKT', 'KMSP', 'KFCM', 'SPTM5'
#             'KMSN', 'KNFW', 'KNUQ', 'KPAE', 'KPAO', 'KPUB', 'KRDU', 'KRHV', 
#             'KRNM', 'KRNT', 'KSAT', 'KTLH', 'KWVI', 'PHNL', 'PHOG']

stations = ['KADS']

plot_numbers = [num for num in range(1,9)]

for station_ in stations: 
    for year_ in years: 
        print(station_, year_)
        for file_ in plot_numbers:
            try: 
                directory = '../data/{}/{}/'.format(station_, year_)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                url = 'https://www.nohrsc.noaa.gov/interactive/html/graph.html?station={}&w=600&h=400&o=a&uc=0&by={}&bm=1&bd=1&bh=0&ey={}&em=1&ed=1&eh=0&data={}&units=0&region=us'.format(station_, year_, year_+1, file_+10)
                r = requests.get(url)
                with open(directory + 'plot_{}_new.csv'.format(file_), 'wb') as f:
                    f.write(r.content)
            except:
                print('Error occurred.')
                pass