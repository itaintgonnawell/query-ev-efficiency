import requests
import urllib3, urllib
from bs4 import BeautifulSoup
from constants import maker_list

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def add_si_eff(data:list[dict]) -> list[dict]:
    for car in data:
        # convert MPGe to km/kWh
        if 'Combined MPGe' in car:
            car['km/kWh'] = round(car['Combined MPGe'] * 0.04775, 3)
        elif 'kWh/100 miles' in car:
            car['km/kWh'] = round(100 * 1.60934 / car['kWh/100 miles'], 3)
    return data


def get_eff(year1:int=2024, year2:int=2025, make:str|list[str]='Hyundai', mclass:str|list[str]='', drive:str|list[str]=''):

    ua_string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'

    make_str = ''
    if isinstance(make, list):
        make_str = '; '.join(make)
        # encode string for URL
    elif isinstance(make, str):
        make_str = make
    make_str = urllib.parse.quote(make_str, safe='/;=')

    if isinstance(mclass, list):
        mclass_str = ','.join(mclass)
    elif isinstance(mclass, str):
        mclass_str = mclass
    mclass_str = urllib.parse.quote(f'={mclass_str}', safe='/,=') if mclass_str else ''

    drive_str = ''
    if isinstance(drive, list):
        drive_str = ', '.join(drive)
    elif isinstance(drive, str):
        drive_str = drive
    drive_str = urllib.parse.quote(drive_str, safe='/,=')

    url = f"https://www.fueleconomy.gov/feg/PowerSearch.do?action=Cars&vtype=Electric&srchtyp=evSelect&rowLimit=200&sortBy=Comb&year1={year1}&year2={year2}&make={make_str}&mclass{mclass_str}&range=&drive={drive_str}"

    response = requests.get(url, verify=False, headers={'User-Agent': ua_string})
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table containing the data - class cars display responsive stickyHeader
        table = soup.find('table', class_='cars display responsive stickyHeader')
        if not table:
            return {"error": "No data table found"}
        else:
            # Extract table rows, first level rows only
            rows = table.find('tbody').find_all('tr', recursive=False)
            data = []
            datarow = dict()
            for i, row in enumerate(rows):
                if i%3 == 0:
                    datarow = dict()
                    headers = [td for td in row.find_all('td')]
                    name_split = headers[0].find('a').get_text(strip=True).split()
                    link_split = headers[0].find('a')['href'].split('id=')
                    if len(name_split) >= 3:
                        datarow['Year'] = int(name_split[0])
                        datarow['Make'] = name_split[1]
                        # if Make has two words, e.g. Automotive CODA or Azure Dynamics
                        if name_split[1] in [make.split()[0] for make in maker_list if len(make.split()) > 1]:
                            datarow['Make'] = ' '.join(name_split[1:3])
                            datarow['Model'] = ' '.join(name_split[3:])
                        else:
                            datarow['Model'] = ' '.join(name_split[2:])
                    else:
                        datarow['Model'] = headers[0]
                    if len(link_split) >= 2:
                        datarow['ID'] = int(link_split[1])
                    datarow['Config'] = headers[0].find('span', class_='config').get_text(strip=True)
                elif i%3 == 1:
                    # 2nd row has a table of 3 rows and columns: 
                    # 1st row contains class mpg-comb for combined MPGe
                    # 2nd row contains city / highway MPGe columns
                    # 3rd row contains kWh/100 miles columns
                    sub_table = row.find('table', class_='ev')
                    if sub_table:
                        sub_rows = sub_table.find_all('tr')
                        for i, sub_row in enumerate(sub_rows):
                            if i == 0:
                                sub_data = sub_row.find_all('td')
                                if len(sub_data) >= 2:
                                    datarow['Combined MPGe'] = float(sub_data[1].get_text(strip=True))
                            elif i == 1:
                                sub_data = sub_row.find_all('td')
                                if len(sub_data) >= 2:
                                    datarow['City MPGe'] = float(sub_data[0].get_text(strip=True))
                                    datarow['Highway MPGe'] = float(sub_data[1].get_text(strip=True))
                            elif i == 3:
                                sub_data = sub_row.find_all('td')
                                if len(sub_data) >= 1:
                                    datarow['kWh/100 miles'] = float(sub_data[0].get_text(strip=True).replace('kWh/100 mi', '').strip())
                elif i%3 == 2:
                    totalrange_split = row.find('div', class_='totalRange').get_text(strip=True).split()
                    if len(totalrange_split) > 0:
                        datarow['Total Range'] = float(totalrange_split[0].strip())
                    data.append(datarow)

            return data
    else:
        return {"error": "Failed to retrieve data", "status_code": response.status_code}
    



if __name__ == "__main__":
    data = add_si_eff(get_eff())

    from get_spec import add_spec_data
    data = add_spec_data(data)

    for car in data:
        print([car['Model'], car['Drive'], car['km/kWh']])