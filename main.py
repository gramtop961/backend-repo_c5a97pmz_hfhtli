import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from database import db, create_document, get_documents
from schemas import Service, Package, Booking, Inquiry, Special, FAQ

app = FastAPI(title="Laserontharing Almere API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Laserontharing Almere Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# In-memory defaults for catalog to seed UI if DB empty (read-only fallback)
DEFAULT_SERVICES: List[Service] = [
    Service(name="Oksels", category="Oksels", code="OKS", price_single=39, duration_min=15),
    Service(name="Bikinilijn klein", category="Bikinilijn", code="BIK-K", price_single=49, duration_min=20),
    Service(name="Bikinilijn groot", category="Bikinilijn", code="BIK-G", price_single=69, duration_min=25),
    Service(name="Onderbenen", category="Benen", code="BEN-OND", price_single=79, duration_min=30),
    Service(name="Bovenbenen", category="Benen", code="BEN-BOV", price_single=89, duration_min=35),
    Service(name="Hele benen", category="Benen", code="BEN-HELE", price_single=129, duration_min=55),
    Service(name="Bovenlip", category="Gezicht", code="GEZ-LIP", price_single=29, duration_min=10),
    Service(name="Kin", category="Gezicht", code="GEZ-KIN", price_single=29, duration_min=10),
    Service(name="Gehele gelaat", category="Gezicht", code="GEZ-FULL", price_single=79, duration_min=35),
    Service(name="Onderarmen", category="Armen", code="ARM-OND", price_single=59, duration_min=25),
    Service(name="Hele armen", category="Armen", code="ARM-HELE", price_single=89, duration_min=35),
]

DEFAULT_PACKAGES: List[Package] = [
    Package(
        title="Full body",
        description="Hele armen + oksels + buik + hele benen + bikinilijn klein",
        code="FB-STD",
        included_codes=["ARM-HELE", "OKS", "BEN-HELE", "BIK-K"],
        price_single=279,
        promo_6_plus_2=True,
    ),
    Package(
        title="Full body + gelaat",
        description="Full body met gehele gelaat als luxere variant",
        code="FB-LUX",
        included_codes=["ARM-HELE", "OKS", "BEN-HELE", "BIK-K", "GEZ-FULL"],
        price_single=329,
        promo_6_plus_2=True,
    ),
]

# Public endpoints
@app.get("/api/services", response_model=List[Service])
def list_services():
    try:
        docs = get_documents("service")
        if docs:
            # Map DB docs to Pydantic model
            return [Service(**{k: v for k, v in d.items() if k in Service.model_fields}) for d in docs]
    except Exception:
        pass
    return DEFAULT_SERVICES

@app.get("/api/packages", response_model=List[Package])
def list_packages():
    try:
        docs = get_documents("package")
        if docs:
            return [Package(**{k: v for k, v in d.items() if k in Package.model_fields}) for d in docs]
    except Exception:
        pass
    return DEFAULT_PACKAGES

class PriceCalcRequest(BaseModel):
    selected_codes: List[str]
    sessions: int = 1  # if 8 with 6+2 promo, charge for 6 of package items

class PriceCalcResponse(BaseModel):
    items: List[Dict]
    subtotal: float
    promo_label: Optional[str] = None
    total: float

@app.post("/api/calc", response_model=PriceCalcResponse)
def calculate_price(payload: PriceCalcRequest):
    # Build catalog map
    services = {s.code: s for s in list_services()}
    packages = list_packages()

    items = []
    subtotal = 0.0

    for code in payload.selected_codes:
        if code in services:
            price = services[code].price_single
            items.append({"code": code, "name": services[code].name, "price": price})
            subtotal += price
        else:
            # Try package code
            pkg = next((p for p in packages if p.code == code), None)
            if pkg:
                price = pkg.price_single
                items.append({"code": code, "name": pkg.title, "price": price, "package": True})
                subtotal += price

    promo_label = None
    total = subtotal

    # Apply 6+2 promo if sessions == 8 and items include eligible services/packages
    if payload.sessions == 8:
        promo_label = "6 + 2 gratis"
        # For simplicity: charge 75% of subtotal (pay 6 of 8)
        total = round(subtotal * 0.75, 2)

    return PriceCalcResponse(items=items, subtotal=round(subtotal, 2), promo_label=promo_label, total=round(total, 2))

class BookingRequest(Booking):
    pass

@app.post("/api/book")
def create_booking(payload: BookingRequest):
    try:
        booking_id = create_document("booking", payload)
        return {"ok": True, "id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class InquiryRequest(Inquiry):
    pass

@app.post("/api/contact")
def create_inquiry(payload: InquiryRequest):
    try:
        inquiry_id = create_document("inquiry", payload)
        return {"ok": True, "id": inquiry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faqs", response_model=List[FAQ])
def list_faqs():
    try:
        docs = get_documents("faq")
        if docs:
            return [FAQ(**{k: v for k, v in d.items() if k in FAQ.model_fields}) for d in docs]
    except Exception:
        pass
    # Default FAQ content
    return [
        FAQ(question="Doet laserontharing pijn?", answer="De meeste klanten ervaren slechts milde prikkels. Met koeling is het goed te doen."),
        FAQ(question="Hoeveel behandelingen heb ik nodig?", answer="Gemiddeld 6-8 sessies voor optimaal resultaat; daarom onze 6 + 2 deal."),
        FAQ(question="Voor wie is het geschikt?", answer="De nieuwste technologie werkt voor de meeste huid- en haartypen. Tijdens de intake adviseren we persoonlijk."),
        FAQ(question="Voorzorg / nazorg?", answer="Vermijd zonnen 48 uur voor en na. Gebruik SPF en volg ons nazorgadvies."),
    ]

# Expose schema for admin tools
@app.get("/schema")
def get_schema():
    return {
        "service": Service.model_json_schema(),
        "package": Package.model_json_schema(),
        "booking": Booking.model_json_schema(),
        "inquiry": Inquiry.model_json_schema(),
        "special": Special.model_json_schema(),
        "faq": FAQ.model_json_schema(),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
