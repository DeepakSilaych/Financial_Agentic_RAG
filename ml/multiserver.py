import pathway as pw
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.servers import DocumentStoreServer
import aiohttp
import aiohttp_cors
import random
import requests
import json
import os
import multiprocessing

class MultiDocumentServer():
    def __init__(
        self,
        host: str,
        proxy_port: int,
        server1_port: int,
        server2_port: int,
        document_store1: DocumentStore,
        document_store2: DocumentStore,
        server1_cache_dir: str,
        server2_cache_dir: str,
    ):
        self.host = host
        self.proxy_port = proxy_port
        self.server1_port = server1_port
        self.server2_port = server2_port
        self.document_store1 = document_store1
        self.document_store2 = document_store2
        self.server1_cache_dir = server1_cache_dir
        self.server2_cache_dir = server2_cache_dir

    def check_server_status(self, url):
        stat_url = url + "/v1/statistics"
        try:
            response = requests.post(
                stat_url,
                json={},
                headers={"Content-Type": "application/json"},
                timeout=2,
            )
            responses = response.json()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


    async def handle_request(self, request):
        server1_url = f"http://{self.host}:{self.server1_port}"
        server2_url = f"http://{self.host}:{self.server2_port}"

        server1_status = self.check_server_status(server1_url)
        server2_status = self.check_server_status(server2_url)

        if server1_status and server2_status:
            print("Both servers are up")
            remote_url = random.choice([server1_url, server2_url]) + request.rel_url.path_qs
            print(f"Selected server: {remote_url}")
        elif server1_status:
            print("Server 1 is up")
            remote_url = server1_url + request.rel_url.path_qs
        elif server2_status:
            print("Server 2 is up")
            remote_url = server2_url + request.rel_url.path_qs
        else:
            print("Both servers are down")
            return aiohttp.web.Response(status=500, text="Both servers are down")

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            # Send the request to the remote URL using the same method
            async with session.request(request.method, remote_url) as resp:
                if resp.content_type == 'application/json':
                    response_json = await resp.json()  # Parse JSON response
                    return aiohttp.web.Response(
                        status=resp.status,
                        body=json.dumps(response_json),  # Convert dict back to string (for returning as body)
                        headers=resp.headers
                    )
                else:
                    # Handle non-JSON responses (like text, html, etc.)
                    text = await resp.text()
                    return aiohttp.web.Response(
                        status=resp.status,
                        text=text,
                        headers=resp.headers
                    )
                
    def run_server1(self):
        # Running server1 with its own cache backend in a separate process
        server1 = DocumentStoreServer(
            host=self.host,
            port=self.server1_port,
            document_store=self.document_store1,
        )

        server1.run(cache_backend=pw.persistence.Backend.filesystem(self.server1_cache_dir))

    def run_server2(self):
        # Running server1 with its own cache backend in a separate process
        server2 = DocumentStoreServer(
            host=self.host,
            port=self.server2_port,
            document_store=self.document_store2,
        )

        server2.run(cache_backend=pw.persistence.Backend.filesystem(self.server2_cache_dir))


    def run(self):
        process1 = multiprocessing.Process(target=self.run_server1)
        process2 = multiprocessing.Process(target=self.run_server2)

        # Start both processes
        process1.start()
        process2.start()

        app = aiohttp.web.Application()
        app.router.add_route('*', '/v1/statistics', self.handle_request)

        aiohttp_cors.setup(app)
        aiohttp.web.run_app(app, host=self.host, port=self.proxy_port)

        # Wait for both processes to complete
        process1.join()
        process2.join()


        

        
