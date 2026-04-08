"""
Comprehensive airport database for autocomplete search.

Contains major airports worldwide with IATA code, name, city, country, and keywords.
Used by the /api/flights/airports endpoint for typeahead search.
"""

# Each entry: (IATA code, airport name, city, country, [keywords])
AIRPORTS = [
    # ── United States ──
    ("JFK", "John F. Kennedy International", "New York", "United States", ["nyc", "manhattan", "brooklyn", "queens"]),
    ("LGA", "LaGuardia", "New York", "United States", ["nyc", "manhattan"]),
    ("EWR", "Newark Liberty International", "Newark", "United States", ["new jersey", "nyc"]),
    ("LAX", "Los Angeles International", "Los Angeles", "United States", ["la", "hollywood"]),
    ("ORD", "O'Hare International", "Chicago", "United States", ["ohare"]),
    ("MDW", "Midway International", "Chicago", "United States", []),
    ("SFO", "San Francisco International", "San Francisco", "United States", ["sf", "bay area"]),
    ("MIA", "Miami International", "Miami", "United States", ["florida", "south florida"]),
    ("DFW", "Dallas/Fort Worth International", "Dallas", "United States", ["fort worth", "dfw"]),
    ("IAH", "George Bush Intercontinental", "Houston", "United States", []),
    ("HOU", "William P. Hobby", "Houston", "United States", ["hobby"]),
    ("SEA", "Seattle-Tacoma International", "Seattle", "United States", ["seatac", "tacoma"]),
    ("BOS", "Logan International", "Boston", "United States", ["massachusetts"]),
    ("ATL", "Hartsfield-Jackson Atlanta International", "Atlanta", "United States", ["georgia"]),
    ("DEN", "Denver International", "Denver", "United States", ["colorado"]),
    ("LAS", "Harry Reid International", "Las Vegas", "United States", ["vegas", "nevada"]),
    ("MCO", "Orlando International", "Orlando", "United States", ["disney", "florida"]),
    ("IAD", "Washington Dulles International", "Washington DC", "United States", ["dulles", "dc", "virginia", "sterling", "ashburn", "reston"]),
    ("DCA", "Ronald Reagan Washington National", "Washington DC", "United States", ["reagan", "national", "arlington", "dc"]),
    ("BWI", "Baltimore/Washington International", "Baltimore", "United States", ["maryland"]),
    ("PHL", "Philadelphia International", "Philadelphia", "United States", ["philly", "pennsylvania"]),
    ("DTW", "Detroit Metropolitan", "Detroit", "United States", ["michigan"]),
    ("MSP", "Minneapolis-Saint Paul International", "Minneapolis", "United States", ["minnesota", "saint paul", "st paul"]),
    ("PHX", "Phoenix Sky Harbor International", "Phoenix", "United States", ["arizona"]),
    ("SAN", "San Diego International", "San Diego", "United States", ["california"]),
    ("PDX", "Portland International", "Portland", "United States", ["oregon"]),
    ("HNL", "Daniel K. Inouye International", "Honolulu", "United States", ["hawaii", "oahu"]),
    ("ANC", "Ted Stevens Anchorage International", "Anchorage", "United States", ["alaska"]),
    ("CLT", "Charlotte Douglas International", "Charlotte", "United States", ["north carolina"]),
    ("SLC", "Salt Lake City International", "Salt Lake City", "United States", ["utah"]),
    ("BNA", "Nashville International", "Nashville", "United States", ["tennessee"]),
    ("AUS", "Austin-Bergstrom International", "Austin", "United States", ["texas"]),
    ("TPA", "Tampa International", "Tampa", "United States", ["florida"]),
    ("MSY", "Louis Armstrong New Orleans International", "New Orleans", "United States", ["louisiana"]),
    ("PIT", "Pittsburgh International", "Pittsburgh", "United States", ["pennsylvania"]),
    ("IND", "Indianapolis International", "Indianapolis", "United States", ["indiana"]),
    ("SAT", "San Antonio International", "San Antonio", "United States", ["texas"]),
    ("STL", "St. Louis Lambert International", "St. Louis", "United States", ["missouri"]),
    ("FLL", "Fort Lauderdale-Hollywood International", "Fort Lauderdale", "United States", ["florida", "broward"]),
    ("RDU", "Raleigh-Durham International", "Raleigh", "United States", ["durham", "north carolina"]),
    ("MCI", "Kansas City International", "Kansas City", "United States", ["missouri"]),
    ("CMH", "John Glenn Columbus International", "Columbus", "United States", ["ohio"]),
    ("CLE", "Cleveland Hopkins International", "Cleveland", "United States", ["ohio"]),
    ("SMF", "Sacramento International", "Sacramento", "United States", ["california"]),
    ("SJC", "San Jose International", "San Jose", "United States", ["silicon valley", "california"]),
    ("MKE", "Milwaukee Mitchell International", "Milwaukee", "United States", ["wisconsin"]),
    ("JAX", "Jacksonville International", "Jacksonville", "United States", ["florida"]),
    ("MEM", "Memphis International", "Memphis", "United States", ["tennessee"]),
    ("RIC", "Richmond International", "Richmond", "United States", ["virginia"]),
    ("BUF", "Buffalo Niagara International", "Buffalo", "United States", ["new york"]),
    ("OAK", "Oakland International", "Oakland", "United States", ["bay area", "california"]),
    ("BUR", "Hollywood Burbank", "Burbank", "United States", ["los angeles"]),
    ("SNA", "John Wayne", "Santa Ana", "United States", ["orange county", "california"]),
    ("RSW", "Southwest Florida International", "Fort Myers", "United States", ["florida"]),
    ("CVG", "Cincinnati/Northern Kentucky International", "Cincinnati", "United States", ["ohio", "kentucky"]),
    ("OMA", "Eppley Airfield", "Omaha", "United States", ["nebraska"]),
    ("ABQ", "Albuquerque International Sunport", "Albuquerque", "United States", ["new mexico"]),
    ("ONT", "Ontario International", "Ontario", "United States", ["california", "inland empire"]),
    ("RNO", "Reno-Tahoe International", "Reno", "United States", ["nevada", "tahoe"]),
    ("TUL", "Tulsa International", "Tulsa", "United States", ["oklahoma"]),
    ("OKC", "Will Rogers World", "Oklahoma City", "United States", ["oklahoma"]),
    ("BOI", "Boise Airport", "Boise", "United States", ["idaho"]),
    ("BDL", "Bradley International", "Hartford", "United States", ["connecticut", "springfield"]),
    ("PVD", "T.F. Green International", "Providence", "United States", ["rhode island"]),
    ("SDF", "Louisville Muhammad Ali International", "Louisville", "United States", ["kentucky"]),

    # ── Canada ──
    ("YYZ", "Toronto Pearson International", "Toronto", "Canada", ["ontario"]),
    ("YVR", "Vancouver International", "Vancouver", "Canada", ["british columbia", "bc"]),
    ("YUL", "Montreal-Trudeau International", "Montreal", "Canada", ["quebec"]),
    ("YYC", "Calgary International", "Calgary", "Canada", ["alberta"]),
    ("YEG", "Edmonton International", "Edmonton", "Canada", ["alberta"]),
    ("YOW", "Ottawa Macdonald-Cartier International", "Ottawa", "Canada", ["ontario"]),
    ("YHZ", "Halifax Stanfield International", "Halifax", "Canada", ["nova scotia"]),
    ("YWG", "Winnipeg James Armstrong Richardson International", "Winnipeg", "Canada", ["manitoba"]),

    # ── Mexico & Central America ──
    ("MEX", "Mexico City International", "Mexico City", "Mexico", ["cdmx", "benito juarez"]),
    ("CUN", "Cancun International", "Cancun", "Mexico", ["quintana roo", "riviera maya"]),
    ("GDL", "Guadalajara International", "Guadalajara", "Mexico", ["jalisco"]),
    ("SJO", "Juan Santamaria International", "San Jose", "Costa Rica", []),
    ("PTY", "Tocumen International", "Panama City", "Panama", []),
    ("SAL", "Monsenor Oscar Arnulfo Romero International", "San Salvador", "El Salvador", []),
    ("GUA", "La Aurora International", "Guatemala City", "Guatemala", []),

    # ── Caribbean ──
    ("NAS", "Lynden Pindling International", "Nassau", "Bahamas", []),
    ("MBJ", "Sangster International", "Montego Bay", "Jamaica", []),
    ("KIN", "Norman Manley International", "Kingston", "Jamaica", []),
    ("SJU", "Luis Munoz Marin International", "San Juan", "Puerto Rico", []),
    ("PUJ", "Punta Cana International", "Punta Cana", "Dominican Republic", []),
    ("SDQ", "Las Americas International", "Santo Domingo", "Dominican Republic", []),

    # ── South America ──
    ("GRU", "Sao Paulo-Guarulhos International", "Sao Paulo", "Brazil", ["guarulhos"]),
    ("GIG", "Rio de Janeiro-Galeao International", "Rio de Janeiro", "Brazil", ["rio", "galeao"]),
    ("EZE", "Ministro Pistarini International", "Buenos Aires", "Argentina", ["ezeiza"]),
    ("LIM", "Jorge Chavez International", "Lima", "Peru", []),
    ("BOG", "El Dorado International", "Bogota", "Colombia", []),
    ("SCL", "Arturo Merino Benitez International", "Santiago", "Chile", []),
    ("MDE", "Jose Maria Cordova International", "Medellin", "Colombia", []),
    ("UIO", "Mariscal Sucre International", "Quito", "Ecuador", []),
    ("GYE", "Jose Joaquin de Olmedo International", "Guayaquil", "Ecuador", []),
    ("MVD", "Carrasco International", "Montevideo", "Uruguay", []),
    ("ASU", "Silvio Pettirossi International", "Asuncion", "Paraguay", []),
    ("VVI", "Viru Viru International", "Santa Cruz", "Bolivia", []),
    ("CCS", "Simon Bolivar International", "Caracas", "Venezuela", []),

    # ── United Kingdom & Ireland ──
    ("LHR", "Heathrow", "London", "United Kingdom", ["uk", "england", "heathrow"]),
    ("LGW", "Gatwick", "London", "United Kingdom", ["uk", "england", "gatwick"]),
    ("STN", "Stansted", "London", "United Kingdom", ["uk", "england", "stansted"]),
    ("LTN", "Luton", "London", "United Kingdom", ["uk", "england", "luton"]),
    ("MAN", "Manchester", "Manchester", "United Kingdom", ["uk", "england"]),
    ("BHX", "Birmingham", "Birmingham", "United Kingdom", ["uk", "england"]),
    ("EDI", "Edinburgh", "Edinburgh", "United Kingdom", ["uk", "scotland"]),
    ("GLA", "Glasgow", "Glasgow", "United Kingdom", ["uk", "scotland"]),
    ("BRS", "Bristol", "Bristol", "United Kingdom", ["uk", "england"]),
    ("BFS", "Belfast International", "Belfast", "United Kingdom", ["northern ireland"]),
    ("DUB", "Dublin", "Dublin", "Ireland", ["eire"]),
    ("SNN", "Shannon", "Shannon", "Ireland", ["limerick"]),
    ("ORK", "Cork", "Cork", "Ireland", []),

    # ── Western Europe ──
    ("CDG", "Charles de Gaulle", "Paris", "France", ["roissy"]),
    ("ORY", "Orly", "Paris", "France", []),
    ("NCE", "Nice Cote d'Azur", "Nice", "France", []),
    ("LYS", "Lyon-Saint Exupery", "Lyon", "France", []),
    ("MRS", "Marseille Provence", "Marseille", "France", []),
    ("BER", "Berlin Brandenburg", "Berlin", "Germany", ["deutschland"]),
    ("FRA", "Frankfurt", "Frankfurt", "Germany", ["deutschland"]),
    ("MUC", "Munich", "Munich", "Germany", ["munchen", "deutschland"]),
    ("DUS", "Dusseldorf", "Dusseldorf", "Germany", []),
    ("HAM", "Hamburg", "Hamburg", "Germany", []),
    ("CGN", "Cologne Bonn", "Cologne", "Germany", ["koln"]),
    ("AMS", "Schiphol", "Amsterdam", "Netherlands", ["holland"]),
    ("BRU", "Brussels", "Brussels", "Belgium", []),
    ("ZRH", "Zurich", "Zurich", "Switzerland", []),
    ("GVA", "Geneva", "Geneva", "Switzerland", []),
    ("BSL", "EuroAirport Basel-Mulhouse-Freiburg", "Basel", "Switzerland", []),
    ("VIE", "Vienna International", "Vienna", "Austria", ["wien"]),
    ("LIS", "Lisbon Humberto Delgado", "Lisbon", "Portugal", ["lisboa"]),
    ("OPO", "Porto Francisco Sa Carneiro", "Porto", "Portugal", []),
    ("MAD", "Adolfo Suarez Madrid-Barajas", "Madrid", "Spain", []),
    ("BCN", "Barcelona-El Prat", "Barcelona", "Spain", ["catalonia"]),
    ("AGP", "Malaga-Costa del Sol", "Malaga", "Spain", ["costa del sol"]),
    ("PMI", "Palma de Mallorca", "Palma", "Spain", ["mallorca", "majorca"]),
    ("FCO", "Leonardo da Vinci-Fiumicino", "Rome", "Italy", ["roma", "fiumicino"]),
    ("MXP", "Milan Malpensa", "Milan", "Italy", ["milano"]),
    ("VCE", "Venice Marco Polo", "Venice", "Italy", ["venezia"]),
    ("NAP", "Naples International", "Naples", "Italy", ["napoli"]),
    ("FLR", "Florence Amerigo Vespucci", "Florence", "Italy", ["firenze"]),
    ("BGY", "Milan Bergamo", "Bergamo", "Italy", ["orio al serio"]),

    # ── Northern Europe ──
    ("CPH", "Copenhagen Kastrup", "Copenhagen", "Denmark", ["kobenhavn"]),
    ("ARN", "Stockholm Arlanda", "Stockholm", "Sweden", []),
    ("GOT", "Gothenburg Landvetter", "Gothenburg", "Sweden", []),
    ("OSL", "Oslo Gardermoen", "Oslo", "Norway", []),
    ("BGO", "Bergen Flesland", "Bergen", "Norway", []),
    ("HEL", "Helsinki-Vantaa", "Helsinki", "Finland", []),
    ("KEF", "Keflavik International", "Reykjavik", "Iceland", []),

    # ── Eastern Europe ──
    ("WAW", "Warsaw Chopin", "Warsaw", "Poland", ["warszawa"]),
    ("KRK", "Krakow John Paul II", "Krakow", "Poland", ["cracow"]),
    ("PRG", "Vaclav Havel", "Prague", "Czech Republic", ["praha", "czechia"]),
    ("BUD", "Budapest Ferenc Liszt", "Budapest", "Hungary", []),
    ("OTP", "Henri Coanda", "Bucharest", "Romania", []),
    ("SOF", "Sofia", "Sofia", "Bulgaria", []),
    ("BEG", "Nikola Tesla", "Belgrade", "Serbia", []),
    ("ZAG", "Franjo Tudman", "Zagreb", "Croatia", []),
    ("SPU", "Split", "Split", "Croatia", []),
    ("DBV", "Dubrovnik", "Dubrovnik", "Croatia", []),
    ("LJU", "Joze Pucnik Ljubljana", "Ljubljana", "Slovenia", []),
    ("TIA", "Tirana International", "Tirana", "Albania", []),
    ("SKP", "Skopje Alexander the Great", "Skopje", "North Macedonia", []),
    ("SJJ", "Sarajevo International", "Sarajevo", "Bosnia and Herzegovina", []),

    # ── Greece & Turkey ──
    ("ATH", "Athens Eleftherios Venizelos", "Athens", "Greece", []),
    ("SKG", "Thessaloniki Macedonia", "Thessaloniki", "Greece", []),
    ("HER", "Heraklion Nikos Kazantzakis", "Heraklion", "Greece", ["crete"]),
    ("JTR", "Santorini (Thira)", "Santorini", "Greece", ["thira"]),
    ("JMK", "Mykonos", "Mykonos", "Greece", []),
    ("IST", "Istanbul", "Istanbul", "Turkey", []),
    ("SAW", "Istanbul Sabiha Gokcen", "Istanbul", "Turkey", ["sabiha"]),
    ("AYT", "Antalya", "Antalya", "Turkey", []),
    ("ADB", "Izmir Adnan Menderes", "Izmir", "Turkey", []),
    ("ESB", "Ankara Esenboga", "Ankara", "Turkey", []),

    # ── Russia & CIS ──
    ("SVO", "Sheremetyevo", "Moscow", "Russia", []),
    ("DME", "Domodedovo", "Moscow", "Russia", []),
    ("LED", "Pulkovo", "Saint Petersburg", "Russia", ["st petersburg"]),
    ("KBP", "Boryspil International", "Kyiv", "Ukraine", ["kiev"]),
    ("TBS", "Tbilisi International", "Tbilisi", "Georgia", []),
    ("EVN", "Zvartnots International", "Yerevan", "Armenia", []),
    ("GYD", "Heydar Aliyev International", "Baku", "Azerbaijan", []),
    ("TSE", "Nursultan Nazarbayev International", "Astana", "Kazakhstan", []),
    ("ALA", "Almaty International", "Almaty", "Kazakhstan", []),
    ("TAS", "Islam Karimov International", "Tashkent", "Uzbekistan", []),

    # ── Middle East ──
    ("DXB", "Dubai International", "Dubai", "United Arab Emirates", ["uae", "emirates"]),
    ("AUH", "Abu Dhabi International", "Abu Dhabi", "United Arab Emirates", ["uae"]),
    ("SHJ", "Sharjah International", "Sharjah", "United Arab Emirates", ["uae"]),
    ("DOH", "Hamad International", "Doha", "Qatar", []),
    ("RUH", "King Khalid International", "Riyadh", "Saudi Arabia", []),
    ("JED", "King Abdulaziz International", "Jeddah", "Saudi Arabia", ["jiddah"]),
    ("DMM", "King Fahd International", "Dammam", "Saudi Arabia", []),
    ("BAH", "Bahrain International", "Manama", "Bahrain", []),
    ("MCT", "Muscat International", "Muscat", "Oman", []),
    ("KWI", "Kuwait International", "Kuwait City", "Kuwait", []),
    ("TLV", "Ben Gurion", "Tel Aviv", "Israel", ["jerusalem"]),
    ("BEY", "Rafic Hariri International", "Beirut", "Lebanon", []),
    ("AMM", "Queen Alia International", "Amman", "Jordan", []),
    ("BGW", "Baghdad International", "Baghdad", "Iraq", []),
    ("IFN", "Isfahan International", "Isfahan", "Iran", []),
    ("IKA", "Imam Khomeini International", "Tehran", "Iran", []),

    # ── South Asia ──
    ("DEL", "Indira Gandhi International", "Delhi", "India", ["new delhi"]),
    ("BOM", "Chhatrapati Shivaji Maharaj International", "Mumbai", "India", ["bombay"]),
    ("BLR", "Kempegowda International", "Bangalore", "India", ["bengaluru"]),
    ("MAA", "Chennai International", "Chennai", "India", ["madras"]),
    ("CCU", "Netaji Subhas Chandra Bose International", "Kolkata", "India", ["calcutta"]),
    ("HYD", "Rajiv Gandhi International", "Hyderabad", "India", []),
    ("COK", "Cochin International", "Kochi", "India", ["cochin", "kerala"]),
    ("GOI", "Goa Manohar International", "Goa", "India", []),
    ("AMD", "Sardar Vallabhbhai Patel International", "Ahmedabad", "India", []),
    ("PNQ", "Pune Airport", "Pune", "India", []),
    ("JAI", "Jaipur International", "Jaipur", "India", ["rajasthan"]),
    ("IXC", "Chandigarh International", "Chandigarh", "India", []),
    ("LKO", "Chaudhary Charan Singh International", "Lucknow", "India", []),
    ("GAU", "Lokpriya Gopinath Bordoloi International", "Guwahati", "India", ["assam"]),
    ("DAC", "Hazrat Shahjalal International", "Dhaka", "Bangladesh", ["dacca", "mymensingh", "comilla", "gazipur", "narayanganj"]),
    ("CGP", "Shah Amanat International", "Chittagong", "Bangladesh", ["chattogram"]),
    ("ZYL", "Osmani International", "Sylhet", "Bangladesh", []),
    ("JSR", "Jessore Airport", "Jessore", "Bangladesh", ["jashore", "khulna"]),
    ("RJH", "Shah Makhdum Airport", "Rajshahi", "Bangladesh", []),
    ("BZL", "Barisal Airport", "Barisal", "Bangladesh", ["barishal"]),
    ("CXB", "Cox's Bazar Airport", "Cox's Bazar", "Bangladesh", ["coxs bazar"]),
    ("SPD", "Saidpur Airport", "Saidpur", "Bangladesh", ["rangpur", "bogra", "dinajpur"]),
    ("ISB", "Islamabad International", "Islamabad", "Pakistan", []),
    ("KHI", "Jinnah International", "Karachi", "Pakistan", []),
    ("LHE", "Allama Iqbal International", "Lahore", "Pakistan", []),
    ("PEW", "Bacha Khan International", "Peshawar", "Pakistan", []),
    ("KTM", "Tribhuvan International", "Kathmandu", "Nepal", []),
    ("CMB", "Bandaranaike International", "Colombo", "Sri Lanka", []),
    ("MLE", "Velana International", "Male", "Maldives", []),

    # ── Southeast Asia ──
    ("SIN", "Singapore Changi", "Singapore", "Singapore", ["changi"]),
    ("BKK", "Suvarnabhumi", "Bangkok", "Thailand", ["suvarnabhumi"]),
    ("DMK", "Don Mueang", "Bangkok", "Thailand", ["don muang"]),
    ("CNX", "Chiang Mai International", "Chiang Mai", "Thailand", []),
    ("HKT", "Phuket International", "Phuket", "Thailand", []),
    ("KUL", "Kuala Lumpur International", "Kuala Lumpur", "Malaysia", ["klia"]),
    ("PEN", "Penang International", "Penang", "Malaysia", []),
    ("CGK", "Soekarno-Hatta International", "Jakarta", "Indonesia", []),
    ("DPS", "Ngurah Rai International", "Bali", "Indonesia", ["denpasar"]),
    ("SUB", "Juanda International", "Surabaya", "Indonesia", []),
    ("MNL", "Ninoy Aquino International", "Manila", "Philippines", []),
    ("CEB", "Mactan-Cebu International", "Cebu", "Philippines", []),
    ("HAN", "Noi Bai International", "Hanoi", "Vietnam", []),
    ("SGN", "Tan Son Nhat International", "Ho Chi Minh City", "Vietnam", ["saigon"]),
    ("DAD", "Da Nang International", "Da Nang", "Vietnam", []),
    ("PNH", "Phnom Penh International", "Phnom Penh", "Cambodia", []),
    ("REP", "Siem Reap International", "Siem Reap", "Cambodia", ["angkor"]),
    ("VTE", "Wattay International", "Vientiane", "Laos", []),
    ("RGN", "Yangon International", "Yangon", "Myanmar", ["rangoon"]),

    # ── East Asia ──
    ("NRT", "Narita International", "Tokyo", "Japan", ["narita"]),
    ("HND", "Haneda", "Tokyo", "Japan", ["haneda"]),
    ("KIX", "Kansai International", "Osaka", "Japan", []),
    ("NGO", "Chubu Centrair International", "Nagoya", "Japan", []),
    ("CTS", "New Chitose", "Sapporo", "Japan", ["hokkaido"]),
    ("FUK", "Fukuoka", "Fukuoka", "Japan", []),
    ("OKA", "Naha", "Okinawa", "Japan", ["naha"]),
    ("ICN", "Incheon International", "Seoul", "South Korea", ["incheon"]),
    ("GMP", "Gimpo International", "Seoul", "South Korea", ["gimpo"]),
    ("PUS", "Gimhae International", "Busan", "South Korea", []),
    ("CJU", "Jeju International", "Jeju", "South Korea", []),
    ("PEK", "Beijing Capital International", "Beijing", "China", ["peking"]),
    ("PKX", "Beijing Daxing International", "Beijing", "China", ["daxing"]),
    ("PVG", "Shanghai Pudong International", "Shanghai", "China", ["pudong"]),
    ("SHA", "Shanghai Hongqiao International", "Shanghai", "China", ["hongqiao"]),
    ("CAN", "Guangzhou Baiyun International", "Guangzhou", "China", ["canton"]),
    ("SZX", "Shenzhen Bao'an International", "Shenzhen", "China", []),
    ("CTU", "Chengdu Tianfu International", "Chengdu", "China", []),
    ("CKG", "Chongqing Jiangbei International", "Chongqing", "China", []),
    ("XIY", "Xi'an Xianyang International", "Xi'an", "China", ["xian"]),
    ("HGH", "Hangzhou Xiaoshan International", "Hangzhou", "China", []),
    ("WUH", "Wuhan Tianhe International", "Wuhan", "China", []),
    ("KMG", "Kunming Changshui International", "Kunming", "China", []),
    ("HKG", "Hong Kong International", "Hong Kong", "Hong Kong", ["chek lap kok"]),
    ("MFM", "Macau International", "Macau", "Macau", []),
    ("TPE", "Taiwan Taoyuan International", "Taipei", "Taiwan", ["taoyuan"]),
    ("KHH", "Kaohsiung International", "Kaohsiung", "Taiwan", []),
    ("UBN", "Chinggis Khaan International", "Ulaanbaatar", "Mongolia", []),

    # ── Africa ──
    ("CAI", "Cairo International", "Cairo", "Egypt", []),
    ("HRG", "Hurghada International", "Hurghada", "Egypt", []),
    ("SSH", "Sharm el-Sheikh International", "Sharm el-Sheikh", "Egypt", []),
    ("JNB", "O.R. Tambo International", "Johannesburg", "South Africa", ["joburg"]),
    ("CPT", "Cape Town International", "Cape Town", "South Africa", []),
    ("DUR", "King Shaka International", "Durban", "South Africa", []),
    ("NBO", "Jomo Kenyatta International", "Nairobi", "Kenya", []),
    ("MBA", "Moi International", "Mombasa", "Kenya", []),
    ("DAR", "Julius Nyerere International", "Dar es Salaam", "Tanzania", []),
    ("JRO", "Kilimanjaro International", "Kilimanjaro", "Tanzania", ["arusha"]),
    ("ZNZ", "Abeid Amani Karume International", "Zanzibar", "Tanzania", []),
    ("EBB", "Entebbe International", "Kampala", "Uganda", ["entebbe"]),
    ("KGL", "Kigali International", "Kigali", "Rwanda", []),
    ("ADD", "Addis Ababa Bole International", "Addis Ababa", "Ethiopia", ["bole"]),
    ("LOS", "Murtala Muhammed International", "Lagos", "Nigeria", []),
    ("ABV", "Nnamdi Azikiwe International", "Abuja", "Nigeria", []),
    ("ACC", "Kotoka International", "Accra", "Ghana", []),
    ("CMN", "Mohammed V International", "Casablanca", "Morocco", []),
    ("RAK", "Menara", "Marrakech", "Morocco", []),
    ("TUN", "Tunis-Carthage International", "Tunis", "Tunisia", []),
    ("ALG", "Houari Boumediene", "Algiers", "Algeria", []),
    ("DSS", "Blaise Diagne International", "Dakar", "Senegal", []),
    ("ABJ", "Felix-Houphouet-Boigny International", "Abidjan", "Ivory Coast", ["cote d'ivoire"]),
    ("TNR", "Ivato International", "Antananarivo", "Madagascar", []),
    ("MRU", "Sir Seewoosagur Ramgoolam International", "Mauritius", "Mauritius", ["port louis"]),

    # ── Oceania ──
    ("SYD", "Sydney Kingsford Smith", "Sydney", "Australia", []),
    ("MEL", "Melbourne Tullamarine", "Melbourne", "Australia", []),
    ("BNE", "Brisbane", "Brisbane", "Australia", ["queensland"]),
    ("PER", "Perth", "Perth", "Australia", ["western australia"]),
    ("ADL", "Adelaide", "Adelaide", "Australia", ["south australia"]),
    ("CBR", "Canberra", "Canberra", "Australia", []),
    ("OOL", "Gold Coast", "Gold Coast", "Australia", ["coolangatta"]),
    ("CNS", "Cairns", "Cairns", "Australia", ["tropical north queensland"]),
    ("AKL", "Auckland", "Auckland", "New Zealand", []),
    ("WLG", "Wellington International", "Wellington", "New Zealand", []),
    ("CHC", "Christchurch International", "Christchurch", "New Zealand", []),
    ("ZQN", "Queenstown", "Queenstown", "New Zealand", []),
    ("NAN", "Nadi International", "Nadi", "Fiji", ["fiji"]),
    ("PPT", "Faaa International", "Papeete", "French Polynesia", ["tahiti"]),
]


def search_airports(query: str, limit: int = 10) -> list:
    """
    Search airports by query string. Matches against IATA code, city, country,
    airport name, and keywords. Returns best matches sorted by relevance.
    """
    if not query or len(query.strip()) < 1:
        return []

    q = query.strip().lower()
    results = []

    for code, name, city, country, keywords in AIRPORTS:
        score = 0
        code_lower = code.lower()
        city_lower = city.lower()
        country_lower = country.lower()
        name_lower = name.lower()

        # Exact IATA code match — highest priority
        if q == code_lower:
            score = 1000
        # IATA code starts with query
        elif code_lower.startswith(q):
            score = 500
        # Exact city match
        elif q == city_lower:
            score = 400
        # City starts with query
        elif city_lower.startswith(q):
            score = 300
        # City contains query
        elif q in city_lower:
            score = 200
        # Country starts with query
        elif country_lower.startswith(q):
            score = 150
        # Country contains query
        elif q in country_lower:
            score = 100
        # Airport name contains query
        elif q in name_lower:
            score = 80
        # Keyword match
        elif any(q in kw or kw.startswith(q) for kw in keywords):
            score = 70
        # Multi-word query: check if all words appear somewhere
        else:
            words = q.split()
            if len(words) > 1:
                searchable = f"{code_lower} {city_lower} {country_lower} {name_lower} {' '.join(keywords)}"
                if all(w in searchable for w in words):
                    score = 60

        if score > 0:
            results.append((score, {
                "code": code,
                "name": name,
                "city": city,
                "country": country,
                "display": f"{city} ({code}) - {name}, {country}",
            }))

    # Sort by score desc, then alphabetically by city
    results.sort(key=lambda x: (-x[0], x[1]["city"]))
    return [r[1] for r in results[:limit]]
