"""
CivicPulse - Indian Municipal Grievance Synthetic & Real-World Dataset Generator
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Generates a stratified 1,500-row dataset modeled on CPGRAMS, Swachhata App,
MCD/BBMP civic portals, and NYC 311 schema. Includes CLI flag '--use-external-csv'
to load and map arbitrary Kaggle/HuggingFace datasets into the standard CivicPulse schema.
"""

import os
import sys
import csv
import random
import argparse
from datetime import datetime, timedelta

# Target Department Classes (5 Municipal Sectors)
DEPARTMENTS = ["WATER", "ROADS", "ELECTRICAL", "SANITATION", "HEALTH"]

# Indian Municipal Wards & Real Landmarks
WARDS_AND_LANDMARKS = [
    ("Ward 04 - Civil Lines", ["near Civil Hospital Gate 2", "behind Govt Girls Senior Secondary School", "adjacent to District Court Complex", "near Officers Colony Park"]),
    ("Ward 11 - Karol Bagh", ["Ajmal Khan Road Market", "near Metro Pillar 142", "Gali No. 6 near Community Centre", "opp. Sarvodaya Vidyalaya"]),
    ("Ward 19 - Rohini Sector 9", ["near DDA Community Hall", "Main Ring Road Service Lane", "near Mother Dairy Booth", "behind Sector 9 Primary Health Centre"]),
    ("Ward 27 - Sadar Bazaar", ["near Qutub Road Crossing", "Bara Hindu Rao Chowk", "Gali Chamrewali", "opp. Municipal Dispensary"]),
    ("Ward 35 - Indiranagar", ["100 Feet Road Junction", "12th Main near ESI Hospital", "near BDA Complex", "behind Cauvery Water Tank"]),
    ("Ward 42 - Koramangala 4th Block", ["near St. John's Medical College Gate", "80 Feet Road junction", "near Sony World Signal", "adjacent to BBMP Ward Office"]),
    ("Ward 51 - Jayanagar 7th Block", ["near National College Metro", "opp. Shanti Sagar Hotel", "behind Jayanagar General Hospital", "near 4th T Block BBMP Park"]),
    ("Ward 63 - Whitefield IT Corridor", ["near ITPL Main Gate", "Hope Farm Junction", "Varthur Lake Bypass Road", "near Govt Kannada Model School"]),
    ("Ward 72 - Dwarka Sector 12", ["near Sector 12 Metro Station", "opp. Ayushman Hospital", "near Govt Model Co-ed School", "behind DDA Market Complex"]),
    ("Ward 84 - Chandni Chowk", ["near Town Hall", "Fatehpuri Masjid Road", "opp. Nai Sarak Entry", "near Katra Neel Crossing"]),
    ("Ward 91 - Lajpat Nagar IV", ["near Amar Colony Police Station", "Dayanand Colony Market", "behind Govt Boys High School", "near Moolchand Underpass"]),
    ("Ward 105 - Andheri East", ["Chakala Metro Station Gate 3", "near Holy Spirit Hospital", "MIDC Central Road", "behind Municipal School"]),
    ("Ward 118 - Dadar West", ["near Shivaji Park Gate 4", "Ranade Road Junction", "opp. Plaza Cinema", "near Shardashram School"]),
    ("Ward 126 - Salt Lake Sector V", ["near Webel More Crossing", "College More Technopolis", "behind Salt Lake Sub-Divisional Hospital", "near Bidhannagar College"]),
    ("Ward 140 - T. Nagar", ["near Panagal Park", "Usman Road Flyover Service Lane", "opp. T. Nagar Municipal High School", "near Ranganathan Street Entry"])
]

# Domain-specific Indian Civic Complaint Templates
TEMPLATES = {
    "WATER": [
        "Potable drinking water pipeline burst open and clean municipal water is gushing out on the road {landmark}. Road is flooded and water pressure is completely zero in nearby houses since {time_duration}.",
        "Severely contaminated dirty black water coming from municipal supply taps smelling foul like sewage in {ward} {landmark}. Children falling sick after consuming tap water. Urgent testing required.",
        "Underground main water distribution pipe cracked causing heavy waterlogging and complete water supply stoppage for over 400 households in {ward}. Handpumps are also dysfunctional.",
        "Sewage pipeline leaking directly into drinking water pipeline {landmark}. Extremely hazardous foul odor and turbid water coming from all taps since {time_duration}.",
        "Water tanker supply has not arrived for {time_duration} in {ward} despite multiple token bookings. Handpump on gali corner is broken and residents have no water for basic sanitation.",
        "Low water pressure and erratic water timings in {ward}. Tap water runs for barely 15 minutes at 4:30 AM with murky brown sediment {landmark}.",
        "Water booster pump station valve damaged at {landmark}. Massive leakage causing local flood on main road and zero pressure in entire block.",
        "Illegal commercial water tanker mafia tampering with main municipal pipeline {landmark}, causing sudden water cut in residential apartments for {time_duration}.",
        "Community handpump handle completely broken and rusted at {landmark}. Poor families and laborers unable to fetch drinking water in peak summer heat.",
        "Open storm water drain overflowing and backflowing into residential ground floor basements {landmark} after brief rain shower."
    ],
    "ROADS": [
        "Massive crater-sized pothole measuring 4 feet wide and 8 inches deep on the main road {landmark}. Two-wheeler riders and school auto rickshaws losing balance daily.",
        "Major road cave-in and sinkhole formed after pipeline trenching work {landmark}. Vehicle wheels getting stuck, severe traffic congestion and imminent fatal accident hazard.",
        "Asphalt surface completely eroded on busy bus route in {ward}. Flying gravel, dangerous loose stones, and deep ruts creating fatal skidding hazard for motorcyclists.",
        "Illegal speed breaker constructed without municipal permission or reflective zebra paint {landmark}. Vehicles bottoming out and elderly passengers suffering spinal jerks.",
        "Underpass severely waterlogged with 3 feet of water {landmark}. Cars stalled and pedestrian walkway completely impassable. High risk of vehicle drowning.",
        "Concrete road slab sunken near stormwater drain {landmark}. Iron reinforcement rebars exposed and piercing vehicle tires. Urgent bituminous patch needed.",
        "Road dug up by telecom company {time_duration} ago and left abandoned without restoration {landmark}. Entire carriage lane blocked with debris and mud.",
        "Missing iron grating over road trench {landmark}. Deep trench left completely unbarricaded with zero warning signs or hazard tape.",
        "Footpath paving tiles broken and completely dislodged outside {landmark}. Pedestrians, elderly citizens, and visually impaired persons tripping and injuring knees.",
        "Flyover expansion joint gap widened dangerously on highway stretch {landmark}. Heavy metallic thudding sound and vibration when buses cross."
    ],
    "ELECTRICAL": [
        "High voltage 11kV electrical wire snapped and hanging loose just 4 feet above ground level {landmark}. Live current sparking intermittently, extreme fatal electrocution hazard!",
        "Distribution transformer sparking violently with loud explosive popping sounds and heavy black toxic smoke emitting {landmark}. Residents terrified of fire outbreak.",
        "All streetlights completely dysfunctional and pitch dark for a 2-kilometer stretch {landmark}. Dark stretch has become accident hotspot and unsafe for women returning home after sunset.",
        "Streetlight iron feeder pillar box open with bare live copper terminals and uninsulated wires exposed {landmark} at child-reachable height during rainy weather.",
        "Overhead low-tension electric cables dangling into tree branches and touching iron tin roof of tea stall {landmark}. Visible sparks whenever wind blows.",
        "Streetlight pole knocked down by heavy truck {time_duration} ago {landmark}. Damaged pole lying on pedestrian footpath with live wiring still attached.",
        "Frequent low voltage and sudden extreme voltage surges up to 320V in {ward} {landmark}. Home appliances, refrigerators, and fans burning out.",
        "High-capacity electric cable joint box smoking and smoldering on the sidewalk {landmark}. Foul burning plastic stench spreading into nearby residences.",
        "Streetlight stays switched on throughout the bright afternoon but turns pitch black every night at 7 PM {landmark} due to faulty photocell timer.",
        "Unauthorized high-voltage wire hooks (katiya) tapped onto main distribution line {landmark}, causing sparking and risk of transformer overload blast."
    ],
    "SANITATION": [
        "Enormous overflowing garbage dump (dhalao) spilling across half the main carriage road {landmark}. Stray cows, dogs, and pigs scattering plastic bags everywhere.",
        "Municipal solid waste collection vehicle has not visited {ward} for {time_duration}. Domestic wet waste accumulating in open heaps and rotting in summer heat.",
        "Open nallah clogged with plastic bags, silt, and thermocol debris {landmark}. Sludge overflowing onto pedestrian lane and emitting intolerable stench.",
        "Dead animal carcass (stray dog/bovine) decomposing on roadside {landmark} for over 48 hours. Swarms of flies, maggots, and severe biohazard health risk.",
        "Illegal midnight dumping of construction & demolition (C&D) debris and concrete rubble blocking storm drain {landmark}.",
        "Public toilet complex (Sulabh Shauchalaya) in {ward} {landmark} completely choked with feces. Zero running water, broken taps, doors vandalized, unusable.",
        "Sweepers dumping collected road dust, dry leaves, and municipal garbage straight into open stormwater drains {landmark} instead of secondary compactor bins.",
        "Green waste, pruned tree branches, and horticulture refuse dumped on footpath {landmark} for {time_duration}, forcing pedestrians onto dangerous traffic lane.",
        "Biomedical waste, used syringes, saline tubes, and blood-stained gauze found dumped in public dustbin {landmark} without segregation.",
        "Open drain grates clogged with vegetable market waste {landmark}. Black sewer muck bubbling up onto the street."
    ],
    "HEALTH": [
        "Severe dengue and chikungunya outbreak risk: Massive stagnant water pool breeding lakhs of mosquito larvae {landmark}. Multiple hospital admissions reported in neighborhood.",
        "Aggressive pack of 8-10 stray dogs terrorizing residents {landmark}. Three school children and an elderly morning walker bitten this week. Urgent rabies anti-rabies vaccination & animal birth control team needed.",
        "Stagnant sewage water accumulated in empty municipal plot {landmark} for {time_duration}. Cloud of mosquitoes entering homes, dengue cases rising rapidly.",
        "Stray cattle (cows and bulls) roaming freely and fighting aggressively in the middle of main intersection {landmark}. Two motorcyclists severely injured.",
        "Unhygienic open meat and poultry slaughtering on roadside with blood and offal draining into open street gutter {landmark}. Unbearable stench and vulture menace.",
        "Suspected waterborne jaundice and gastroenteritis cluster in {ward} {landmark}. Over 12 residents admitted to civil hospital due to contaminated municipal pipe.",
        "Dense breeding of malaria vectors in abandoned municipal fountain / decorative pool {landmark}. Water is pitch green with active mosquito pupae.",
        "Dead rodents and toxic chemical discharge from unauthorized electroplating unit in residential lane {landmark}. Residents experiencing breathing distress.",
        "No vector control fogging or anti-larval chemical spraying conducted in {ward} for over {time_duration} despite municipal health advisory.",
        "Swarm of aggressive stray dogs chasing two-wheelers and delivery riders at night {landmark}, causing serious head injuries and fractures."
    ]
}

# Ambiguous Multi-Department Complaints (Cross-domain interactions)
AMBIGUOUS_COMPLAINTS = [
    ("WATER", "High voltage underground electrical cable severed during JCB excavation for water pipeline repair {landmark}. Water flooding the open electrical trench with sparking risk!"),
    ("ROADS", "Huge water pipeline burst has caused massive road cave-in and sinkhole {landmark}. Submerged crater is completely invisible to speeding night traffic."),
    ("ELECTRICAL", "Live overhead power cable snapped and fell directly into waterlogged pothole on road {landmark}. Pedestrians risk instantaneous electrocution."),
    ("SANITATION", "Overflowing open nallah has submerged the entire road and flooded the ground-level electrical distribution box {landmark} with foul black sewage."),
    ("HEALTH", "Massive open garbage dump rotting {landmark} has blocked storm drain, causing stagnant wastewater where dengue mosquitoes are breeding and stray dogs are attacking pedestrians."),
    ("WATER", "Sewage line overflow mixed with road cave-in near school gate {landmark}. Foul liquid entering classrooms and road impassable for school buses."),
    ("ELECTRICAL", "Transformer sparking right above an overflowing open garbage vat {landmark}. Burning sparks falling onto dry cardboard and waste heaps with imminent fire outbreak."),
    ("ROADS", "Uncollected construction debris and broken streetlight pole blocking road {landmark}. Dark stretch and rubble causing multiple bike accidents nightly."),
    ("SANITATION", "Dead animal carcass thrown into drinking water pipeline inspection chamber {landmark}. Entire colony water supply contaminated with unbearable stench."),
    ("HEALTH", "Waterlogging in deep potholes on main road {landmark} creating mosquito breeding pools while stray cattle sit in the water causing severe road traffic blocks.")
]

# Short / Noisy / Edge Case Complaints to test Data Quality Gate
NOISY_EDGE_CASES = [
    ("WATER", "no water in taps since 3 days pls help", "LOW", 0),
    ("ROADS", "big pothole fix it fast", "LOW", 0),
    ("ELECTRICAL", "lights off in gali", "LOW", 0),
    ("SANITATION", "kachra everywhere", "LOW", 0),
    ("HEALTH", "mosquitoes very high here", "LOW", 0),
    ("ELECTRICAL", "urgent power hazard help!!", "MEDIUM", 0),
    ("WATER", "pani nahi aa raha ward 14", "LOW", 0),
    ("ROADS", "road broken near school", "MEDIUM", 0),
    ("SANITATION", "garbage truck not coming", "LOW", 0),
    ("HEALTH", "dog bite incident hospital", "HIGH", 0)
]

TIME_DURATIONS = ["2 days", "4 days", "5 days", "1 week", "10 days", "2 weeks", "3 weeks"]

def determine_severity_and_hazard(text: str, dept: str) -> tuple[str, int]:
    """Deterministically calculate ground-truth severity based on safety keywords."""
    text_lower = text.lower()
    
    # Critical Life Safety Hazards
    critical_keywords = [
        "snapped", "live wire", "sparking", "electrocution", "11kv", "sinkhole",
        "cave-in", "contaminated", "sewage mixed", "explosive", "blast", "gas leak"
    ]
    # High Priority Issues
    high_keywords = [
        "dengue", "larvae", "dog bite", "rabies", "open manhole", "carcass",
        "hospital", "school", "waterlogged", "underpass", "biohazard"
    ]
    # Medium Priority Issues
    medium_keywords = [
        "overflowing", "pothole", "garbage dump", "clogged", "broken tiles",
        "low voltage", "stray cattle", "pipeline burst"
    ]
    
    if any(k in text_lower for k in critical_keywords):
        return "CRITICAL", random.randint(75, 150)
    elif any(k in text_lower for k in high_keywords):
        return "HIGH", random.randint(35, 75)
    elif any(k in text_lower for k in medium_keywords):
        return "MEDIUM", random.randint(10, 35)
    else:
        return "LOW", random.randint(1, 15)

def generate_synthetic_dataset(total_rows: int = 1500, output_csv: str = "civic_complaints_india.csv") -> str:
    """Generates 1,500 highly realistic, stratified civic complaint records."""
    random.seed(42)
    rows_per_dept = total_rows // len(DEPARTMENTS) # 300 per dept
    
    records = []
    ticket_counter = 1
    
    base_time = datetime(2026, 10, 15, 8, 30, 0)
    
    for dept in DEPARTMENTS:
        dept_records = []
        
        # 1. Standard Domain Complaints (~260 per dept)
        standard_count = rows_per_dept - 30 - 10 # 260
        for _ in range(standard_count):
            ward, landmarks = random.choice(WARDS_AND_LANDMARKS)
            landmark = random.choice(landmarks)
            time_dur = random.choice(TIME_DURATIONS)
            template = random.choice(TEMPLATES[dept])
            
            raw_text = template.format(ward=ward, landmark=landmark, time_duration=time_dur)
            severity, upvotes = determine_severity_and_hazard(raw_text, dept)
            
            # Timestamp jitter over last 30 days
            delta_seconds = random.randint(0, 30 * 86400)
            timestamp = (base_time + timedelta(seconds=delta_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            
            dept_records.append({
                "complaint_id": f"CP-2026-{ticket_counter:04d}",
                "timestamp": timestamp,
                "ward_location": f"{ward} ({landmark})",
                "raw_text": raw_text,
                "citizen_upvotes": upvotes,
                "true_department": dept,
                "base_severity_ground_truth": severity,
                "is_ambiguous_edge_case": 0
            })
            ticket_counter += 1
            
        # 2. Ambiguous Multi-Department Complaints (30 per dept)
        for _ in range(30):
            ward, landmarks = random.choice(WARDS_AND_LANDMARKS)
            landmark = random.choice(landmarks)
            
            matching_ambiguous = [item for item in AMBIGUOUS_COMPLAINTS if item[0] == dept]
            if not matching_ambiguous:
                matching_ambiguous = AMBIGUOUS_COMPLAINTS
            _, amb_template = random.choice(matching_ambiguous)
            raw_text = amb_template.format(ward=ward, landmark=landmark)
            
            severity, upvotes = determine_severity_and_hazard(raw_text, dept)
            delta_seconds = random.randint(0, 30 * 86400)
            timestamp = (base_time + timedelta(seconds=delta_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            
            dept_records.append({
                "complaint_id": f"CP-2026-{ticket_counter:04d}",
                "timestamp": timestamp,
                "ward_location": f"{ward} ({landmark})",
                "raw_text": raw_text,
                "citizen_upvotes": upvotes + 15, # ambiguous often attracts more citizen attention
                "true_department": dept,
                "base_severity_ground_truth": severity,
                "is_ambiguous_edge_case": 1
            })
            ticket_counter += 1
            
        # 3. Short / Noisy Edge Cases (10 per dept)
        for _ in range(10):
            ward, landmarks = random.choice(WARDS_AND_LANDMARKS)
            landmark = random.choice(landmarks)
            matching_noisy = [item for item in NOISY_EDGE_CASES if item[0] == dept]
            if matching_noisy:
                _, noisy_text, sev, upv = random.choice(matching_noisy)
            else:
                noisy_text = f"Urgent municipal complaint for {dept} in {ward}."
                sev, upv = "LOW", 2
                
            delta_seconds = random.randint(0, 30 * 86400)
            timestamp = (base_time + timedelta(seconds=delta_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            
            dept_records.append({
                "complaint_id": f"CP-2026-{ticket_counter:04d}",
                "timestamp": timestamp,
                "ward_location": f"{ward} ({landmark})",
                "raw_text": f"{noisy_text} {landmark}.",
                "citizen_upvotes": upv,
                "true_department": dept,
                "base_severity_ground_truth": sev,
                "is_ambiguous_edge_case": 0
            })
            ticket_counter += 1
            
        records.extend(dept_records)
        
    # Shuffle while maintaining determinism
    random.shuffle(records)
    
    # Write to CSV
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    fieldnames = [
        "complaint_id", "timestamp", "ward_location", "raw_text",
        "citizen_upvotes", "true_department", "base_severity_ground_truth",
        "is_ambiguous_edge_case"
    ]
    
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    print(f"[DATASET GENERATED] Total Rows: {len(records)} -> Saved to: {output_csv}")
    print(f"Class Breakdown:")
    for d in DEPARTMENTS:
        count = sum(1 for r in records if r["true_department"] == d)
        print(f"  - {d:12s}: {count} records ({count/len(records)*100:.1f}%)")
    amb_count = sum(1 for r in records if r["is_ambiguous_edge_case"] == 1)
    print(f"Ambiguous Edge Cases: {amb_count} ({amb_count/len(records)*100:.1f}%)")
    return output_csv

def load_external_csv(external_path: str, output_csv: str = "civic_complaints_india.csv") -> str:
    """
    Ingests and maps an external civic grievance CSV (e.g. from Kaggle/HuggingFace/NYC311/CPGRAMS)
    into the standard CivicPulse 8-column schema.
    """
    if not os.path.exists(external_path):
        raise FileNotFoundError(f"External CSV file not found: {external_path}")
        
    print(f"[EXTERNAL CSV] Loading: {external_path}")
    mapped_records = []
    
    with open(external_path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # Attempt to find relevant text column
            text_candidates = ["description", "complaint_text", "text", "complaint", "summary", "detail"]
            raw_text = next((row[c] for c in text_candidates if c in row and row[c]), "Civic grievance recorded.")
            
            # Attempt to find department/category column
            dept_candidates = ["category", "department", "agency", "type", "complaint_type"]
            raw_dept = next((row[c] for c in dept_candidates if c in row and row[c]), "").upper()
            
            # Map raw department to CivicPulse 5 classes
            if any(k in raw_dept for k in ["WATER", "SEWER", "SEWAGE", "PIPE", "DRAIN"]):
                dept = "WATER"
            elif any(k in raw_dept for k in ["ROAD", "POTHOLE", "STREET", "PAVEMENT", "TRAFFIC"]):
                dept = "ROADS"
            elif any(k in raw_dept for k in ["ELECTRIC", "LIGHT", "POWER", "WIRE", "LAMP"]):
                dept = "ELECTRICAL"
            elif any(k in raw_dept for k in ["SANITA", "GARBAGE", "WASTE", "CLEAN", "TRASH", "SWEEP"]):
                dept = "SANITATION"
            elif any(k in raw_dept for k in ["HEALTH", "DOG", "MOSQUITO", "CLINIC", "HOSPITAL", "ANIMAL"]):
                dept = "HEALTH"
            else:
                dept = random.choice(DEPARTMENTS)
                
            ward = row.get("ward", row.get("location", row.get("borough", "Ward 14 - Municipal Zone")))
            upvotes = int(row.get("upvotes", row.get("votes", random.randint(0, 50))))
            sev, _ = determine_severity_and_hazard(raw_text, dept)
            
            mapped_records.append({
                "complaint_id": f"CP-EXT-{i:05d}",
                "timestamp": row.get("timestamp", row.get("created_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                "ward_location": ward,
                "raw_text": raw_text,
                "citizen_upvotes": upvotes,
                "true_department": dept,
                "base_severity_ground_truth": sev,
                "is_ambiguous_edge_case": 0
            })
            
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "complaint_id", "timestamp", "ward_location", "raw_text",
            "citizen_upvotes", "true_department", "base_severity_ground_truth",
            "is_ambiguous_edge_case"
        ])
        writer.writeheader()
        writer.writerows(mapped_records)
        
    print(f"[MAPPED EXTERNAL CSV] Loaded {len(mapped_records)} records -> Saved to {output_csv}")
    return output_csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CivicPulse Dataset Generator / Ingester")
    parser.add_argument("--rows", type=int, default=1500, help="Number of synthetic rows to generate (default: 1500)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--use-external-csv", type=str, default=None, help="Path to external Kaggle/HuggingFace CSV to map")
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = args.output if args.output else os.path.join(script_dir, "civic_complaints_india.csv")
    
    if args.use_external_csv:
        load_external_csv(args.use_external_csv, output_path)
    else:
        generate_synthetic_dataset(total_rows=args.rows, output_csv=output_path)
