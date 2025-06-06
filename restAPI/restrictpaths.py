from django.http import HttpResponseForbidden
from ipaddress import ip_address, ip_network

class RestrictPathsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define your local network (e.g., 10.20.30.0/24)
        self.local_network = ip_network('10.20.30.0/24')
        # Define restricted paths
        self.restricted_paths = [
            '/admin/',
            '/schema/',
            '/schema/swagger-ui/'
        ]

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.restricted_paths):
            # Prefer X-Forwarded-For if present (for use behind a proxy)
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            try:
                if ip_address(client_ip) not in self.local_network:
                    return HttpResponseForbidden("Access to this path is restricted to the local network.")
            except ValueError:
                return HttpResponseForbidden("Invalid IP address.")
        return self.get_response(request)