"""Synthetic business attributes for the Olist dataset.

Olist ships anonymized: no customer, seller or product names. This script generates stable,
unique, semi-realistic ones so the model is readable. Every value here is FICTIONAL — say so in the
write-up. Deterministic: same input CSVs -> same names, so re-running never reshuffles a dimension.

Usage:  python generate_synthetic_names.py <raw_csv_dir> <out_dir>
Writes: synthetic_customer_names.csv, synthetic_seller_names.csv, synthetic_product_names.csv
"""
import csv, hashlib, random, sys
from collections import Counter, defaultdict
from pathlib import Path

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

def rng_for(key: str) -> random.Random:
    """A generator seeded by the business key itself, so a name never depends on row order."""
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))

def read(name):
    with open(RAW / f"{name}.csv", encoding="utf-8-sig", newline="") as fh:   # the translation file has a BOM
        return list(csv.DictReader(fh))

def unique(key, make, seen):
    r = rng_for(key)
    for _ in range(50):
        v = make(r)
        if v not in seen:
            seen.add(v); return v
    raise RuntimeError(f"could not make a unique value for {key}")

# ---------- people ----------
FEMALE = """Ana Maria Juliana Mariana Fernanda Patrícia Aline Camila Amanda Bruna Jéssica Letícia Júlia
Luana Gabriela Vanessa Beatriz Larissa Carolina Renata Adriana Daniela Tatiane Priscila Natália Rafaela
Débora Cláudia Simone Luciana Sandra Márcia Raquel Isabela Lorena Bianca Thaís Viviane Aparecida
Francisca Antônia Rosângela Eliane Cristiane Helena Alice Laura Manuela Sofia Valentina Heloísa Lívia
Cecília Yasmin Giovanna Mirella Emanuelly Luíza Clara Rebeca Elaine Sueli Vera Lúcia Tânia Kátia""".split()
MALE = """José João Antônio Francisco Carlos Paulo Pedro Lucas Luiz Marcos Luís Gabriel Rafael Daniel
Marcelo Bruno Eduardo Felipe Raimundo Rodrigo Manoel Mateus André Fernando Fábio Leonardo Gustavo
Guilherme Leandro Tiago Anderson Ricardo Márcio Jorge Sebastião Alexandre Roberto Edson Diego Vitor
Sérgio Cláudio Matheus Thiago Geraldo Adriano Luciano Júlio Renato Alex Vinícius Rogério Samuel
Ronaldo Mário Flávio Heitor Arthur Bernardo Davi Enzo Miguel Otávio Caio Igor Wesley Emerson Wagner""".split()
SURNAMES = """Silva Santos Oliveira Souza Rodrigues Ferreira Alves Pereira Lima Gomes Costa Ribeiro Martins
Carvalho Almeida Lopes Soares Fernandes Vieira Barbosa Rocha Dias Nascimento Andrade Moreira Nunes
Marques Machado Mendes Freitas Cardoso Ramos Gonçalves Santana Teixeira Araújo Pinto Moura Cavalcanti
Monteiro Correia Batista Campos Castro Farias Rezende Azevedo Brito Duarte Moraes Sampaio Pires Reis
Melo Cunha Xavier Tavares Macedo Borges Queiroz Siqueira Aguiar Barros Coelho Leite Peixoto Fonseca
Guimarães Medeiros Magalhães Bezerra Figueiredo Nogueira Pacheco Brandão Vasconcelos Porto Paiva""".split()

# ---------- category vocab (English product nouns, keyed by silver's category_en) ----------
NOUNS = {
 "bed_bath_table": ["Bath Towel Set","Duvet Cover","Fitted Sheet Set","Pillowcase Pair","Table Runner","Bath Mat","Quilt","Tablecloth"],
 "sports_leisure": ["Yoga Mat","Resistance Band Kit","Cycling Gloves","Soccer Ball","Dumbbell Pair","Jump Rope","Camping Lantern","Swim Goggles"],
 "furniture_decor": ["Wall Mirror","Floating Shelf","Decorative Vase","Photo Frame","Table Lamp","Wall Clock","Throw Pillow","Candle Holder"],
 "health_beauty": ["Facial Serum","Hair Dryer","Moisturizing Cream","Hair Straightener","Makeup Brush Set","Sunscreen SPF 50","Shampoo","Nail Kit"],
 "housewares": ["Food Container Set","Knife Block","Cutting Board","Dish Rack","Thermos Bottle","Spice Rack","Cookware Set","Storage Basket"],
 "auto": ["Car Seat Cover","Phone Mount","Floor Mat Set","Steering Wheel Cover","Tire Inflator","LED Headlight Kit","Car Charger","Dash Cam"],
 "computers_accessories": ["Wireless Mouse","Mechanical Keyboard","USB Hub","Laptop Stand","HDMI Cable","External SSD","Webcam","Mouse Pad"],
 "toys": ["Building Blocks","Plush Bear","Puzzle 500 pc","Remote Control Car","Doll House","Board Game","Toy Kitchen","Action Figure"],
 "watches_gifts": ["Analog Watch","Smartwatch","Gift Box","Chronograph Watch","Keychain","Jewelry Box","Digital Watch","Pocket Watch"],
 "telephony": ["Phone Case","Screen Protector","Wireless Earbuds","Power Bank","Charging Cable","Selfie Stick","Car Phone Holder","Fast Charger"],
 "baby": ["Baby Stroller","Crib Mobile","Baby Carrier","Bottle Set","Changing Pad","Baby Monitor","Teether","Bath Seat"],
 "perfumery": ["Eau de Parfum","Eau de Toilette","Body Splash","Perfume Gift Set","Deodorant","Cologne"],
 "stationery": ["Notebook","Gel Pen Set","Planner","Colored Pencils","Sticky Notes","Desk Organizer","Backpack","Pencil Case"],
 "fashion_bags_accessories": ["Leather Handbag","Crossbody Bag","Wallet","Belt","Sunglasses","Tote Bag","Backpack","Scarf"],
 "cool_stuff": ["Novelty Mug","LED Night Light","Mini Fan","Bluetooth Speaker","Gadget Kit","Collectible Figure"],
 "garden_tools": ["Garden Hose","Pruning Shears","Planter Pot","Watering Can","Garden Glove Set","Lawn Sprinkler","Shovel"],
 "pet_shop": ["Dog Bed","Cat Scratcher","Pet Feeder","Dog Leash","Cat Litter Box","Pet Carrier","Chew Toy"],
 "electronics": ["Bluetooth Speaker","Universal Remote","Headphones","Portable Radio","Batteries 8 pk","Extension Cord"],
 "consoles_games": ["Game Controller","Video Game","Charging Dock","Gaming Headset","Console Skin"],
 "office_furniture": ["Office Chair","Desk","Filing Cabinet","Bookcase","Monitor Stand","Footrest"],
 "musical_instruments": ["Acoustic Guitar","Guitar Strings","Keyboard Stand","Ukulele","Drumsticks","Microphone","Capo"],
 "books_general_interest": ["Novel","Cookbook","Biography","Self-Help Book","Travel Guide"],
 "books_technical": ["Programming Handbook","Engineering Textbook","Accounting Manual","Medical Reference"],
 "books_imported": ["Imported Novel","Imported Art Book"],
 "food_drink": ["Coffee Beans 1 kg","Gourmet Chocolate","Olive Oil","Tea Assortment"],
 "food": ["Granola","Honey Jar","Snack Box","Protein Bar Pack"], "drinks": ["Craft Beer Pack","Wine Bottle","Cachaça","Juice Box Pack"],
 "unknown": ["Assorted Item","General Merchandise","Multi-Use Item"],
}
DEFAULT_NOUNS = ["Kit","Set","Accessory","Model","Unit","Pack"]
ADJ = ["Premium","Classic","Compact","Deluxe","Essential","Pro","Eco","Plus","Max","Slim","Home","Urban","Tropical","Nordic"]
COLORS = ["Black","White","Navy","Gray","Red","Blue","Green","Beige","Rose","Silver","Brown","Yellow"]
BRANDS = ["Casa Viva","Brisa","Ipê","Aurora","Solaris","Tupã","Jangada","Bossa","Carioca","Mandacaru","Serra Azul",
          "Paraty","Guaraná","Pampa","Araucária","Coqueiro","Itapuã","Lume","Vento Sul","Cerrado","Maré","Bahia Bela",
          "Oca","Juriti","Sabiá","Pitanga","Caju","Ypê Verde","Cristal","Andorinha"]

def category_title(cat):
    return cat.replace("_", " ").title()

# ---------- seller business words by category ----------
BIZ = {"bed_bath_table":"Cama Mesa e Banho","furniture_decor":"Decorações","health_beauty":"Cosméticos",
       "sports_leisure":"Esportes","housewares":"Utilidades","auto":"Autopeças","computers_accessories":"Informática",
       "toys":"Brinquedos","watches_gifts":"Relógios e Presentes","telephony":"Celulares","baby":"Bebê",
       "perfumery":"Perfumaria","stationery":"Papelaria","fashion_bags_accessories":"Bolsas e Acessórios",
       "garden_tools":"Jardinagem","pet_shop":"Pet Shop","electronics":"Eletrônicos","musical_instruments":"Música"}
SUFFIX = ["Ltda","ME","EIRELI","Comércio Ltda",""]

# ---------- build ----------
cust = read("olist_customers_dataset")
seen = set(); rows = []
for uid in sorted({r["customer_unique_id"] for r in cust}):
    def make(r):
        first = r.choice(FEMALE if r.random() < 0.5 else MALE)
        return f"{first} {r.choice(SURNAMES)} {r.choice(SURNAMES)}"
    rows.append((uid, unique(uid, make, seen)))
with open(OUT / "synthetic_customer_names.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["customer_unique_id", "customer_name"]); w.writerows(rows)
print("customers:", len(rows))

trans = {r["product_category_name"]: r["product_category_name_english"] for r in read("product_category_name_translation")}
prods = read("olist_products_dataset")
cat_of = {p["product_id"]: trans.get(p["product_category_name"]) or p["product_category_name"] or "unknown" for p in prods}

seller_cats = defaultdict(Counter)
for li in read("olist_order_items_dataset"):
    seller_cats[li["seller_id"]][cat_of.get(li["product_id"], "unknown")] += 1

seen = set(); rows = []
for s in sorted(r["seller_id"] for r in read("olist_sellers_dataset")):
    top = seller_cats[s].most_common(1)[0][0] if seller_cats[s] else "unknown"
    def make(r, top=top):
        biz = BIZ.get(top, r.choice(["Comércio","Distribuidora","Variedades","Store","Shop","Center"]))
        pattern = r.randrange(4)
        if pattern == 0: name = f"{r.choice(SURNAMES)} {biz}"
        elif pattern == 1: name = f"Loja {r.choice(BRANDS)} {biz}"
        elif pattern == 2: name = f"{r.choice(SURNAMES)} & {r.choice(SURNAMES)} {biz}"
        else: name = f"{r.choice(BRANDS)} {biz}"
        return f"{name} {r.choice(SUFFIX)}".strip()
    rows.append((s, unique(s, make, seen)))
with open(OUT / "synthetic_seller_names.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["seller_id", "seller_name"]); w.writerows(rows)
print("sellers:", len(rows))

seen = set(); rows = []
for p in sorted(prods, key=lambda p: p["product_id"]):
    pid, cat = p["product_id"], cat_of[p["product_id"]]
    def make(r, cat=cat):
        noun = r.choice(NOUNS.get(cat, [f"{category_title(cat)} {n}" for n in DEFAULT_NOUNS]))
        name = f"{r.choice(BRANDS)} {r.choice(ADJ)} {noun}"
        if r.random() < 0.6: name += f", {r.choice(COLORS)}"
        if r.random() < 0.5: name += f" Ref. {r.randrange(100, 9999)}"
        return name
    rows.append((pid, unique(pid, make, seen)))
with open(OUT / "synthetic_product_names.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["product_id", "product_name"]); w.writerows(rows)
print("products:", len(rows))
