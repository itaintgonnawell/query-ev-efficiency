import requests
import urllib3, urllib
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_spec(id:int|list[int]):
    ua_string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'

    id_str = ''
    id_len = 0
    if isinstance(id, list):
        id_str = '&id='.join([str(i) for i in id])
        id_len = len(id)
    elif isinstance(id, int):
        id_str = str(id)
        id_len = 1
    url = f"https://www.fueleconomy.gov/feg/Find.do?action=sbs&id={id_str}"

    response = requests.get(url, verify=False, headers={'User-Agent': ua_string})
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table inside the div with id 'tab4'
        table = soup.find('div', id='tab4').find('table')
        if not table:
            return {"error": "No data table found"}
        else:
            # Extract table rows, first level rows only
            rows = table.find_all('tr')

            data = []
            for i in range(id_len):
                # add empty dict for each id
                data.append(dict())

            for row in rows:
                # Each row has two columns: label(th) and value(td)
                headers = [td.get_text(strip=True) for td in row.find_all(['th', 'td'])]
                if len(headers) >= 2:
                    # check if header[0] is empty or null string, skip it
                    if not headers[0] or headers[0].strip() == '':
                        continue

                    for i in range(len(headers)-1):
                        if i < id_len:
                            data[i][headers[0]] = headers[i+1]
            return data


def add_spec_data(data:list[dict]) -> list[dict]:
    id_list = []
    for car in data:
        if 'ID' in car:
            id_list.append(car['ID'])

    # there is size limit on id_list upto 4, so split into chunks of 4
    spec_data = []
    if len(id_list) > 4:
        for i in range(0, len(id_list), 4):
            chunk = id_list[i:i+4]
            spec_data.extend(get_spec(chunk))
    else:
        spec_data = get_spec(id_list)

    # merge spec_data into data based on ID
    for i, car in enumerate(data):
        car.update(spec_data[i])

    return data


if __name__ == "__main__":
    data = get_spec([44092, 48367])
    print(data)