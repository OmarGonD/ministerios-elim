from iglesias.models import IglesiaPage
from django.conf import settings

class ChurchSubdomainMiddleware:
    """
    Middleware to serve an IglesiaPage when a church's slug is used as a subdomain.
    Example: elim-buenos-aires.localhost:8000 serving the church page content at root.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0] # Remove port
        
        # Simple subdomain extraction logic
        # Assumes format: subdomain.domain.tld or subdomain.localhost
        parts = host.split('.')
        
        # Skip if IP address or localhost without subdomain
        if len(parts) > 1 and parts[0] != 'www' and not host.replace('.', '').isdigit() and 'localhost' in host:
             # Logic for localhost testing: [slug].localhost
             subdomain = parts[0]
        elif len(parts) > 2:
             # Logic for production: [slug].domain.com
             subdomain = parts[0]
        else:
            subdomain = None

        if subdomain:
            # print(f"DEBUG: Subdomain detected: {subdomain}")
            try:
                # Try to find the church with this slug
                church = IglesiaPage.objects.live().filter(slug=subdomain).first()
                
                if church:
                    # print(f"DEBUG: Found church: {church.title}")
                    request.church_page = church
                    
                    # If visiting the root of the subdomain, serve the church page
                    if request.path == '/':
                        # print("DEBUG: Serving church page at root")
                        return church.serve(request)
            except Exception as e:
                print(f"DEBUG: Middleware error: {e}")
                pass


        return self.get_response(request)
