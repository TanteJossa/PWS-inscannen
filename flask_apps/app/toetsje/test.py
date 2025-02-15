import requests
import os
import json
from PIL import Image, ImageFile
from io import BytesIO
import base64
from multiprocessing.pool import ThreadPool

ImageFile.LOAD_TRUNCATED_IMAGES = True


contexts = {
        "1": "Geen context toepasselijk",
        "2": "De reactievergelijking voor dit experiment is: 14 KMnO4 (s) + 4 C3H8O3 (l) → 14 MnO2 (s) + 14 KOH (aq) + 12 CO2 (g) + 8 H2O (l)",
        "3": "Ze mengden voorzichtig wat paarse kaliumpermanganaatkristallen met enkele druppels kleurloze glycerine in een schaaltje. Plotseling begon het mengsel te sissen en te borrelen. Een dikke, grijze rookwolk steeg op, gevolgd door een felle vlam. De hitte was zo intens dat ze een stap achteruit moesten doen. 'Voel je die warmte?' vroeg Lisa verbaasd. 'Het is alsof we naast een kampvuur staan!' Het vuur doofde snel, maar de warmte bleef hangen.",
        "4": "Magnesium (4p): Magnesiumlint is gemaakt van magnesium. Magnesium is goed brandbaar. Tijdens de verbranding van magnesium ontstaat er een witte as, MgO.",
        "5": "Trichloormethaan (TCM), staat ook bekend als chloroform. In films zie je vaak de anesthetische kant van dit molecuul. Het inademen van TCM kan brandwonden veroorzaken. Scheikundig gezien is het een eenvoudige alkaan met de molecuulformule CHCl3",
        "6": "Glazen & waxinelichtjes (4p) Deze vragen sluiten aan bij het practicum, beschreven in de bijlage. Neem aan dat de formule voor kaarsvet C25H52 is. Practicum Glazen & Waxinelichtjes. Het maken van dit practicum is niet nodig voor het beantwoorden van de vragen. Bij tijdnood kun je ervoor kiezen om het practicum over te slaan en direct door te gaan naar de vragen.Materialen:2 waxinelichtjes,lucifer/aansteker, 50 mL bekerglas, 200 mL bekerglas, Werkwijze: Zorg ervoor dat er aan de gebruikelijke veiligheidsvoorschriften gehouden worden; denk hierbij aan een labjas en veiligheidsbril.Zorg ervoor dat er niets licht-ontvlambaars in je directe omgeving is, behalve de lont van het waxinelichtje. Steek beide waxinelichtjes aan.Wacht ongeveer 10 seconden.Plaats de bekerglazen tegelijkertijd over de waxinelichtjes. Noteer welk waxinelichtje het kortste brandde",
        "7": "Glazen & waxinelichtjes (4p) Deze vragen sluiten aan bij het practicum, beschreven in de bijlage. Neem aan dat de formule voor kaarsvet C25H52 is. Practicum Glazen & Waxinelichtjes. Het maken van dit practicum is niet nodig voor het beantwoorden van de vragen. Bij tijdnood kun je ervoor kiezen om het practicum over te slaan en direct door te gaan naar de vragen.Materialen:2 waxinelichtjes,lucifer/aansteker, 50 mL bekerglas, 200 mL bekerglas, Werkwijze: Zorg ervoor dat er aan de gebruikelijke veiligheidsvoorschriften gehouden worden; denk hierbij aan een labjas en veiligheidsbril.Zorg ervoor dat er niets licht-ontvlambaars in je directe omgeving is, behalve de lont van het waxinelichtje. Steek beide waxinelichtjes aan.Wacht ongeveer 10 seconden.Plaats de bekerglazen tegelijkertijd over de waxinelichtjes. Noteer welk waxinelichtje het kortste brandde"
}

questions =  {
    "1": "Noteer 'A' als antwoord op vraag 1.",
    "2": "Is er hier sprake van een verbranding? Kijk zorgvuldig naar de reactievergelijking. Beargumenteer je antwoord.",
    "3": "Is er hier sprake van een exotherme of endotherme reactie? Beargumenteer je antwoord.",
    "4": "Geef de reactievergelijking van de verbranding van het magnesiumlint. Benoem tevens de fases. Ga uit van een volledige verbranding.",
    "5": "Geef een tekening van het molecuul TCM. Zorg ervoor dat elk atoom aan zijn covalentie voldoet. Kras niet in de tekening. Bij correctie, teken opnieuw.",
    "6": "In het practicum zag je dat één waxinelichtje langer brandde. Geef aan welk waxinelichtje dit is, gebruik met het kleinere/grotere bekerglas als aanduiding. Beargumenteer waarom dit het geval is.",
    "7": "Philip wil graag het experiment herhalen, alleen gebruikt hij een ander merk waxinelichtjes. Deze waxinelichtjes hebben een grotere lont. Door deze grotere lont wordt er meer kaarsvet per tijdseenheid verbrand.Voorspel wat er zal gebeuren met de brandingsduur van Philips waxinelichtjes ten opzichte van eerdere waxinelichtje. Ga uit van dezelfde omstandigheden. Beargumenteer je antwoord."
}

rubrics = {
        "1": ["1p: er is een versie genoteerd"],
        "2": [
        "1p: er is geen zuurstof(gas) voor de pijl/er is geen zuurstof(gas) als reactant betrokken",
        "1p: consequente conclusie op basis van argumentatie"
        ],
        "3": [
        "1p: Je neemt waar dat er een vorm van energie vrijkomt, zoals warmte/vuur/licht",
        "1p: Consequente conclusie op basis van argumentatie, zoals bijvoorbeeld er komt energie vrij, dus exotherme reactie. Of er is foutief genoemd dat er energie in de reactie gaat, maar wel consequent geconcludeert dat er sprake is van een endotherme reactie."
        ],
        "4": [
        "1p: alle moleculen correct benoemd (Mg, O₂, MgO)",
        "1p: reactievergelijking is correct gebalanceerd (coëfficiënten) en de correcte moleculen zijn benoemd (zie punt 1)",
        "1p: alle fases correct benoemd"
        ],
        "5": [
        "1p: 3 Cl atomen en 1 C atoom en 1 H atoom", 
        "1p: alle atomen voldoen aan hun covalenties"],
        "6": [
        "1p: er is meer zuurstof bij het grotere bekerglas",
        "1p: een conclusie waarbij de brandingsduur gekoppeld is aan de hoeveelheid zuurstof in het bekerglas. Mocht de leerling foutief hebben genoemd dat in het kleinere bekerglas meer zuurstof zit, dan kan dit punt wel toegekend worden als er een consequente conclusie wordt getrokken."
        ],
        "7": [
        "1p: genoemd dat de hoeveelheid zuurstof voor beide waxinelichtjes hetzelfde is",
        "1p: consequente conclusie, zoals het waxinelichtje met de grotere lont gebruikt meer zuurstof per seconde"
        ]
}

def png_to_base64(file_path, quality=1):
    if not file_path.endswith('.png'):
        raise ValueError("Input file must be a PNG image.")
    if quality != 1:
        # https://platform.openai.com/docs/guides/vision 

        pillow_image = Image.open(file_path)
        
        new_width = int(pillow_image.width * quality)
        new_height = int(float(pillow_image.size[1]) * quality)
        
        resized_image = pillow_image.resize((new_width, new_height))
        buffered = BytesIO()
        resized_image.save(buffered, format="PNG")
        base64_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
    else:
        with open(file_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")
            
    if not base64_string.startswith('data:image'):
        base64_string = "data:image/png;base64," + base64_string
    
    return base64_string #

def process_image(name):
    base64_img = png_to_base64('./output/'+name, 0.5)
    print('starting: '+name)
    try:
        result = requests.post('http://localhost:8080/scan_page', json={
            "Base64Image": base64_img,
            "contexts": contexts,
            "questions": questions,
            "rubrics": rubrics,
        }, headers={
            'Content-Type': 'application/json'
        }) # Adding a timeout to handle potential hanging requests

        if result.ok and (result.json())["output"]:
            print('finished: '+name)
            output = (result.json())["output"]
            del output["cropped_base64"]
            del output["red_pen_base64"]
            return output
        else:
            print('Error '+name+': '+result.text)
            return None  # Return None for failed requests
    except requests.exceptions.RequestException as e:
        print(f'Request Exception for {name}: {e}')
        return None

output = []



# Number of threads in the pool, adjust as needed
num_threads = os.cpu_count()  # A reasonable starting point

with ThreadPool(num_threads) as pool:
    results = pool.map(process_image, os.listdir('./output'))

# Filter out None results (failed requests)
output = [r for r in results if r is not None]
        
with open('output.json', 'w') as f:
    json.dump(output, f)
    
    
