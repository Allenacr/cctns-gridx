"""
CCTNS-GridX — Tamil Nadu Seed Data Generator
Generates 2500+ realistic FIRs, police stations, crime categories, patrol data,
women safety zones, and accident-prone areas across all 38 Tamil Nadu districts.
"""

import sqlite3
import random
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from security.encryption import hash_password

random.seed(42)

# ═══════════════════════════════════════════════════════════════
# TAMIL NADU DISTRICTS
# ═══════════════════════════════════════════════════════════════
DISTRICTS = [
    {"name": "Chennai", "code": "CHN", "lat": 13.0827, "lng": 80.2707, "population": 7088000, "area": 426, "zone": "North"},
    {"name": "Coimbatore", "code": "CBE", "lat": 11.0168, "lng": 76.9558, "population": 3458000, "area": 4723, "zone": "West"},
    {"name": "Madurai", "code": "MDU", "lat": 9.9252, "lng": 78.1198, "population": 3038000, "area": 3741, "zone": "South"},
    {"name": "Tiruchirappalli", "code": "TRY", "lat": 10.7905, "lng": 78.7047, "population": 2722000, "area": 4403, "zone": "Central"},
    {"name": "Salem", "code": "SLM", "lat": 11.6643, "lng": 78.1460, "population": 3482000, "area": 5245, "zone": "West"},
    {"name": "Tirunelveli", "code": "TNV", "lat": 8.7139, "lng": 77.7567, "population": 3077000, "area": 6823, "zone": "South"},
    {"name": "Erode", "code": "ERD", "lat": 11.3410, "lng": 77.7172, "population": 2252000, "area": 5722, "zone": "West"},
    {"name": "Vellore", "code": "VLR", "lat": 12.9165, "lng": 79.1325, "population": 1614000, "area": 2474, "zone": "North"},
    {"name": "Thoothukudi", "code": "TUT", "lat": 8.7642, "lng": 78.1348, "population": 1750000, "area": 4621, "zone": "South"},
    {"name": "Dindigul", "code": "DGL", "lat": 10.3624, "lng": 77.9695, "population": 2160000, "area": 6058, "zone": "Central"},
    {"name": "Thanjavur", "code": "TNJ", "lat": 10.7870, "lng": 79.1378, "population": 2405000, "area": 3396, "zone": "Central"},
    {"name": "Kanchipuram", "code": "KPM", "lat": 12.8342, "lng": 79.7036, "population": 1166000, "area": 1684, "zone": "North"},
    {"name": "Sivagangai", "code": "SVG", "lat": 10.0441, "lng": 78.4846, "population": 1339000, "area": 4189, "zone": "South"},
    {"name": "Karur", "code": "KRR", "lat": 10.9601, "lng": 78.0766, "population": 1064000, "area": 2895, "zone": "Central"},
    {"name": "Kanyakumari", "code": "KNY", "lat": 8.0883, "lng": 77.5385, "population": 1870000, "area": 1672, "zone": "South"},
    {"name": "Tiruvarur", "code": "TVR", "lat": 10.7713, "lng": 79.6367, "population": 1264000, "area": 2377, "zone": "Central"},
    {"name": "Nagapattinam", "code": "NGP", "lat": 10.7672, "lng": 79.8449, "population": 1616000, "area": 2716, "zone": "Central"},
    {"name": "Cuddalore", "code": "CDL", "lat": 11.7480, "lng": 79.7714, "population": 2605000, "area": 3678, "zone": "North"},
    {"name": "Villupuram", "code": "VPM", "lat": 11.9401, "lng": 79.4861, "population": 2093000, "area": 3725, "zone": "North"},
    {"name": "Tiruvannamalai", "code": "TVM", "lat": 12.2253, "lng": 79.0747, "population": 2464000, "area": 6191, "zone": "North"},
    {"name": "Namakkal", "code": "NMK", "lat": 11.2189, "lng": 78.1674, "population": 1726000, "area": 3363, "zone": "West"},
    {"name": "Dharmapuri", "code": "DPI", "lat": 12.1357, "lng": 78.1602, "population": 1506000, "area": 4498, "zone": "West"},
    {"name": "Krishnagiri", "code": "KGI", "lat": 12.5186, "lng": 78.2137, "population": 1879000, "area": 5143, "zone": "West"},
    {"name": "Ariyalur", "code": "ALR", "lat": 11.1401, "lng": 79.0783, "population": 754000, "area": 1949, "zone": "Central"},
    {"name": "Perambalur", "code": "PMB", "lat": 11.2330, "lng": 78.8809, "population": 565000, "area": 1757, "zone": "Central"},
    {"name": "Pudukkottai", "code": "PDK", "lat": 10.3833, "lng": 78.8001, "population": 1619000, "area": 4651, "zone": "Central"},
    {"name": "Ramanathapuram", "code": "RMD", "lat": 9.3762, "lng": 78.8308, "population": 1337000, "area": 4123, "zone": "South"},
    {"name": "Virudhunagar", "code": "VNR", "lat": 9.5680, "lng": 77.9624, "population": 1943000, "area": 4283, "zone": "South"},
    {"name": "Theni", "code": "TNI", "lat": 10.0104, "lng": 77.4760, "population": 1245000, "area": 2889, "zone": "South"},
    {"name": "Nilgiris", "code": "NLG", "lat": 11.4102, "lng": 76.6950, "population": 735000, "area": 2549, "zone": "West"},
    {"name": "Chengalpattu", "code": "CGP", "lat": 12.6819, "lng": 79.9888, "population": 2557000, "area": 2944, "zone": "North"},
    {"name": "Ranipet", "code": "RPT", "lat": 12.9322, "lng": 79.3213, "population": 1210000, "area": 2535, "zone": "North"},
    {"name": "Tirupattur", "code": "TPR", "lat": 12.4955, "lng": 78.5730, "population": 1111000, "area": 3094, "zone": "North"},
    {"name": "Kallakurichi", "code": "KLK", "lat": 11.7392, "lng": 78.9620, "population": 1370000, "area": 3050, "zone": "North"},
    {"name": "Tenkasi", "code": "TNK", "lat": 8.9604, "lng": 77.3152, "population": 1407000, "area": 2929, "zone": "South"},
    {"name": "Tiruvallur", "code": "TRL", "lat": 13.1428, "lng": 79.9083, "population": 3728000, "area": 3424, "zone": "North"},
    {"name": "Mayiladuthurai", "code": "MYL", "lat": 11.1018, "lng": 79.6491, "population": 918000, "area": 1129, "zone": "Central"},
]

# ═══════════════════════════════════════════════════════════════
# POLICE STATIONS PER DISTRICT
# ═══════════════════════════════════════════════════════════════
STATION_TEMPLATES = {
    "Chennai": [
        ("Adyar PS", "Regular"), ("T. Nagar PS", "Regular"), ("Anna Nagar PS", "Regular"),
        ("Mylapore PS", "Regular"), ("Egmore PS", "Regular"), ("Nungambakkam PS", "Regular"),
        ("Guindy PS", "Regular"), ("Ashok Nagar PS", "Regular"), ("Royapettah PS", "Regular"),
        ("Triplicane PS", "Regular"), ("George Town PS", "Regular"), ("Flower Bazaar PS", "Regular"),
        ("Teynampet PS", "Regular"), ("Kotturpuram PS", "Regular"), ("Besant Nagar PS", "Regular"),
        ("Velachery PS", "Regular"), ("Tambaram PS", "Regular"), ("Chromepet PS", "Regular"),
        ("Perungudi PS", "Regular"), ("Sholinganallur PS", "Regular"),
        ("Anna Nagar All Women PS", "Women"), ("Adyar Cyber PS", "Cyber"),
        ("Chennai Central Railway PS", "Railway"), ("Chennai Traffic PS", "Traffic"),
    ],
    "Coimbatore": [
        ("Saibaba Colony PS", "Regular"), ("RS Puram PS", "Regular"), ("Town Hall PS", "Regular"),
        ("Peelamedu PS", "Regular"), ("Singanallur PS", "Regular"), ("Kuniyamuthur PS", "Regular"),
        ("Sulur PS", "Regular"), ("Gandhipuram PS", "Regular"), ("Race Course PS", "Regular"),
        ("Coimbatore Women PS", "Women"), ("Coimbatore Cyber PS", "Cyber"),
    ],
    "Madurai": [
        ("Tallakulam PS", "Regular"), ("Sellur PS", "Regular"), ("SS Colony PS", "Regular"),
        ("Koodal Nagar PS", "Regular"), ("Thirumangalam PS", "Regular"), ("Melur PS", "Regular"),
        ("Anna Nagar PS", "Regular"), ("Teppakulam PS", "Regular"),
        ("Madurai Women PS", "Women"), ("Madurai Cyber PS", "Cyber"),
    ],
    "Tiruchirappalli": [
        ("Srirangam PS", "Regular"), ("Cantonment PS", "Regular"), ("KK Nagar PS", "Regular"),
        ("Woraiyur PS", "Regular"), ("Thillai Nagar PS", "Regular"), ("Lalgudi PS", "Regular"),
        ("Trichy Women PS", "Women"), ("Trichy Traffic PS", "Traffic"),
    ],
    "Salem": [
        ("Suramangalam PS", "Regular"), ("Ammapet PS", "Regular"), ("Hasthampatti PS", "Regular"),
        ("Omalur PS", "Regular"), ("Attur PS", "Regular"), ("Mettur PS", "Regular"),
        ("Salem Women PS", "Women"),
    ],
}

# Generic station names for districts without specific data
GENERIC_STATIONS = [
    ("Town PS", "Regular"), ("East PS", "Regular"), ("West PS", "Regular"),
    ("North PS", "Regular"), ("South PS", "Regular"), ("Central PS", "Regular"),
    ("Women PS", "Women"), ("Traffic PS", "Traffic"),
]

# ═══════════════════════════════════════════════════════════════
# CRIME CATEGORIES — ALL ACTS FROM PROBLEM STATEMENT
# ═══════════════════════════════════════════════════════════════
CRIME_CATEGORIES = [
    # Indian Penal Code
    ("Indian Penal Code", "121", "Waging war against Government of India", 5, "Anti-National", 1, 0),
    ("Indian Penal Code", "141", "Unlawful assembly", 3, "Public Order", 1, 1),
    ("Indian Penal Code", "144", "Joining unlawful assembly armed with deadly weapon", 3, "Public Order", 1, 0),
    ("Indian Penal Code", "146", "Rioting", 3, "Public Order", 1, 0),
    ("Indian Penal Code", "147", "Punishment for rioting", 3, "Public Order", 1, 1),
    ("Indian Penal Code", "148", "Rioting armed with deadly weapon", 4, "Public Order", 1, 0),
    ("Indian Penal Code", "151", "Knowingly joining or continuing in assembly of five or more persons", 2, "Public Order", 1, 1),
    ("Indian Penal Code", "153-A", "Promoting enmity between groups", 4, "Communal", 1, 0),
    ("Indian Penal Code", "295-A", "Deliberate acts to outrage religious feelings", 4, "Communal", 1, 0),
    ("Indian Penal Code", "268", "Public nuisance", 2, "Public Order", 1, 1),
    ("Indian Penal Code", "302", "Murder", 5, "Violent Crime", 1, 0),
    ("Indian Penal Code", "304-B", "Dowry death", 5, "Violent Crime", 1, 0),
    ("Indian Penal Code", "307", "Attempt to murder", 5, "Violent Crime", 1, 0),
    ("Indian Penal Code", "322", "Voluntarily causing grievous hurt", 4, "Violent Crime", 1, 0),
    ("Indian Penal Code", "324", "Voluntarily causing hurt by dangerous weapon", 4, "Violent Crime", 1, 0),
    ("Indian Penal Code", "351", "Assault", 3, "Violent Crime", 1, 1),
    ("Indian Penal Code", "354", "Assault on woman with intent to outrage modesty", 4, "Crime Against Women", 1, 0),
    ("Indian Penal Code", "509", "Word, gesture or act intended to insult modesty of woman", 3, "Crime Against Women", 1, 1),
    ("Indian Penal Code", "498-A", "Cruelty by husband or relatives", 4, "Crime Against Women", 1, 0),
    ("Indian Penal Code", "363", "Kidnapping", 5, "Kidnapping", 1, 0),
    ("Indian Penal Code", "364", "Kidnapping for ransom", 5, "Kidnapping", 1, 0),
    ("Indian Penal Code", "365", "Kidnapping with intent to secretly confine", 5, "Kidnapping", 1, 0),
    ("Indian Penal Code", "366", "Kidnapping woman to compel marriage", 5, "Crime Against Women", 1, 0),
    ("Indian Penal Code", "376", "Rape", 5, "Crime Against Women", 1, 0),
    ("Indian Penal Code", "379", "Theft", 3, "Property Crime", 1, 1),
    ("Indian Penal Code", "380", "Theft in dwelling house", 3, "Property Crime", 1, 0),
    ("Indian Penal Code", "383", "Extortion", 4, "Property Crime", 1, 0),
    ("Indian Penal Code", "390", "Robbery", 4, "Property Crime", 1, 0),
    ("Indian Penal Code", "391", "Dacoity", 5, "Property Crime", 1, 0),
    ("Indian Penal Code", "392", "Punishment for robbery", 4, "Property Crime", 1, 0),
    ("Indian Penal Code", "395", "Punishment for dacoity", 5, "Property Crime", 1, 0),
    ("Indian Penal Code", "396", "Dacoity with murder", 5, "Property Crime", 1, 0),
    ("Indian Penal Code", "397", "Robbery with attempt to cause death", 5, "Property Crime", 1, 0),
    ("Indian Penal Code", "411", "Dishonestly receiving stolen property", 3, "Property Crime", 1, 0),
    ("Indian Penal Code", "420", "Cheating", 3, "Economic Crime", 1, 1),
    ("Indian Penal Code", "441", "Criminal trespass", 2, "Property Crime", 1, 1),
    ("Indian Penal Code", "442", "House trespass", 3, "Property Crime", 1, 0),
    ("Indian Penal Code", "447", "Punishment for criminal trespass", 2, "Property Crime", 1, 1),
    ("Indian Penal Code", "448", "Punishment for house trespass", 3, "Property Crime", 1, 0),
    ("Indian Penal Code", "454", "Lurking house-trespass in order to commit offence", 4, "Property Crime", 1, 0),
    ("Indian Penal Code", "457", "Lurking house-trespass by night", 4, "Property Crime", 1, 0),
    ("Indian Penal Code", "465", "Forgery", 3, "Economic Crime", 1, 0),
    ("Indian Penal Code", "467", "Forgery of valuable security", 4, "Economic Crime", 1, 0),
    ("Indian Penal Code", "468", "Forgery for purpose of cheating", 4, "Economic Crime", 1, 0),
    ("Indian Penal Code", "470", "Forged document", 3, "Economic Crime", 1, 0),
    ("Indian Penal Code", "471", "Using forged document as genuine", 3, "Economic Crime", 1, 0),
    ("Indian Penal Code", "489-A", "Counterfeiting currency notes", 5, "Economic Crime", 1, 0),
    ("Indian Penal Code", "504", "Intentional insult with intent to provoke breach of peace", 2, "Public Order", 1, 1),
    ("Indian Penal Code", "506", "Criminal intimidation", 3, "Violent Crime", 1, 1),
    # NDPS Act
    ("NDPS Act", "20", "Cannabis-related offences", 4, "Narcotics", 1, 0),
    ("NDPS Act", "21", "Manufactured drugs offences", 5, "Narcotics", 1, 0),
    ("NDPS Act", "22", "Psychotropic substances offences", 5, "Narcotics", 1, 0),
    # Gambling Act
    ("Gambling Act", "13", "Gambling in public place", 2, "Vice Crime", 1, 1),
    # Arms Act
    ("Arms Act", "25", "Possession of arms without licence", 4, "Arms", 1, 0),
    # Excise Act
    ("Excise Act", "60", "Manufacture of liquor without licence", 3, "Excise", 1, 0),
    ("Excise Act", "60(2)", "Sale of illicit liquor", 3, "Excise", 1, 0),
    ("Excise Act", "72", "Possession of contraband liquor", 3, "Excise", 1, 1),
    # Cow Protection Act
    ("Cow Protection Act", "3", "Prohibition of slaughter", 3, "Animal Protection", 1, 0),
    ("Cow Protection Act", "5", "Prohibition of transport", 3, "Animal Protection", 1, 0),
    ("Cow Protection Act", "11", "Penalty for offences", 2, "Animal Protection", 1, 1),
    # SC/ST Act
    ("SC/ST Prevention of Atrocities Act", "3", "Offences of atrocities", 5, "Atrocity", 1, 0),
    # Mineral and Mining Act
    ("Mineral and Mining Act", "4", "Illegal mining", 4, "Mining", 1, 0),
    ("Mineral and Mining Act", "21", "Penalty for contravention", 3, "Mining", 1, 0),
    # Immoral Traffic Prevention Act
    ("Immoral Traffic Prevention Act", "3", "Keeping a brothel", 4, "Vice Crime", 1, 0),
    ("Immoral Traffic Prevention Act", "4", "Living on earnings of prostitution", 4, "Vice Crime", 1, 0),
    ("Immoral Traffic Prevention Act", "5", "Procuring or inducing for prostitution", 5, "Vice Crime", 1, 0),
    # Goonda Act
    ("Goonda Act", "3", "Detention of goondas", 4, "Public Order", 1, 0),
]

# ═══════════════════════════════════════════════════════════════
# SAMPLE DATA FOR FIR GENERATION
# ═══════════════════════════════════════════════════════════════
FIRST_NAMES_MALE = [
    "Rajesh", "Kumar", "Senthil", "Murugan", "Arjun", "Vikram", "Suresh", "Karthik",
    "Manikandan", "Dinesh", "Prakash", "Ramesh", "Anand", "Balaji", "Ganesh",
    "Saravanan", "Vignesh", "Arun", "Mohan", "Sathish", "Ravi", "Selvam",
    "Pandian", "Dhanush", "Ashwin", "Deepak", "Gopal", "Hari", "Jagan", "Kannan",
]
FIRST_NAMES_FEMALE = [
    "Priya", "Lakshmi", "Meena", "Saranya", "Divya", "Kavitha", "Revathi",
    "Sangeetha", "Nithya", "Deepika", "Anjali", "Bhavani", "Chitra", "Devi",
    "Gayathri", "Indira", "Janani", "Kala", "Lavanya", "Madhavi",
]
LAST_NAMES = [
    "Nadar", "Pillai", "Gounder", "Mudaliar", "Thevar", "Chettiar", "Iyer",
    "Iyengar", "Naicker", "Reddiar", "Achari", "Padayachi", "Vanniar", "Kallar",
    "Maravar", "Devar", "Pandiyan", "Pandey", "Raj", "Subramanian",
]

LOCATION_TYPES = [
    "Main Road", "Bus Stand Area", "Market Complex", "Residential Colony",
    "Industrial Area", "Temple Street", "Railway Station Area", "Highway Junction",
    "School Zone", "College Road", "Hospital Road", "Park Area",
    "Shopping Complex", "Bazaar Area", "Lake Side Road",
]

MODUS_OPERANDI = [
    "By breaking the lock of the door", "By snatching from the victim",
    "By threatening with a knife", "Using stolen vehicle",
    "By impersonation", "Online fraud through fake website",
    "By administering intoxicating substance", "By pickpocketing in crowded area",
    "Chain snatching from two-wheeler rider", "By hacking social media account",
    "By fake currency exchange", "Using duplicate key",
    "By creating distraction", "Breaking window glass of parked vehicle",
]

STATUSES = ["Registered", "Under Investigation", "Charge Sheet Filed", "Closed", "Undetected"]


def _random_name(gender="Male"):
    if gender == "Male":
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def _random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _random_time():
    # Crime time distribution — more at night
    weights = [3, 2, 1, 1, 1, 2, 3, 5, 6, 7, 8, 8, 7, 6, 6, 5, 5, 6, 7, 8, 9, 8, 6, 4]
    hour = random.choices(range(24), weights=weights)[0]
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"


def _jitter(val, amount=0.02):
    return val + random.uniform(-amount, amount)


def _clamp_tn(lat, lng):
    """Clamp coordinates to stay inside Tamil Nadu land area (off the sea and borders)."""
    lat = max(8.07, min(13.4, lat))
    lng = max(76.25, min(80.3, lng))
    # East coast boundary — keep points on land
    if lat < 9.0:
        lng = min(lng, 79.0)
    elif lat < 10.0:
        lng = min(lng, 79.3)
    elif lat < 10.5:
        lng = min(lng, 79.6)
    elif lat < 11.0:
        lng = min(lng, 79.7)
    elif lat < 12.0:
        lng = min(lng, 79.9)
    elif lat < 12.5:
        lng = min(lng, 80.0)
    elif lat < 13.0:
        lng = min(lng, 80.15)
    else:
        lng = min(lng, 80.25)
    return round(lat, 6), round(lng, 6)


# ═══════════════════════════════════════════════════════════════
# WOMEN SAFETY ZONES DATA
# ═══════════════════════════════════════════════════════════════
WOMEN_SAFETY_ZONES_DATA = [
    ("ECR Highway - Thiruvanmiyur to Mahabalipuram", "Highway", 12.9516, 80.2478, 2000, "High", "Hourly", "CHN"),
    ("GST Road - Chromepet to Singaperumal Koil", "Highway", 12.7516, 80.0478, 1500, "Medium", "Regular", "CGP"),
    ("Mount Road - Anna Salai", "City", 13.0604, 80.2496, 500, "Medium", "Regular", "CHN"),
    ("T. Nagar Shopping Area", "Commercial", 13.0418, 80.2341, 400, "Medium", "Regular", "CHN"),
    ("Chennai Central Station Area", "City", 13.0827, 80.2785, 300, "High", "Hourly", "CHN"),
    ("Coimbatore Bus Stand Area", "City", 11.0018, 76.9558, 400, "Medium", "Regular", "CBE"),
    ("Madurai Meenakshi Temple Area", "City", 9.9195, 78.1193, 300, "Low", "Daily", "MDU"),
    ("NH-44 Krishnagiri Stretch", "Highway", 12.5186, 78.2137, 3000, "High", "Hourly", "KGI"),
    ("NH-48 Salem - Dharmapuri", "Highway", 11.9000, 78.1500, 2500, "High", "Hourly", "SLM"),
    ("Trichy Chathram Bus Stand", "City", 10.8050, 78.6856, 400, "Medium", "Regular", "TRY"),
    ("Velankanni Church Road", "City", 10.6833, 79.8500, 300, "Low", "Daily", "NGP"),
    ("Nagercoil Town Center", "City", 8.1780, 77.4345, 400, "Medium", "Regular", "KNY"),
    ("Tirunelveli Junction Area", "City", 8.7270, 77.6860, 500, "Medium", "Regular", "TNV"),
    ("NH-45 Villupuram Highway", "Highway", 11.9401, 79.4861, 2000, "High", "Hourly", "VPM"),
    ("Thanjavur Palace Area", "City", 10.7870, 79.1378, 300, "Low", "Daily", "TNJ"),
    ("Erode Bus Stand Complex", "City", 11.3410, 77.7172, 400, "Medium", "Regular", "ERD"),
    ("Anna University Campus Road", "Educational", 13.0108, 80.2354, 500, "Low", "Daily", "CHN"),
    ("Sathyamangalam Highway", "Highway", 11.5050, 77.2380, 3000, "High", "Hourly", "ERD"),
    ("Koyambedu Bus Terminus", "City", 13.0694, 80.1948, 500, "High", "Hourly", "CHN"),
    ("Marina Beach Promenade", "City", 13.0500, 80.2824, 800, "Medium", "Regular", "CHN"),
]

# ═══════════════════════════════════════════════════════════════
# ACCIDENT ZONES DATA
# ═══════════════════════════════════════════════════════════════
ACCIDENT_ZONES_DATA = [
    ("Vandalur - Kelambakkam Road Junction", 12.8917, 80.0829, "NH-45", "National Highway", 47, 12, 35, "Critical", "Over speeding", 80, 1, 1),
    ("Mamallapuram Highway Curve", 12.6166, 80.1929, "ECR", "State Highway", 38, 8, 30, "High", "Sharp curve", 60, 0, 0),
    ("Ambattur Industrial Area Signal", 13.1143, 80.1548, "NH-205", "National Highway", 31, 5, 26, "High", "Signal jumping", 40, 1, 1),
    ("Salem - Namakkal NH Junction", 11.4416, 78.1567, "NH-44", "National Highway", 52, 15, 37, "Critical", "Over speeding", 100, 1, 1),
    ("Trichy - Dindigul Highway", 10.5764, 78.3371, "NH-45", "National Highway", 29, 6, 23, "High", "Drunk driving", 80, 0, 1),
    ("Madurai Bypass Road", 9.9500, 78.0800, "NH-44", "National Highway", 35, 9, 26, "High", "Over speeding", 80, 1, 1),
    ("Hosur - Krishnagiri Ghats", 12.6200, 78.0500, "NH-44", "National Highway", 44, 14, 30, "Critical", "Sharp curve", 40, 0, 0),
    ("Coimbatore - Mettupalayam Road", 11.1000, 76.9200, "SH-15", "State Highway", 27, 4, 23, "Medium", "Fog", 60, 1, 0),
    ("Thoothukudi Port Road", 8.8050, 78.1000, "Port Road", "District Road", 18, 3, 15, "Medium", "Heavy vehicles", 40, 1, 1),
    ("Ooty - Coonoor Ghat Road", 11.3500, 76.7200, "SH-17", "State Highway", 56, 18, 38, "Critical", "Sharp curve", 30, 0, 0),
    ("Tindivanam - Gingee Road", 12.2333, 79.4500, "SH-9", "State Highway", 22, 5, 17, "Medium", "Bad road", 60, 0, 0),
    ("Kanyakumari - Nagercoil Highway", 8.1500, 77.4800, "NH-44", "National Highway", 25, 6, 19, "High", "Over speeding", 80, 1, 1),
    ("Thanjavur - Kumbakonam Road", 10.8500, 79.3500, "SH-22", "State Highway", 21, 4, 17, "Medium", "Drunk driving", 60, 1, 0),
    ("Erode - Gobichettipalayam Road", 11.4100, 77.4400, "SH-79", "State Highway", 19, 3, 16, "Medium", "Over speeding", 60, 0, 0),
    ("Vellore - Katpadi Junction", 12.9700, 79.1500, "NH-46", "National Highway", 33, 7, 26, "High", "Signal jumping", 40, 1, 1),
    ("Pudukkottai - Karaikudi Road", 10.2600, 78.7000, "SH-33", "State Highway", 16, 2, 14, "Medium", "Cattle crossing", 60, 0, 0),
    ("Dharmapuri - Pappireddipatti Ghats", 12.0500, 78.0200, "SH-68", "State Highway", 41, 11, 30, "Critical", "Sharp curve", 30, 0, 0),
    ("Tirunelveli - Tenkasi Road", 8.8400, 77.5200, "NH-744", "National Highway", 28, 6, 22, "High", "Over speeding", 80, 1, 0),
    ("Chengalpattu - Madurantakam Road", 12.5500, 79.9000, "SH-116", "State Highway", 20, 3, 17, "Medium", "Bad road", 60, 0, 0),
    ("Uthiramerur - Kanchipuram Road", 12.7800, 79.7500, "SH-58", "State Highway", 15, 2, 13, "Medium", "Over speeding", 60, 0, 0),
]


# ═══════════════════════════════════════════════════════════════
# SEED FUNCTION
# ═══════════════════════════════════════════════════════════════
def seed_database(db_path: str):
    """Seed the database with all Tamil Nadu data."""
    print("[*] Seeding CCTNS-GridX database...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ─── Read and execute schema ────────────────────────────
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    print("  [OK] Schema created")

    # ─── Districts ──────────────────────────────────────────
    for d in DISTRICTS:
        cursor.execute(
            "INSERT OR IGNORE INTO districts (name, code, lat, lng, population, area_sq_km, zone) VALUES (?,?,?,?,?,?,?)",
            (d["name"], d["code"], d["lat"], d["lng"], d["population"], d["area"], d["zone"]),
        )
    conn.commit()
    print(f"  [OK] {len(DISTRICTS)} districts inserted")

    # ─── Police Stations ────────────────────────────────────
    district_ids = {}
    for row in cursor.execute("SELECT id, name, code FROM districts"):
        district_ids[row[1]] = row[0]
        district_ids[row[2]] = row[0]

    station_count = 0
    for d in DISTRICTS:
        did = district_ids[d["name"]]
        stations = STATION_TEMPLATES.get(d["name"], GENERIC_STATIONS)
        for sname, stype in stations:
            # If generic, prefix with district name
            full_name = sname if d["name"] in STATION_TEMPLATES else f"{d['name']} {sname}"
            slat, slng = _clamp_tn(_jitter(d["lat"], 0.05), _jitter(d["lng"], 0.05))
            cursor.execute(
                "INSERT INTO police_stations (name, district_id, lat, lng, station_type, sho_name) VALUES (?,?,?,?,?,?)",
                (full_name, did, slat, slng, stype, _random_name("Male")),
            )
            station_count += 1
    conn.commit()
    print(f"  [OK] {station_count} police stations inserted")

    # ─── Crime Categories ───────────────────────────────────
    for cat in CRIME_CATEGORIES:
        cursor.execute(
            "INSERT OR IGNORE INTO crime_categories (act_name, section, description, severity, crime_type, is_cognizable, is_bailable) VALUES (?,?,?,?,?,?,?)",
            cat,
        )
    conn.commit()
    print(f"  [OK] {len(CRIME_CATEGORIES)} crime categories inserted")

    # ─── Fetch IDs for FIR generation ───────────────────────
    stations = cursor.execute("SELECT id, district_id, lat, lng FROM police_stations").fetchall()
    categories = cursor.execute("SELECT id, act_name, section, crime_type, severity FROM crime_categories").fetchall()
    districts_list = cursor.execute("SELECT id, code FROM districts").fetchall()
    district_code_map = {d[0]: d[1] for d in districts_list}

    # ─── FIR Records (2500+) ────────────────────────────────
    fir_count = 0
    # Weight crime categories to make property crime and violent crime more common
    cat_weights = []
    for cat in categories:
        severity = cat[4]
        crime_type = cat[3]
        weight = 10
        if crime_type == "Property Crime":
            weight = 25
        elif crime_type == "Violent Crime":
            weight = 15
        elif crime_type in ("Crime Against Women", "Economic Crime"):
            weight = 12
        elif crime_type == "Narcotics":
            weight = 8
        elif crime_type == "Excise":
            weight = 10
        elif severity >= 5:
            weight = 5
        cat_weights.append(weight)

    for i in range(2500):
        station = random.choice(stations)
        sid, did = station[0], station[1]
        cat = random.choices(categories, weights=cat_weights, k=1)[0]
        cat_id = cat[0]
        crime_type = cat[3]

        dt = _random_date(2023, 2025)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = _random_time()

        # Location jitter around station
        lat, lng = _clamp_tn(_jitter(station[2], 0.03), _jitter(station[3], 0.03))

        # Victim/accused gender logic
        if crime_type in ("Crime Against Women",):
            victim_gender = "Female"
            accused_gender = "Male"
        else:
            victim_gender = random.choice(["Male", "Female", "Male", "Male"])
            accused_gender = random.choice(["Male", "Male", "Male", "Female"])

        victim_name = _random_name(victim_gender)
        accused_name = _random_name(accused_gender)
        complainant_gender = random.choice(["Male", "Female"])
        complainant_name = _random_name(complainant_gender)

        d_code = district_code_map.get(did, "UNK")
        fir_number = f"TN/{d_code}/{sid:03d}/{dt.year}/{fir_count + 1:04d}"

        status = random.choices(
            STATUSES,
            weights=[15, 35, 20, 20, 10],
            k=1,
        )[0]

        mo = random.choice(MODUS_OPERANDI) if random.random() > 0.3 else None
        location = f"{random.choice(LOCATION_TYPES)}, near {victim_name.split()[1]} area"
        prop_value = random.uniform(1000, 500000) if crime_type == "Property Crime" else 0

        cursor.execute(
            """INSERT INTO fir_records (
                fir_number, police_station_id, district_id, crime_category_id,
                date_reported, date_of_crime, time_of_crime,
                latitude, longitude, location_address,
                complainant_name, complainant_age, complainant_gender,
                accused_name, accused_age, accused_gender,
                victim_name, victim_age, victim_gender,
                description, modus_operandi, property_value,
                status, investigating_officer, cctns_synced
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                fir_number, sid, did, cat_id,
                date_str, date_str, time_str,
                lat, lng, location,
                complainant_name, random.randint(20, 65), complainant_gender,
                accused_name, random.randint(18, 55), accused_gender,
                victim_name, random.randint(15, 70), victim_gender,
                f"FIR registered under {cat[1]} {cat[2]}. Incident at {location}.",
                mo, round(prop_value, 2),
                status, _random_name("Male"), random.choice([0, 1]),
            ),
        )
        fir_count += 1

    conn.commit()
    print(f"  [OK] {fir_count} FIR records generated")

    # ─── Women Safety Zones ─────────────────────────────────
    for zone in WOMEN_SAFETY_ZONES_DATA:
        did = district_ids.get(zone[7], 1)
        # Find nearest station
        nearest_sid = None
        min_dist = float("inf")
        for s in stations:
            if s[1] == did:
                d = abs(s[2] - zone[2]) + abs(s[3] - zone[3])
                if d < min_dist:
                    min_dist = d
                    nearest_sid = s[0]

        cursor.execute(
            """INSERT INTO women_safety_zones
                (name, zone_type, lat, lng, radius_meters, risk_level,
                 patrol_frequency, district_id, total_incidents, has_cctv,
                 has_streetlight, nearest_station_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                zone[0], zone[1], zone[2], zone[3], zone[4], zone[5],
                zone[6], did, random.randint(5, 50),
                random.choice([0, 1]), 1, nearest_sid,
            ),
        )
    conn.commit()
    print(f"  [OK] {len(WOMEN_SAFETY_ZONES_DATA)} women safety zones inserted")

    # ─── Accident Zones ─────────────────────────────────────
    for az in ACCIDENT_ZONES_DATA:
        # Find district by proximity
        min_dist = float("inf")
        best_did = 1
        for d in DISTRICTS:
            dist = abs(d["lat"] - az[1]) + abs(d["lng"] - az[2])
            if dist < min_dist:
                min_dist = dist
                best_did = district_ids[d["name"]]

        cursor.execute(
            """INSERT INTO accident_zones
                (location_name, lat, lng, road_name, road_type,
                 accident_count, fatality_count, injury_count, severity,
                 primary_cause, district_id, speed_limit, has_signal, has_divider)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                az[0], az[1], az[2], az[3], az[4],
                az[5], az[6], az[7], az[8],
                az[9], best_did, az[10], az[11], az[12],
            ),
        )
    conn.commit()
    print(f"  [OK] {len(ACCIDENT_ZONES_DATA)} accident zones inserted")

    # ─── Patrol Routes ──────────────────────────────────────
    seasons = ["Summer", "Monsoon", "Winter", "Festival", "General"]
    route_types = ["Regular", "Highway", "Women Safety", "Night", "Emergency"]
    patrol_count = 0

    for d in DISTRICTS[:15]:  # Top 15 districts get patrol routes
        did = district_ids[d["name"]]
        d_stations = [s for s in stations if s[1] == did]
        if not d_stations:
            continue

        for season in random.sample(seasons, k=min(3, len(seasons))):
            rt = random.choice(route_types)
            # Generate waypoints around station locations
            base_station = random.choice(d_stations)
            waypoints = []
            for j in range(random.randint(4, 8)):
                wp_lat, wp_lng = _clamp_tn(_jitter(base_station[2], 0.04), _jitter(base_station[3], 0.04))
                waypoints.append({
                    "lat": wp_lat,
                    "lng": wp_lng,
                    "name": f"Checkpoint {j + 1}",
                })

            cursor.execute(
                """INSERT INTO patrol_routes
                    (name, police_station_id, district_id, season, route_type,
                     waypoints, total_distance_km, estimated_time_mins, priority)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    f"{d['name']} {season} {rt} Patrol",
                    base_station[0], did, season, rt,
                    json.dumps(waypoints),
                    round(random.uniform(5, 40), 1),
                    random.randint(30, 180),
                    random.randint(1, 5),
                ),
            )
            patrol_count += 1

    conn.commit()
    print(f"  [OK] {patrol_count} patrol routes generated")

    # ─── Patrol Units ───────────────────────────────────────
    unit_types = ["Vehicle", "Bike", "Foot", "Highway"]
    unit_statuses = ["Active", "Idle", "On Break"]
    unit_count = 0

    for d in DISTRICTS[:15]:
        did = district_ids[d["name"]]
        d_stations = [s for s in stations if s[1] == did]
        for s in d_stations[:3]:
            ut = random.choice(unit_types)
            cursor.execute(
                """INSERT INTO patrol_units
                    (unit_name, unit_type, police_station_id,
                     current_lat, current_lng, status, officers_count)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    f"{d['name']}-{ut[:3].upper()}-{unit_count + 1:03d}",
                    ut, s[0],
                    *_clamp_tn(_jitter(s[2], 0.02), _jitter(s[3], 0.02)),
                    random.choice(unit_statuses),
                    random.randint(2, 4),
                ),
            )
            unit_count += 1

    conn.commit()
    print(f"  [OK] {unit_count} patrol units created")

    # ─── Users (Demo accounts) ──────────────────────────────
    demo_users = [
        ("sp_admin", "admin123", "Dr. K. Rajendran IPS", "SP", "admin", "TN-SP-001"),
        ("dsp_ops", "admin123", "S. Meenakshi Sundaram", "DSP", "analyst", "TN-DSP-042"),
        ("sho_adyar", "admin123", "R. Vijayakumar", "SHO", "officer", "TN-SHO-101"),
        ("si_patrol", "admin123", "M. Karthikeyan", "SI", "officer", "TN-SI-205"),
        ("constable1", "admin123", "P. Senthilkumar", "CONSTABLE", "viewer", "TN-CON-310"),
    ]
    for username, pwd, full_name, rank, role, badge in demo_users:
        cursor.execute(
            """INSERT OR IGNORE INTO users
                (username, password_hash, full_name, rank, role, badge_number, district_id)
            VALUES (?,?,?,?,?,?,?)""",
            (username, hash_password(pwd), full_name, rank, role, badge, 1),
        )
    conn.commit()
    print(f"  [OK] {len(demo_users)} demo user accounts created")

    # ─── Behavioral Profiles ────────────────────────────────
    bp_count = 0
    for cat in categories[:20]:  # Top 20 crime categories
        for d in DISTRICTS[:10]:  # Top 10 districts
            did = district_ids[d["name"]]
            hourly = [random.randint(1, 20) for _ in range(24)]
            # Make nighttime higher for property crimes
            if cat[3] == "Property Crime":
                for h in [22, 23, 0, 1, 2, 3]:
                    hourly[h] = random.randint(15, 30)
            elif cat[3] == "Crime Against Women":
                for h in [18, 19, 20, 21, 22]:
                    hourly[h] = random.randint(12, 25)

            dow = [random.randint(5, 20) for _ in range(7)]
            monthly = [random.randint(5, 25) for _ in range(12)]

            cursor.execute(
                """INSERT INTO behavioral_profiles
                    (crime_category_id, district_id, hourly_pattern,
                     day_of_week_pattern, monthly_pattern, peak_season,
                     avg_accused_age, predominant_gender,
                     financial_correlation, repeat_offender_rate,
                     urban_rural_ratio, sample_size)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cat[0], did,
                    json.dumps(hourly), json.dumps(dow), json.dumps(monthly),
                    random.choice(["Summer", "Monsoon", "Winter", "Festival"]),
                    round(random.uniform(22, 40), 1),
                    random.choice(["Male", "Male", "Male", "Female"]),
                    random.choice(["Low Income", "Middle Income", "Mixed"]),
                    round(random.uniform(0.05, 0.35), 2),
                    round(random.uniform(0.3, 3.0), 1),
                    random.randint(20, 200),
                ),
            )
            bp_count += 1

    conn.commit()
    print(f"  [OK] {bp_count} behavioral profiles generated")

    conn.close()
    print("[OK] Database seeding complete!")


if __name__ == "__main__":
    seed_database(config.DATABASE_PATH)
