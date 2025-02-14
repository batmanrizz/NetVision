import nmap
import threading
import json
import logging
from time import sleep

class NetworkScanner:
    def __init__(self, socketio):
        self.nm = nmap.PortScanner()
        self.socketio = socketio
        self.scanning = False
        self.logger = logging.getLogger(__name__)

    def start_scan(self, target, ports):
        if self.scanning:
            return
        
        self.scanning = True
        scan_thread = threading.Thread(target=self._scan_worker, args=(target, ports))
        scan_thread.daemon = True
        scan_thread.start()

    def stop_scan(self):
        self.scanning = False

    def _scan_worker(self, target, ports):
        try:
            self.socketio.emit('scan_status', {'status': 'starting'})
            
            # Start the scan
            self.nm.scan(target, ports, arguments='-sV -sS')
            
            for host in self.nm.all_hosts():
                if not self.scanning:
                    break
                
                host_data = {
                    'host': host,
                    'status': self.nm[host].state(),
                    'ports': []
                }

                for proto in self.nm[host].all_protocols():
                    ports = self.nm[host][proto].keys()
                    for port in ports:
                        port_info = self.nm[host][proto][port]
                        port_data = {
                            'port': port,
                            'state': port_info['state'],
                            'service': port_info.get('name', ''),
                            'version': port_info.get('version', '')
                        }
                        host_data['ports'].append(port_data)
                        self.socketio.emit('port_data', port_data)
                        sleep(0.1)  # Prevent flooding

                self.socketio.emit('host_data', host_data)

            self.socketio.emit('scan_status', {'status': 'completed'})
        except Exception as e:
            self.logger.error(f"Scan error: {str(e)}")
            self.socketio.emit('scan_error', {'error': str(e)})
        finally:
            self.scanning = False
