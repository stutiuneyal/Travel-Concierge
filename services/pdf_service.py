from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright

from config.settings import settings
from services.storage_service import make_file_path


env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml']),
)

def enrich_hotels(payload: dict) -> dict:
    hotels = payload.get("hotels", [])
    hotel_insights = payload.get("hotel_insights", {})

    enriched = []
    for hotel in hotels:
        name = hotel.get("name") or hotel.get("hotel_name")

        enriched.append({
            **hotel,
            "address": hotel.get("address") or hotel.get("formatted_address"),
            "rating": hotel.get("rating"),
            "price": hotel.get("price") or hotel.get("amount"),
            "currency": hotel.get("currency"),
        })

    payload["hotels"] = enriched
    return payload

async def generate_itinerary_pdf(payload: dict, session_id: str) -> dict:
    payload = enrich_hotels(payload)
    template = env.get_template('itinerary_pdf.html')
    html = template.render(payload=payload)

    html_path = make_file_path(f'itinerary_{session_id}.html')
    pdf_path = make_file_path(f'itinerary_{session_id}.pdf')

    html_path.write_text(html, encoding='utf-8')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f'file://{html_path.resolve()}')
        await page.pdf(path=str(pdf_path), format='A4', print_background=True)
        await browser.close()

    return {
        'pdf_path': str(pdf_path),
        'pdf_url': f"{settings.APP_BASE_URL}/downloads/{pdf_path.name}",
    }
