-- India Geographic Seed Data for sales_tracker
-- Idempotent: uses INSERT IGNORE so re-running is safe.
-- Schema dependency: regions, districts, accounts (see schema_v2.sql)

USE sales_tracker;

-- =========================================================
-- 1) REGIONS — 28 states + 8 union territories = 36 total
-- =========================================================
INSERT IGNORE INTO regions (name, code, type) VALUES
  ('Andhra Pradesh',                                   'AP', 'state'),
  ('Arunachal Pradesh',                                'AR', 'state'),
  ('Assam',                                            'AS', 'state'),
  ('Bihar',                                            'BR', 'state'),
  ('Chhattisgarh',                                     'CG', 'state'),
  ('Goa',                                              'GA', 'state'),
  ('Gujarat',                                          'GJ', 'state'),
  ('Haryana',                                          'HR', 'state'),
  ('Himachal Pradesh',                                 'HP', 'state'),
  ('Jharkhand',                                        'JH', 'state'),
  ('Karnataka',                                        'KA', 'state'),
  ('Kerala',                                           'KL', 'state'),
  ('Madhya Pradesh',                                   'MP', 'state'),
  ('Maharashtra',                                      'MH', 'state'),
  ('Manipur',                                          'MN', 'state'),
  ('Meghalaya',                                        'ML', 'state'),
  ('Mizoram',                                          'MZ', 'state'),
  ('Nagaland',                                         'NL', 'state'),
  ('Odisha',                                           'OR', 'state'),
  ('Punjab',                                           'PB', 'state'),
  ('Rajasthan',                                        'RJ', 'state'),
  ('Sikkim',                                           'SK', 'state'),
  ('Tamil Nadu',                                       'TN', 'state'),
  ('Telangana',                                        'TG', 'state'),
  ('Tripura',                                          'TR', 'state'),
  ('Uttar Pradesh',                                    'UP', 'state'),
  ('Uttarakhand',                                      'UK', 'state'),
  ('West Bengal',                                      'WB', 'state'),
  ('Andaman and Nicobar Islands',                      'AN', 'ut'),
  ('Chandigarh',                                       'CH', 'ut'),
  ('Dadra and Nagar Haveli and Daman and Diu',         'DN', 'ut'),
  ('Delhi',                                            'DL', 'ut'),
  ('Jammu and Kashmir',                                'JK', 'ut'),
  ('Ladakh',                                           'LA', 'ut'),
  ('Lakshadweep',                                      'LD', 'ut'),
  ('Puducherry',                                       'PY', 'ut');


-- =========================================================
-- 2) DISTRICTS — ~640 districts across all 36 regions
-- =========================================================

-- ---------- Andhra Pradesh (26) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Alluri Sitharama Raju' AS name UNION ALL SELECT 'Anakapalli' UNION ALL
  SELECT 'Anantapur' UNION ALL SELECT 'Annamayya' UNION ALL SELECT 'Bapatla' UNION ALL
  SELECT 'Chittoor' UNION ALL SELECT 'East Godavari' UNION ALL SELECT 'Eluru' UNION ALL
  SELECT 'Guntur' UNION ALL SELECT 'Kakinada' UNION ALL SELECT 'Konaseema' UNION ALL
  SELECT 'Krishna' UNION ALL SELECT 'Kurnool' UNION ALL SELECT 'Nandyal' UNION ALL
  SELECT 'NTR' UNION ALL SELECT 'Palnadu' UNION ALL SELECT 'Parvathipuram Manyam' UNION ALL
  SELECT 'Prakasam' UNION ALL SELECT 'Sri Potti Sriramulu Nellore' UNION ALL
  SELECT 'Sri Sathya Sai' UNION ALL SELECT 'Srikakulam' UNION ALL SELECT 'Tirupati' UNION ALL
  SELECT 'Visakhapatnam' UNION ALL SELECT 'Vizianagaram' UNION ALL SELECT 'West Godavari' UNION ALL
  SELECT 'YSR Kadapa'
) t WHERE regions.code = 'AP';

-- ---------- Arunachal Pradesh (25) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Anjaw' AS name UNION ALL SELECT 'Changlang' UNION ALL SELECT 'Dibang Valley' UNION ALL
  SELECT 'East Kameng' UNION ALL SELECT 'East Siang' UNION ALL SELECT 'Kamle' UNION ALL
  SELECT 'Kra Daadi' UNION ALL SELECT 'Kurung Kumey' UNION ALL SELECT 'Lepa Rada' UNION ALL
  SELECT 'Lohit' UNION ALL SELECT 'Longding' UNION ALL SELECT 'Lower Dibang Valley' UNION ALL
  SELECT 'Lower Siang' UNION ALL SELECT 'Lower Subansiri' UNION ALL SELECT 'Namsai' UNION ALL
  SELECT 'Pakke Kessang' UNION ALL SELECT 'Papum Pare' UNION ALL SELECT 'Shi Yomi' UNION ALL
  SELECT 'Siang' UNION ALL SELECT 'Tawang' UNION ALL SELECT 'Tirap' UNION ALL
  SELECT 'Upper Siang' UNION ALL SELECT 'Upper Subansiri' UNION ALL SELECT 'West Kameng' UNION ALL
  SELECT 'West Siang'
) t WHERE regions.code = 'AR';

-- ---------- Assam (35) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Bajali' AS name UNION ALL SELECT 'Baksa' UNION ALL SELECT 'Barpeta' UNION ALL
  SELECT 'Biswanath' UNION ALL SELECT 'Bongaigaon' UNION ALL SELECT 'Cachar' UNION ALL
  SELECT 'Charaideo' UNION ALL SELECT 'Chirang' UNION ALL SELECT 'Darrang' UNION ALL
  SELECT 'Dhemaji' UNION ALL SELECT 'Dhubri' UNION ALL SELECT 'Dibrugarh' UNION ALL
  SELECT 'Dima Hasao' UNION ALL SELECT 'Goalpara' UNION ALL SELECT 'Golaghat' UNION ALL
  SELECT 'Hailakandi' UNION ALL SELECT 'Hojai' UNION ALL SELECT 'Jorhat' UNION ALL
  SELECT 'Kamrup' UNION ALL SELECT 'Kamrup Metropolitan' UNION ALL SELECT 'Karbi Anglong' UNION ALL
  SELECT 'Karimganj' UNION ALL SELECT 'Kokrajhar' UNION ALL SELECT 'Lakhimpur' UNION ALL
  SELECT 'Majuli' UNION ALL SELECT 'Morigaon' UNION ALL SELECT 'Nagaon' UNION ALL
  SELECT 'Nalbari' UNION ALL SELECT 'Sivasagar' UNION ALL SELECT 'Sonitpur' UNION ALL
  SELECT 'South Salmara-Mankachar' UNION ALL SELECT 'Tinsukia' UNION ALL SELECT 'Udalguri' UNION ALL
  SELECT 'West Karbi Anglong' UNION ALL SELECT 'Bishwanath'
) t WHERE regions.code = 'AS';

-- ---------- Bihar (38) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Araria' AS name UNION ALL SELECT 'Arwal' UNION ALL SELECT 'Aurangabad' UNION ALL
  SELECT 'Banka' UNION ALL SELECT 'Begusarai' UNION ALL SELECT 'Bhagalpur' UNION ALL
  SELECT 'Bhojpur' UNION ALL SELECT 'Buxar' UNION ALL SELECT 'Darbhanga' UNION ALL
  SELECT 'East Champaran' UNION ALL SELECT 'Gaya' UNION ALL SELECT 'Gopalganj' UNION ALL
  SELECT 'Jamui' UNION ALL SELECT 'Jehanabad' UNION ALL SELECT 'Kaimur' UNION ALL
  SELECT 'Katihar' UNION ALL SELECT 'Khagaria' UNION ALL SELECT 'Kishanganj' UNION ALL
  SELECT 'Lakhisarai' UNION ALL SELECT 'Madhepura' UNION ALL SELECT 'Madhubani' UNION ALL
  SELECT 'Munger' UNION ALL SELECT 'Muzaffarpur' UNION ALL SELECT 'Nalanda' UNION ALL
  SELECT 'Nawada' UNION ALL SELECT 'Patna' UNION ALL SELECT 'Purnia' UNION ALL
  SELECT 'Rohtas' UNION ALL SELECT 'Saharsa' UNION ALL SELECT 'Samastipur' UNION ALL
  SELECT 'Saran' UNION ALL SELECT 'Sheikhpura' UNION ALL SELECT 'Sheohar' UNION ALL
  SELECT 'Sitamarhi' UNION ALL SELECT 'Siwan' UNION ALL SELECT 'Supaul' UNION ALL
  SELECT 'Vaishali' UNION ALL SELECT 'West Champaran'
) t WHERE regions.code = 'BR';

-- ---------- Chhattisgarh (33) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Balod' AS name UNION ALL SELECT 'Baloda Bazar' UNION ALL SELECT 'Balrampur' UNION ALL
  SELECT 'Bastar' UNION ALL SELECT 'Bemetara' UNION ALL SELECT 'Bijapur' UNION ALL
  SELECT 'Bilaspur' UNION ALL SELECT 'Dantewada' UNION ALL SELECT 'Dhamtari' UNION ALL
  SELECT 'Durg' UNION ALL SELECT 'Gariaband' UNION ALL SELECT 'Gaurela-Pendra-Marwahi' UNION ALL
  SELECT 'Janjgir-Champa' UNION ALL SELECT 'Jashpur' UNION ALL SELECT 'Kabirdham' UNION ALL
  SELECT 'Kanker' UNION ALL SELECT 'Khairagarh-Chhuikhadan-Gandai' UNION ALL
  SELECT 'Kondagaon' UNION ALL SELECT 'Korba' UNION ALL SELECT 'Koriya' UNION ALL
  SELECT 'Mahasamund' UNION ALL SELECT 'Manendragarh-Chirmiri-Bharatpur' UNION ALL
  SELECT 'Mohla-Manpur-Ambagarh Chouki' UNION ALL SELECT 'Mungeli' UNION ALL
  SELECT 'Narayanpur' UNION ALL SELECT 'Raigarh' UNION ALL SELECT 'Raipur' UNION ALL
  SELECT 'Rajnandgaon' UNION ALL SELECT 'Sakti' UNION ALL SELECT 'Sarangarh-Bilaigarh' UNION ALL
  SELECT 'Sukma' UNION ALL SELECT 'Surajpur' UNION ALL SELECT 'Surguja'
) t WHERE regions.code = 'CG';

-- ---------- Goa (2) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'North Goa' AS name UNION ALL SELECT 'South Goa'
) t WHERE regions.code = 'GA';

-- ---------- Gujarat (33) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Ahmedabad' AS name UNION ALL SELECT 'Amreli' UNION ALL SELECT 'Anand' UNION ALL
  SELECT 'Aravalli' UNION ALL SELECT 'Banaskantha' UNION ALL SELECT 'Bharuch' UNION ALL
  SELECT 'Bhavnagar' UNION ALL SELECT 'Botad' UNION ALL SELECT 'Chhota Udaipur' UNION ALL
  SELECT 'Dahod' UNION ALL SELECT 'Dang' UNION ALL SELECT 'Devbhoomi Dwarka' UNION ALL
  SELECT 'Gandhinagar' UNION ALL SELECT 'Gir Somnath' UNION ALL SELECT 'Jamnagar' UNION ALL
  SELECT 'Junagadh' UNION ALL SELECT 'Kheda' UNION ALL SELECT 'Kutch' UNION ALL
  SELECT 'Mahisagar' UNION ALL SELECT 'Mehsana' UNION ALL SELECT 'Morbi' UNION ALL
  SELECT 'Narmada' UNION ALL SELECT 'Navsari' UNION ALL SELECT 'Panchmahal' UNION ALL
  SELECT 'Patan' UNION ALL SELECT 'Porbandar' UNION ALL SELECT 'Rajkot' UNION ALL
  SELECT 'Sabarkantha' UNION ALL SELECT 'Surat' UNION ALL SELECT 'Surendranagar' UNION ALL
  SELECT 'Tapi' UNION ALL SELECT 'Vadodara' UNION ALL SELECT 'Valsad'
) t WHERE regions.code = 'GJ';

-- ---------- Haryana (22) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Ambala' AS name UNION ALL SELECT 'Bhiwani' UNION ALL SELECT 'Charkhi Dadri' UNION ALL
  SELECT 'Faridabad' UNION ALL SELECT 'Fatehabad' UNION ALL SELECT 'Gurugram' UNION ALL
  SELECT 'Hisar' UNION ALL SELECT 'Jhajjar' UNION ALL SELECT 'Jind' UNION ALL
  SELECT 'Kaithal' UNION ALL SELECT 'Karnal' UNION ALL SELECT 'Kurukshetra' UNION ALL
  SELECT 'Mahendragarh' UNION ALL SELECT 'Nuh' UNION ALL SELECT 'Palwal' UNION ALL
  SELECT 'Panchkula' UNION ALL SELECT 'Panipat' UNION ALL SELECT 'Rewari' UNION ALL
  SELECT 'Rohtak' UNION ALL SELECT 'Sirsa' UNION ALL SELECT 'Sonipat' UNION ALL
  SELECT 'Yamunanagar'
) t WHERE regions.code = 'HR';

-- ---------- Himachal Pradesh (12) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Bilaspur' AS name UNION ALL SELECT 'Chamba' UNION ALL SELECT 'Hamirpur' UNION ALL
  SELECT 'Kangra' UNION ALL SELECT 'Kinnaur' UNION ALL SELECT 'Kullu' UNION ALL
  SELECT 'Lahaul and Spiti' UNION ALL SELECT 'Mandi' UNION ALL SELECT 'Shimla' UNION ALL
  SELECT 'Sirmaur' UNION ALL SELECT 'Solan' UNION ALL SELECT 'Una'
) t WHERE regions.code = 'HP';

-- ---------- Jharkhand (24) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Bokaro' AS name UNION ALL SELECT 'Chatra' UNION ALL SELECT 'Deoghar' UNION ALL
  SELECT 'Dhanbad' UNION ALL SELECT 'Dumka' UNION ALL SELECT 'East Singhbhum' UNION ALL
  SELECT 'Garhwa' UNION ALL SELECT 'Giridih' UNION ALL SELECT 'Godda' UNION ALL
  SELECT 'Gumla' UNION ALL SELECT 'Hazaribagh' UNION ALL SELECT 'Jamtara' UNION ALL
  SELECT 'Khunti' UNION ALL SELECT 'Koderma' UNION ALL SELECT 'Latehar' UNION ALL
  SELECT 'Lohardaga' UNION ALL SELECT 'Pakur' UNION ALL SELECT 'Palamu' UNION ALL
  SELECT 'Ramgarh' UNION ALL SELECT 'Ranchi' UNION ALL SELECT 'Sahibganj' UNION ALL
  SELECT 'Seraikela Kharsawan' UNION ALL SELECT 'Simdega' UNION ALL SELECT 'West Singhbhum'
) t WHERE regions.code = 'JH';

-- ---------- Karnataka (31) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Bagalkot' AS name UNION ALL SELECT 'Ballari' UNION ALL SELECT 'Belagavi' UNION ALL
  SELECT 'Bengaluru Rural' UNION ALL SELECT 'Bengaluru Urban' UNION ALL SELECT 'Bidar' UNION ALL
  SELECT 'Chamarajanagar' UNION ALL SELECT 'Chikballapur' UNION ALL SELECT 'Chikkamagaluru' UNION ALL
  SELECT 'Chitradurga' UNION ALL SELECT 'Dakshina Kannada' UNION ALL SELECT 'Davanagere' UNION ALL
  SELECT 'Dharwad' UNION ALL SELECT 'Gadag' UNION ALL SELECT 'Hassan' UNION ALL
  SELECT 'Haveri' UNION ALL SELECT 'Kalaburagi' UNION ALL SELECT 'Kodagu' UNION ALL
  SELECT 'Kolar' UNION ALL SELECT 'Koppal' UNION ALL SELECT 'Mandya' UNION ALL
  SELECT 'Mysuru' UNION ALL SELECT 'Raichur' UNION ALL SELECT 'Ramanagara' UNION ALL
  SELECT 'Shivamogga' UNION ALL SELECT 'Tumakuru' UNION ALL SELECT 'Udupi' UNION ALL
  SELECT 'Uttara Kannada' UNION ALL SELECT 'Vijayanagara' UNION ALL SELECT 'Vijayapura' UNION ALL
  SELECT 'Yadgir'
) t WHERE regions.code = 'KA';

-- ---------- Kerala (14) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Alappuzha' AS name UNION ALL SELECT 'Ernakulam' UNION ALL SELECT 'Idukki' UNION ALL
  SELECT 'Kannur' UNION ALL SELECT 'Kasaragod' UNION ALL SELECT 'Kollam' UNION ALL
  SELECT 'Kottayam' UNION ALL SELECT 'Kozhikode' UNION ALL SELECT 'Malappuram' UNION ALL
  SELECT 'Palakkad' UNION ALL SELECT 'Pathanamthitta' UNION ALL SELECT 'Thiruvananthapuram' UNION ALL
  SELECT 'Thrissur' UNION ALL SELECT 'Wayanad'
) t WHERE regions.code = 'KL';

-- ---------- Madhya Pradesh (55) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Agar Malwa' AS name UNION ALL SELECT 'Alirajpur' UNION ALL SELECT 'Anuppur' UNION ALL
  SELECT 'Ashoknagar' UNION ALL SELECT 'Balaghat' UNION ALL SELECT 'Barwani' UNION ALL
  SELECT 'Betul' UNION ALL SELECT 'Bhind' UNION ALL SELECT 'Bhopal' UNION ALL
  SELECT 'Burhanpur' UNION ALL SELECT 'Chhatarpur' UNION ALL SELECT 'Chhindwara' UNION ALL
  SELECT 'Damoh' UNION ALL SELECT 'Datia' UNION ALL SELECT 'Dewas' UNION ALL
  SELECT 'Dhar' UNION ALL SELECT 'Dindori' UNION ALL SELECT 'Guna' UNION ALL
  SELECT 'Gwalior' UNION ALL SELECT 'Harda' UNION ALL SELECT 'Hoshangabad' UNION ALL
  SELECT 'Indore' UNION ALL SELECT 'Jabalpur' UNION ALL SELECT 'Jhabua' UNION ALL
  SELECT 'Katni' UNION ALL SELECT 'Khandwa' UNION ALL SELECT 'Khargone' UNION ALL
  SELECT 'Maihar' UNION ALL SELECT 'Mandla' UNION ALL SELECT 'Mandsaur' UNION ALL
  SELECT 'Mauganj' UNION ALL SELECT 'Morena' UNION ALL SELECT 'Narsinghpur' UNION ALL
  SELECT 'Narmadapuram' UNION ALL SELECT 'Neemuch' UNION ALL SELECT 'Niwari' UNION ALL
  SELECT 'Pandhurna' UNION ALL SELECT 'Panna' UNION ALL SELECT 'Raisen' UNION ALL
  SELECT 'Rajgarh' UNION ALL SELECT 'Ratlam' UNION ALL SELECT 'Rewa' UNION ALL
  SELECT 'Sagar' UNION ALL SELECT 'Satna' UNION ALL SELECT 'Sehore' UNION ALL
  SELECT 'Seoni' UNION ALL SELECT 'Shahdol' UNION ALL SELECT 'Shajapur' UNION ALL
  SELECT 'Sheopur' UNION ALL SELECT 'Shivpuri' UNION ALL SELECT 'Sidhi' UNION ALL
  SELECT 'Singrauli' UNION ALL SELECT 'Tikamgarh' UNION ALL SELECT 'Ujjain' UNION ALL
  SELECT 'Umaria' UNION ALL SELECT 'Vidisha'
) t WHERE regions.code = 'MP';

-- ---------- Maharashtra (36) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Ahmednagar' AS name UNION ALL SELECT 'Akola' UNION ALL SELECT 'Amravati' UNION ALL
  SELECT 'Aurangabad' UNION ALL SELECT 'Beed' UNION ALL SELECT 'Bhandara' UNION ALL
  SELECT 'Buldhana' UNION ALL SELECT 'Chandrapur' UNION ALL SELECT 'Dhule' UNION ALL
  SELECT 'Gadchiroli' UNION ALL SELECT 'Gondia' UNION ALL SELECT 'Hingoli' UNION ALL
  SELECT 'Jalgaon' UNION ALL SELECT 'Jalna' UNION ALL SELECT 'Kolhapur' UNION ALL
  SELECT 'Latur' UNION ALL SELECT 'Mumbai City' UNION ALL SELECT 'Mumbai Suburban' UNION ALL
  SELECT 'Nagpur' UNION ALL SELECT 'Nanded' UNION ALL SELECT 'Nandurbar' UNION ALL
  SELECT 'Nashik' UNION ALL SELECT 'Osmanabad' UNION ALL SELECT 'Palghar' UNION ALL
  SELECT 'Parbhani' UNION ALL SELECT 'Pune' UNION ALL SELECT 'Raigad' UNION ALL
  SELECT 'Ratnagiri' UNION ALL SELECT 'Sangli' UNION ALL SELECT 'Satara' UNION ALL
  SELECT 'Sindhudurg' UNION ALL SELECT 'Solapur' UNION ALL SELECT 'Thane' UNION ALL
  SELECT 'Wardha' UNION ALL SELECT 'Washim' UNION ALL SELECT 'Yavatmal'
) t WHERE regions.code = 'MH';

-- ---------- Manipur (16) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Bishnupur' AS name UNION ALL SELECT 'Chandel' UNION ALL SELECT 'Churachandpur' UNION ALL
  SELECT 'Imphal East' UNION ALL SELECT 'Imphal West' UNION ALL SELECT 'Jiribam' UNION ALL
  SELECT 'Kakching' UNION ALL SELECT 'Kamjong' UNION ALL SELECT 'Kangpokpi' UNION ALL
  SELECT 'Noney' UNION ALL SELECT 'Pherzawl' UNION ALL SELECT 'Senapati' UNION ALL
  SELECT 'Tamenglong' UNION ALL SELECT 'Tengnoupal' UNION ALL SELECT 'Thoubal' UNION ALL
  SELECT 'Ukhrul'
) t WHERE regions.code = 'MN';

-- ---------- Meghalaya (12) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'East Garo Hills' AS name UNION ALL SELECT 'East Jaintia Hills' UNION ALL
  SELECT 'East Khasi Hills' UNION ALL SELECT 'Eastern West Khasi Hills' UNION ALL
  SELECT 'North Garo Hills' UNION ALL SELECT 'Ri Bhoi' UNION ALL SELECT 'South Garo Hills' UNION ALL
  SELECT 'South West Garo Hills' UNION ALL SELECT 'South West Khasi Hills' UNION ALL
  SELECT 'West Garo Hills' UNION ALL SELECT 'West Jaintia Hills' UNION ALL
  SELECT 'West Khasi Hills'
) t WHERE regions.code = 'ML';

-- ---------- Mizoram (11) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Aizawl' AS name UNION ALL SELECT 'Champhai' UNION ALL SELECT 'Hnahthial' UNION ALL
  SELECT 'Khawzawl' UNION ALL SELECT 'Kolasib' UNION ALL SELECT 'Lawngtlai' UNION ALL
  SELECT 'Lunglei' UNION ALL SELECT 'Mamit' UNION ALL SELECT 'Saiha' UNION ALL
  SELECT 'Saitual' UNION ALL SELECT 'Serchhip'
) t WHERE regions.code = 'MZ';

-- ---------- Nagaland (16) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Chumukedima' AS name UNION ALL SELECT 'Dimapur' UNION ALL SELECT 'Kiphire' UNION ALL
  SELECT 'Kohima' UNION ALL SELECT 'Longleng' UNION ALL SELECT 'Mokokchung' UNION ALL
  SELECT 'Mon' UNION ALL SELECT 'Niuland' UNION ALL SELECT 'Noklak' UNION ALL
  SELECT 'Peren' UNION ALL SELECT 'Phek' UNION ALL SELECT 'Shamator' UNION ALL
  SELECT 'Tseminyu' UNION ALL SELECT 'Tuensang' UNION ALL SELECT 'Wokha' UNION ALL
  SELECT 'Zunheboto'
) t WHERE regions.code = 'NL';

-- ---------- Odisha (30) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Angul' AS name UNION ALL SELECT 'Balangir' UNION ALL SELECT 'Balasore' UNION ALL
  SELECT 'Bargarh' UNION ALL SELECT 'Bhadrak' UNION ALL SELECT 'Boudh' UNION ALL
  SELECT 'Cuttack' UNION ALL SELECT 'Debagarh' UNION ALL SELECT 'Dhenkanal' UNION ALL
  SELECT 'Gajapati' UNION ALL SELECT 'Ganjam' UNION ALL SELECT 'Jagatsinghpur' UNION ALL
  SELECT 'Jajpur' UNION ALL SELECT 'Jharsuguda' UNION ALL SELECT 'Kalahandi' UNION ALL
  SELECT 'Kandhamal' UNION ALL SELECT 'Kendrapara' UNION ALL SELECT 'Kendujhar' UNION ALL
  SELECT 'Khordha' UNION ALL SELECT 'Koraput' UNION ALL SELECT 'Malkangiri' UNION ALL
  SELECT 'Mayurbhanj' UNION ALL SELECT 'Nabarangpur' UNION ALL SELECT 'Nayagarh' UNION ALL
  SELECT 'Nuapada' UNION ALL SELECT 'Puri' UNION ALL SELECT 'Rayagada' UNION ALL
  SELECT 'Sambalpur' UNION ALL SELECT 'Subarnapur' UNION ALL SELECT 'Sundargarh'
) t WHERE regions.code = 'OR';

-- ---------- Punjab (23) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Amritsar' AS name UNION ALL SELECT 'Barnala' UNION ALL SELECT 'Bathinda' UNION ALL
  SELECT 'Faridkot' UNION ALL SELECT 'Fatehgarh Sahib' UNION ALL SELECT 'Fazilka' UNION ALL
  SELECT 'Firozpur' UNION ALL SELECT 'Gurdaspur' UNION ALL SELECT 'Hoshiarpur' UNION ALL
  SELECT 'Jalandhar' UNION ALL SELECT 'Kapurthala' UNION ALL SELECT 'Ludhiana' UNION ALL
  SELECT 'Malerkotla' UNION ALL SELECT 'Mansa' UNION ALL SELECT 'Moga' UNION ALL
  SELECT 'Pathankot' UNION ALL SELECT 'Patiala' UNION ALL SELECT 'Rupnagar' UNION ALL
  SELECT 'Sahibzada Ajit Singh Nagar' UNION ALL SELECT 'Sangrur' UNION ALL
  SELECT 'Shaheed Bhagat Singh Nagar' UNION ALL SELECT 'Sri Muktsar Sahib' UNION ALL
  SELECT 'Tarn Taran'
) t WHERE regions.code = 'PB';

-- ---------- Rajasthan (50) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Ajmer' AS name UNION ALL SELECT 'Alwar' UNION ALL SELECT 'Anupgarh' UNION ALL
  SELECT 'Balotra' UNION ALL SELECT 'Banswara' UNION ALL SELECT 'Baran' UNION ALL
  SELECT 'Barmer' UNION ALL SELECT 'Beawar' UNION ALL SELECT 'Bharatpur' UNION ALL
  SELECT 'Bhilwara' UNION ALL SELECT 'Bikaner' UNION ALL SELECT 'Bundi' UNION ALL
  SELECT 'Chittorgarh' UNION ALL SELECT 'Churu' UNION ALL SELECT 'Dausa' UNION ALL
  SELECT 'Deeg' UNION ALL SELECT 'Dholpur' UNION ALL SELECT 'Didwana-Kuchaman' UNION ALL
  SELECT 'Dudu' UNION ALL SELECT 'Dungarpur' UNION ALL SELECT 'Ganganagar' UNION ALL
  SELECT 'Gangapur City' UNION ALL SELECT 'Hanumangarh' UNION ALL SELECT 'Jaipur' UNION ALL
  SELECT 'Jaipur Rural' UNION ALL SELECT 'Jaisalmer' UNION ALL SELECT 'Jalore' UNION ALL
  SELECT 'Jhalawar' UNION ALL SELECT 'Jhunjhunu' UNION ALL SELECT 'Jodhpur' UNION ALL
  SELECT 'Jodhpur Rural' UNION ALL SELECT 'Karauli' UNION ALL SELECT 'Kekri' UNION ALL
  SELECT 'Khairthal-Tijara' UNION ALL SELECT 'Kota' UNION ALL SELECT 'Kotputli-Behror' UNION ALL
  SELECT 'Nagaur' UNION ALL SELECT 'Neem ka Thana' UNION ALL SELECT 'Pali' UNION ALL
  SELECT 'Phalodi' UNION ALL SELECT 'Pratapgarh' UNION ALL SELECT 'Rajsamand' UNION ALL
  SELECT 'Salumbar' UNION ALL SELECT 'Sanchore' UNION ALL SELECT 'Sawai Madhopur' UNION ALL
  SELECT 'Shahpura' UNION ALL SELECT 'Sikar' UNION ALL SELECT 'Sirohi' UNION ALL
  SELECT 'Tonk' UNION ALL SELECT 'Udaipur'
) t WHERE regions.code = 'RJ';

-- ---------- Sikkim (6) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Gangtok' AS name UNION ALL SELECT 'Gyalshing' UNION ALL SELECT 'Mangan' UNION ALL
  SELECT 'Namchi' UNION ALL SELECT 'Pakyong' UNION ALL SELECT 'Soreng'
) t WHERE regions.code = 'SK';

-- ---------- Tamil Nadu (38) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Ariyalur' AS name UNION ALL SELECT 'Chengalpattu' UNION ALL SELECT 'Chennai' UNION ALL
  SELECT 'Coimbatore' UNION ALL SELECT 'Cuddalore' UNION ALL SELECT 'Dharmapuri' UNION ALL
  SELECT 'Dindigul' UNION ALL SELECT 'Erode' UNION ALL SELECT 'Kallakurichi' UNION ALL
  SELECT 'Kanchipuram' UNION ALL SELECT 'Kanyakumari' UNION ALL SELECT 'Karur' UNION ALL
  SELECT 'Krishnagiri' UNION ALL SELECT 'Madurai' UNION ALL SELECT 'Mayiladuthurai' UNION ALL
  SELECT 'Nagapattinam' UNION ALL SELECT 'Namakkal' UNION ALL SELECT 'Nilgiris' UNION ALL
  SELECT 'Perambalur' UNION ALL SELECT 'Pudukkottai' UNION ALL SELECT 'Ramanathapuram' UNION ALL
  SELECT 'Ranipet' UNION ALL SELECT 'Salem' UNION ALL SELECT 'Sivaganga' UNION ALL
  SELECT 'Tenkasi' UNION ALL SELECT 'Thanjavur' UNION ALL SELECT 'Theni' UNION ALL
  SELECT 'Thoothukudi' UNION ALL SELECT 'Tiruchirappalli' UNION ALL SELECT 'Tirunelveli' UNION ALL
  SELECT 'Tirupathur' UNION ALL SELECT 'Tiruppur' UNION ALL SELECT 'Tiruvallur' UNION ALL
  SELECT 'Tiruvannamalai' UNION ALL SELECT 'Tiruvarur' UNION ALL SELECT 'Vellore' UNION ALL
  SELECT 'Viluppuram' UNION ALL SELECT 'Virudhunagar'
) t WHERE regions.code = 'TN';

-- ---------- Telangana (33) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Adilabad' AS name UNION ALL SELECT 'Bhadradri Kothagudem' UNION ALL
  SELECT 'Hanumakonda' UNION ALL SELECT 'Hyderabad' UNION ALL SELECT 'Jagtial' UNION ALL
  SELECT 'Jangaon' UNION ALL SELECT 'Jayashankar Bhupalpally' UNION ALL
  SELECT 'Jogulamba Gadwal' UNION ALL SELECT 'Kamareddy' UNION ALL SELECT 'Karimnagar' UNION ALL
  SELECT 'Khammam' UNION ALL SELECT 'Komaram Bheem' UNION ALL SELECT 'Mahabubabad' UNION ALL
  SELECT 'Mahabubnagar' UNION ALL SELECT 'Mancherial' UNION ALL SELECT 'Medak' UNION ALL
  SELECT 'Medchal Malkajgiri' UNION ALL SELECT 'Mulugu' UNION ALL SELECT 'Nagarkurnool' UNION ALL
  SELECT 'Nalgonda' UNION ALL SELECT 'Narayanpet' UNION ALL SELECT 'Nirmal' UNION ALL
  SELECT 'Nizamabad' UNION ALL SELECT 'Peddapalli' UNION ALL SELECT 'Rajanna Sircilla' UNION ALL
  SELECT 'Rangareddy' UNION ALL SELECT 'Sangareddy' UNION ALL SELECT 'Siddipet' UNION ALL
  SELECT 'Suryapet' UNION ALL SELECT 'Vikarabad' UNION ALL SELECT 'Wanaparthy' UNION ALL
  SELECT 'Warangal' UNION ALL SELECT 'Yadadri Bhuvanagiri'
) t WHERE regions.code = 'TG';

-- ---------- Tripura (8) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Dhalai' AS name UNION ALL SELECT 'Gomati' UNION ALL SELECT 'Khowai' UNION ALL
  SELECT 'North Tripura' UNION ALL SELECT 'Sepahijala' UNION ALL SELECT 'South Tripura' UNION ALL
  SELECT 'Unakoti' UNION ALL SELECT 'West Tripura'
) t WHERE regions.code = 'TR';

-- ---------- Uttar Pradesh (75) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Agra' AS name UNION ALL SELECT 'Aligarh' UNION ALL SELECT 'Ambedkar Nagar' UNION ALL
  SELECT 'Amethi' UNION ALL SELECT 'Amroha' UNION ALL SELECT 'Auraiya' UNION ALL
  SELECT 'Ayodhya' UNION ALL SELECT 'Azamgarh' UNION ALL SELECT 'Baghpat' UNION ALL
  SELECT 'Bahraich' UNION ALL SELECT 'Ballia' UNION ALL SELECT 'Balrampur' UNION ALL
  SELECT 'Banda' UNION ALL SELECT 'Barabanki' UNION ALL SELECT 'Bareilly' UNION ALL
  SELECT 'Basti' UNION ALL SELECT 'Bhadohi' UNION ALL SELECT 'Bijnor' UNION ALL
  SELECT 'Budaun' UNION ALL SELECT 'Bulandshahr' UNION ALL SELECT 'Chandauli' UNION ALL
  SELECT 'Chitrakoot' UNION ALL SELECT 'Deoria' UNION ALL SELECT 'Etah' UNION ALL
  SELECT 'Etawah' UNION ALL SELECT 'Farrukhabad' UNION ALL SELECT 'Fatehpur' UNION ALL
  SELECT 'Firozabad' UNION ALL SELECT 'Gautam Buddha Nagar' UNION ALL SELECT 'Ghaziabad' UNION ALL
  SELECT 'Ghazipur' UNION ALL SELECT 'Gonda' UNION ALL SELECT 'Gorakhpur' UNION ALL
  SELECT 'Hamirpur' UNION ALL SELECT 'Hapur' UNION ALL SELECT 'Hardoi' UNION ALL
  SELECT 'Hathras' UNION ALL SELECT 'Jalaun' UNION ALL SELECT 'Jaunpur' UNION ALL
  SELECT 'Jhansi' UNION ALL SELECT 'Kannauj' UNION ALL SELECT 'Kanpur Dehat' UNION ALL
  SELECT 'Kanpur Nagar' UNION ALL SELECT 'Kasganj' UNION ALL SELECT 'Kaushambi' UNION ALL
  SELECT 'Kheri' UNION ALL SELECT 'Kushinagar' UNION ALL SELECT 'Lalitpur' UNION ALL
  SELECT 'Lucknow' UNION ALL SELECT 'Maharajganj' UNION ALL SELECT 'Mahoba' UNION ALL
  SELECT 'Mainpuri' UNION ALL SELECT 'Mathura' UNION ALL SELECT 'Mau' UNION ALL
  SELECT 'Meerut' UNION ALL SELECT 'Mirzapur' UNION ALL SELECT 'Moradabad' UNION ALL
  SELECT 'Muzaffarnagar' UNION ALL SELECT 'Pilibhit' UNION ALL SELECT 'Pratapgarh' UNION ALL
  SELECT 'Prayagraj' UNION ALL SELECT 'Raebareli' UNION ALL SELECT 'Rampur' UNION ALL
  SELECT 'Saharanpur' UNION ALL SELECT 'Sambhal' UNION ALL SELECT 'Sant Kabir Nagar' UNION ALL
  SELECT 'Shahjahanpur' UNION ALL SELECT 'Shamli' UNION ALL SELECT 'Shrawasti' UNION ALL
  SELECT 'Siddharthnagar' UNION ALL SELECT 'Sitapur' UNION ALL SELECT 'Sonbhadra' UNION ALL
  SELECT 'Sultanpur' UNION ALL SELECT 'Unnao' UNION ALL SELECT 'Varanasi'
) t WHERE regions.code = 'UP';

-- ---------- Uttarakhand (13) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Almora' AS name UNION ALL SELECT 'Bageshwar' UNION ALL SELECT 'Chamoli' UNION ALL
  SELECT 'Champawat' UNION ALL SELECT 'Dehradun' UNION ALL SELECT 'Haridwar' UNION ALL
  SELECT 'Nainital' UNION ALL SELECT 'Pauri Garhwal' UNION ALL SELECT 'Pithoragarh' UNION ALL
  SELECT 'Rudraprayag' UNION ALL SELECT 'Tehri Garhwal' UNION ALL SELECT 'Udham Singh Nagar' UNION ALL
  SELECT 'Uttarkashi'
) t WHERE regions.code = 'UK';

-- ---------- West Bengal (23) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Alipurduar' AS name UNION ALL SELECT 'Bankura' UNION ALL SELECT 'Birbhum' UNION ALL
  SELECT 'Cooch Behar' UNION ALL SELECT 'Dakshin Dinajpur' UNION ALL SELECT 'Darjeeling' UNION ALL
  SELECT 'Hooghly' UNION ALL SELECT 'Howrah' UNION ALL SELECT 'Jalpaiguri' UNION ALL
  SELECT 'Jhargram' UNION ALL SELECT 'Kalimpong' UNION ALL SELECT 'Kolkata' UNION ALL
  SELECT 'Malda' UNION ALL SELECT 'Murshidabad' UNION ALL SELECT 'Nadia' UNION ALL
  SELECT 'North 24 Parganas' UNION ALL SELECT 'Paschim Bardhaman' UNION ALL
  SELECT 'Paschim Medinipur' UNION ALL SELECT 'Purba Bardhaman' UNION ALL
  SELECT 'Purba Medinipur' UNION ALL SELECT 'Purulia' UNION ALL SELECT 'South 24 Parganas' UNION ALL
  SELECT 'Uttar Dinajpur'
) t WHERE regions.code = 'WB';

-- ---------- Andaman and Nicobar (3) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Nicobar' AS name UNION ALL SELECT 'North and Middle Andaman' UNION ALL
  SELECT 'South Andaman'
) t WHERE regions.code = 'AN';

-- ---------- Chandigarh (1) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Chandigarh' AS name
) t WHERE regions.code = 'CH';

-- ---------- Dadra and Nagar Haveli and Daman and Diu (3) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Dadra and Nagar Haveli' AS name UNION ALL SELECT 'Daman' UNION ALL SELECT 'Diu'
) t WHERE regions.code = 'DN';

-- ---------- Delhi (11) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Central Delhi' AS name UNION ALL SELECT 'East Delhi' UNION ALL SELECT 'New Delhi' UNION ALL
  SELECT 'North Delhi' UNION ALL SELECT 'North East Delhi' UNION ALL SELECT 'North West Delhi' UNION ALL
  SELECT 'Shahdara' UNION ALL SELECT 'South Delhi' UNION ALL SELECT 'South East Delhi' UNION ALL
  SELECT 'South West Delhi' UNION ALL SELECT 'West Delhi'
) t WHERE regions.code = 'DL';

-- ---------- Jammu and Kashmir (20) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Anantnag' AS name UNION ALL SELECT 'Bandipora' UNION ALL SELECT 'Baramulla' UNION ALL
  SELECT 'Budgam' UNION ALL SELECT 'Doda' UNION ALL SELECT 'Ganderbal' UNION ALL
  SELECT 'Jammu' UNION ALL SELECT 'Kathua' UNION ALL SELECT 'Kishtwar' UNION ALL
  SELECT 'Kulgam' UNION ALL SELECT 'Kupwara' UNION ALL SELECT 'Poonch' UNION ALL
  SELECT 'Pulwama' UNION ALL SELECT 'Rajouri' UNION ALL SELECT 'Ramban' UNION ALL
  SELECT 'Reasi' UNION ALL SELECT 'Samba' UNION ALL SELECT 'Shopian' UNION ALL
  SELECT 'Srinagar' UNION ALL SELECT 'Udhampur'
) t WHERE regions.code = 'JK';

-- ---------- Ladakh (2) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Kargil' AS name UNION ALL SELECT 'Leh'
) t WHERE regions.code = 'LA';

-- ---------- Lakshadweep (1) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Lakshadweep' AS name
) t WHERE regions.code = 'LD';

-- ---------- Puducherry (4) ----------
INSERT IGNORE INTO districts (region_id, name)
SELECT regions.id, t.name FROM regions, (
  SELECT 'Karaikal' AS name UNION ALL SELECT 'Mahe' UNION ALL SELECT 'Puducherry' UNION ALL
  SELECT 'Yanam'
) t WHERE regions.code = 'PY';


-- =========================================================
-- 3) ACCOUNTS — sample doctors / chemists / stockists in 8 metro districts
-- =========================================================

-- ---------- Mumbai (Mumbai City + Mumbai Suburban) ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Rajesh Mehta' AS name, 'doctor' AS type, 'Cardiology' AS specialty,
         'Lilavati Hospital, Bandra West, Mumbai' AS address, '+91-22-26568000' AS phone,
         19.0596 AS lat, 72.8295 AS lon
  UNION ALL SELECT 'Dr. Priya Iyer', 'doctor', 'Pediatrics',
         'Hinduja Hospital, Mahim, Mumbai', '+91-22-24452222', 19.0411, 72.8419
  UNION ALL SELECT 'Apollo Pharmacy Bandra', 'chemist', NULL,
         'Linking Road, Bandra West, Mumbai', '+91-22-26424500', 19.0606, 72.8311
  UNION ALL SELECT 'Wellness Forever Andheri', 'chemist', NULL,
         'SV Road, Andheri West, Mumbai', '+91-22-26730000', 19.1364, 72.8296
  UNION ALL SELECT 'Mehta Distributors Pvt Ltd', 'stockist', NULL,
         'Lower Parel, Mumbai', '+91-22-24923400', 18.9967, 72.8302
) t
WHERE districts.name = 'Mumbai Suburban' AND regions.code = 'MH';

-- ---------- Delhi (New Delhi district) ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Anil Kapoor' AS name, 'doctor' AS type, 'Orthopedics' AS specialty,
         'AIIMS, Ansari Nagar, New Delhi' AS address, '+91-11-26588500' AS phone,
         28.5672 AS lat, 77.2100 AS lon
  UNION ALL SELECT 'Dr. Sunita Sharma', 'doctor', 'Gynecology',
         'Sir Ganga Ram Hospital, Rajinder Nagar, New Delhi', '+91-11-25750000', 28.6385, 77.1900
  UNION ALL SELECT 'Apollo Pharmacy Connaught Place', 'chemist', NULL,
         'Connaught Place, New Delhi', '+91-11-23416789', 28.6315, 77.2167
  UNION ALL SELECT 'MedPlus Khan Market', 'chemist', NULL,
         'Khan Market, New Delhi', '+91-11-24693200', 28.6000, 77.2273
  UNION ALL SELECT 'Capital Pharma Distributors', 'stockist', NULL,
         'Bhagirath Place, Chandni Chowk, New Delhi', '+91-11-23861100', 28.6562, 77.2300
) t
WHERE districts.name = 'New Delhi' AND regions.code = 'DL';

-- ---------- Bangalore (Bengaluru Urban) ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Venkatesh Rao' AS name, 'doctor' AS type, 'Oncology' AS specialty,
         'Manipal Hospital, HAL Airport Road, Bengaluru' AS address, '+91-80-25023333' AS phone,
         12.9591 AS lat, 77.6493 AS lon
  UNION ALL SELECT 'Dr. Lakshmi Narayan', 'doctor', 'Neurology',
         'NIMHANS, Hosur Road, Bengaluru', '+91-80-26995000', 12.9426, 77.5961
  UNION ALL SELECT 'Apollo Pharmacy Koramangala', 'chemist', NULL,
         '80 Feet Road, Koramangala, Bengaluru', '+91-80-25530000', 12.9352, 77.6245
  UNION ALL SELECT 'MedPlus Indiranagar', 'chemist', NULL,
         '100 Feet Road, Indiranagar, Bengaluru', '+91-80-25218800', 12.9719, 77.6412
  UNION ALL SELECT 'Karnataka Pharma Agencies', 'stockist', NULL,
         'SP Road, Bengaluru', '+91-80-22264500', 12.9698, 77.5810
) t
WHERE districts.name = 'Bengaluru Urban' AND regions.code = 'KA';

-- ---------- Chennai ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Karthik Subramanian' AS name, 'doctor' AS type, 'Cardiology' AS specialty,
         'Apollo Hospitals, Greams Road, Chennai' AS address, '+91-44-28293333' AS phone,
         13.0639 AS lat, 80.2520 AS lon
  UNION ALL SELECT 'Dr. Meera Krishnan', 'doctor', 'Dermatology',
         'MIOT International, Manapakkam, Chennai', '+91-44-42002288', 13.0167, 80.1842
  UNION ALL SELECT 'Apollo Pharmacy T Nagar', 'chemist', NULL,
         'Usman Road, T Nagar, Chennai', '+91-44-28156700', 13.0418, 80.2341
  UNION ALL SELECT 'MedPlus Anna Nagar', 'chemist', NULL,
         '2nd Avenue, Anna Nagar, Chennai', '+91-44-26161200', 13.0850, 80.2101
  UNION ALL SELECT 'Tamil Nadu Pharma Distributors', 'stockist', NULL,
         'Broadway, George Town, Chennai', '+91-44-25351200', 13.0916, 80.2890
) t
WHERE districts.name = 'Chennai' AND regions.code = 'TN';

-- ---------- Kolkata ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Abhijit Banerjee' AS name, 'doctor' AS type, 'Gastroenterology' AS specialty,
         'AMRI Hospitals, Salt Lake, Kolkata' AS address, '+91-33-66800000' AS phone,
         22.5780 AS lat, 88.4101 AS lon
  UNION ALL SELECT 'Dr. Ritu Chatterjee', 'doctor', 'Endocrinology',
         'Apollo Gleneagles, EM Bypass, Kolkata', '+91-33-23203040', 22.5108, 88.3978
  UNION ALL SELECT 'Apollo Pharmacy Park Street', 'chemist', NULL,
         'Park Street, Kolkata', '+91-33-22290900', 22.5530, 88.3520
  UNION ALL SELECT 'Frank Ross Pharmacy', 'chemist', NULL,
         'Esplanade, Kolkata', '+91-33-22481100', 22.5670, 88.3520
  UNION ALL SELECT 'Bengal Chemicals Distributors', 'stockist', NULL,
         'Bagri Market, Canning Street, Kolkata', '+91-33-22210300', 22.5703, 88.3520
) t
WHERE districts.name = 'Kolkata' AND regions.code = 'WB';

-- ---------- Hyderabad ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Srinivas Reddy' AS name, 'doctor' AS type, 'Cardiology' AS specialty,
         'Apollo Hospitals, Jubilee Hills, Hyderabad' AS address, '+91-40-23607777' AS phone,
         17.4172 AS lat, 78.4258 AS lon
  UNION ALL SELECT 'Dr. Anjali Rao', 'doctor', 'Pulmonology',
         'KIMS Hospital, Secunderabad, Hyderabad', '+91-40-44885000', 17.4399, 78.4983
  UNION ALL SELECT 'MedPlus Banjara Hills', 'chemist', NULL,
         'Road No 10, Banjara Hills, Hyderabad', '+91-40-23556700', 17.4126, 78.4380
  UNION ALL SELECT 'Apollo Pharmacy Hitech City', 'chemist', NULL,
         'Hitech City Main Road, Hyderabad', '+91-40-23110000', 17.4485, 78.3908
  UNION ALL SELECT 'Deccan Pharma Distributors', 'stockist', NULL,
         'Koti, Hyderabad', '+91-40-24752000', 17.3850, 78.4867
) t
WHERE districts.name = 'Hyderabad' AND regions.code = 'TG';

-- ---------- Pune ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Sachin Deshpande' AS name, 'doctor' AS type, 'Orthopedics' AS specialty,
         'Ruby Hall Clinic, Sassoon Road, Pune' AS address, '+91-20-66455100' AS phone,
         18.5306 AS lat, 73.8809 AS lon
  UNION ALL SELECT 'Dr. Vaishali Joshi', 'doctor', 'Gynecology',
         'Jehangir Hospital, Sassoon Road, Pune', '+91-20-66811000', 18.5290 , 73.8770
  UNION ALL SELECT 'Apollo Pharmacy Koregaon Park', 'chemist', NULL,
         'North Main Road, Koregaon Park, Pune', '+91-20-26156800', 18.5362, 73.8949
  UNION ALL SELECT 'Wellness Forever Aundh', 'chemist', NULL,
         'ITI Road, Aundh, Pune', '+91-20-25893400', 18.5593, 73.8077
  UNION ALL SELECT 'Maharashtra Pharma Suppliers', 'stockist', NULL,
         'Shukrawar Peth, Pune', '+91-20-24452200', 18.5117, 73.8567
) t
WHERE districts.name = 'Pune' AND regions.code = 'MH';

-- ---------- Ahmedabad ----------
INSERT IGNORE INTO accounts (name, type, specialty, district_id, address, phone, lat, lon)
SELECT t.name, t.type, t.specialty, districts.id, t.address, t.phone, t.lat, t.lon
FROM districts
JOIN regions ON regions.id = districts.region_id
JOIN (
  SELECT 'Dr. Kiran Patel' AS name, 'doctor' AS type, 'Cardiology' AS specialty,
         'CIMS Hospital, Science City Road, Ahmedabad' AS address, '+91-79-30101000' AS phone,
         23.0731 AS lat, 72.5159 AS lon
  UNION ALL SELECT 'Dr. Bhavna Shah', 'doctor', 'Pediatrics',
         'Sterling Hospital, Memnagar, Ahmedabad', '+91-79-40011111', 23.0567, 72.5390
  UNION ALL SELECT 'Apollo Pharmacy Navrangpura', 'chemist', NULL,
         'CG Road, Navrangpura, Ahmedabad', '+91-79-26461500', 23.0388, 72.5610
  UNION ALL SELECT 'MedPlus Satellite', 'chemist', NULL,
         'Satellite Road, Ahmedabad', '+91-79-26929400', 23.0301, 72.5119
  UNION ALL SELECT 'Gujarat Medical Distributors', 'stockist', NULL,
         'Relief Road, Ahmedabad', '+91-79-25506700', 23.0258, 72.5873
) t
WHERE districts.name = 'Ahmedabad' AND regions.code = 'GJ';


-- =========================================================
-- 4) Final count verification
-- =========================================================
SELECT
  (SELECT COUNT(*) FROM regions)   AS region_count,
  (SELECT COUNT(*) FROM districts) AS district_count,
  (SELECT COUNT(*) FROM accounts)  AS account_count;
