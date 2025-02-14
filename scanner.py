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
        self.is_pro = False  # Pro version flag

    def set_pro_access(self, is_pro):
        self.is_pro = is_pro

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

            # Basic scan arguments - TCP Connect scan doesn't require root
            scan_args = '-sT'  

            # Enhanced scanning for pro version - include version detection
            if self.is_pro:
                scan_args = '-sT -sV'  # TCP Connect scan with version detection

            # Start the scan
            self.nm.scan(target, ports, arguments=scan_args)

            for host in self.nm.all_hosts():
                if not self.scanning:
                    break

                host_data = {
                    'host': host,
                    'status': self.nm[host].state(),
                    'ports': [],
                    'is_pro': self.is_pro
                }

                for proto in self.nm[host].all_protocols():
                    ports = self.nm[host][proto].keys()
                    for port in ports:
                        port_info = self.nm[host][proto][port]
                        port_data = {
                            'port': port,
                            'state': port_info['state'],
                            'service': port_info.get('name', ''),
                            'is_pro': self.is_pro
                        }

                        # Add extra information for pro version
                        if self.is_pro:
                            port_data.update({
                                'version': port_info.get('version', ''),
                                'product': port_info.get('product', ''),
                                'extrainfo': port_info.get('extrainfo', ''),
                                'cpe': port_info.get('cpe', '')
                            })

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