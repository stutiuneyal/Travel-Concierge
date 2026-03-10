from states.graph_state import GraphState
from services.pdf_service import generate_itinerary_pdf


async def run_pdf(state: GraphState) -> GraphState:
    if not state.get('pdf_requested'):
        return {
            'results': [{'source': 'pdf', 'result': 'PDF generation was not requested.'}],
        }

    session_id = state.get('session_id', 'default')
    payload = {
        'trip_context': state.get('trip_context', {}),
        'flights': state.get('flights', []),
        'flight_insights': state.get('flight_insights', {}),
        'hotels': state.get('hotels', []),
        'hotel_insights': state.get('hotel_insights', {}),
        'weather_summary': state.get('weather_summary', {}),
        'weather_insights': state.get('weather_insights', {}),
        'places': state.get('places', []),
        'places_insights': state.get('places_insights', {}),
        'budget_summary': state.get('budget_summary', {}),
        'itinerary': state.get('itinerary', {}),
        'visa_info': state.get('visa_info', {}),
    }
    pdf_meta = await generate_itinerary_pdf(payload, session_id)
    return {
        'pdf_path': pdf_meta['pdf_path'],
        'pdf_url': pdf_meta['pdf_url'],
        'results': [{'source': 'pdf', 'result': f"PDF generated successfully: {pdf_meta['pdf_url']}"}],
    }
