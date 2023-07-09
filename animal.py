import requests
from bs4 import BeautifulSoup

def get_adoptable_animals():
    url = 'https://www.animal.go.kr/front/awtis/public/publicList.do?menuNo=1000000055'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    animals = []
    table = soup.find('table', {'class': 'list'})
    if table:
        rows = table.find_all('tr')
        for row in rows[1:]:
            columns = row.find_all('td')
            animal = {
                'no': columns[0].text.strip(),
                'name': columns[1].text.strip(),
                'species': columns[2].text.strip(),
                'gender': columns[3].text.strip(),
                'age': columns[4].text.strip(),
                'location': columns[5].text.strip(),
                'contact': columns[6].text.strip()
            }
            animals.append(animal)
    
    return animals

# 유기동물 리스트 가져오기
animal_list = get_adoptable_animals()

# 결과 출력
for animal in animal_list:
    print(f"번호: {animal['no']}")
    print(f"이름: {animal['name']}")
    print(f"종: {animal['species']}")
    print(f"성별: {animal['gender']}")
    print(f"나이: {animal['age']}")
    print(f"보호장소: {animal['location']}")
    print(f"연락처: {animal['contact']}")
    print()
