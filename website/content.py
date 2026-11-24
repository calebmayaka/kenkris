"""Fixed page content that changes rarely; edit here and redeploy.

Content that staff update often (contact details, stats, courses) lives in
the database and is edited in the Django admin instead.
"""

TRACKER_STEPS = [
    {"label": "Booked", "sub": "Bill of lading issued", "time": "Day 1", "state": "done"},
    {"label": "In Transit", "sub": "Vessel en route to Mombasa", "time": "Day 14", "state": "done"},
    {"label": "Customs Clearance", "sub": "Declaration lodged with KRA", "time": "Day 21", "state": "active"},
    {"label": "Out for Delivery", "sub": "Nairobi warehouse", "time": "Day 23 (est.)", "state": "pending"},
]

STRIP_CHIPS = ["Customs Brokerage", "Freight Forwarding", "Cargo Handling", "Goods in Transit", "Trade Training"]

SERVICES = [
    {"icon": "📋", "title": "Customs Brokerage",
     "desc": "Full declaration, duty assessment and clearance with KRA and border agencies.",
     "tag": "IDF / EAC-CD1 / VERIFICATION"},
    {"icon": "🚢", "title": "Freight Forwarding",
     "desc": "Sea, air and road freight booked and tracked from origin to final delivery.",
     "tag": "FCL / LCL / AIR"},
    {"icon": "📦", "title": "Cargo Handling",
     "desc": "Port handling, warehousing and last-mile transport across the region.",
     "tag": "PORT / WAREHOUSE / TRANSPORT"},
]

JOURNEY_STEPS = [
    {"num": "1", "title": "Book & Document", "desc": "Share invoice, packing list and bill of lading."},
    {"num": "2", "title": "Declare", "desc": "We lodge your customs entry and assess duty."},
    {"num": "3", "title": "Verify & Clear", "desc": "Physical or scanner verification with KRA."},
    {"num": "4", "title": "Transit", "desc": "Bonded movement to inland or cross-border markets."},
    {"num": "5", "title": "Deliver", "desc": "Cargo dropped at your warehouse door."},
]

FEATURES = [
    {"icon": "🎓", "title": "Customs Compliance", "desc": "Understand HS codes, valuation and duty exposure."},
    {"icon": "📑", "title": "Documentation", "desc": "Get shipping paperwork right the first time."},
    {"icon": "🌍", "title": "Regional Trade", "desc": "Navigate EAC and COMESA trade rules."},
]

WHY_POINTS = [
    "Licensed customs agents with direct KRA iCMS access",
    "Real-time shipment tracking from booking to delivery",
    "Bonded transit for landlocked destination markets",
    "In-house trade training for your own staff",
]

CORRIDORS = [
    {"city": "Mombasa", "role": "Port of Entry", "desc": "Sea freight clearance and port handling."},
    {"city": "Nairobi", "role": "Head Office", "desc": "Customs brokerage and inland warehousing."},
    {"city": "Kampala", "role": "Transit Corridor", "desc": "Bonded transit to Uganda markets."},
    {"city": "Kigali", "role": "Transit Corridor", "desc": "Cross-border cargo to Rwanda."},
]

DESTINATIONS = ["Uganda", "Rwanda", "Burundi", "DR Congo", "South Sudan", "Tanzania"]

REQUIREMENTS = [
    {"icon": "🧾", "title": "Commercial Invoice", "desc": "Signed, itemised invoice from the supplier."},
    {"icon": "📦", "title": "Packing List", "desc": "Weights, dimensions and package count."},
    {"icon": "🚢", "title": "Bill of Lading / Airway Bill", "desc": "Original or telex-released transport document."},
    {"icon": "📄", "title": "Certificate of Origin", "desc": "Required for preferential duty rates."},
    {"icon": "🪪", "title": "PIN & IDF Number", "desc": "Importer PIN certificate and import declaration form."},
]
