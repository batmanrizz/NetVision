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
        self.is_pro = False
        self.common_vulns = {
            21: "FTP - Potential anonymous access, clear-text authentication",
            22: "SSH - Check for outdated versions, weak ciphers",
            23: "Telnet - Clear-text protocol, susceptible to MITM",
            25: "SMTP - Check for open relay, version exploits",
            80: "HTTP - Web vulnerabilities, check SSL/TLS",
            443: "HTTPS - SSL/TLS vulnerabilities, check certificates",
            3306: "MySQL - Database access, check auth settings",
            3389: "RDP - Remote access vulnerabilities"
        }

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
            scan_args = '-sT -Pn'
            self.nm.scan(target, ports, arguments=scan_args)

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
                            'service': port_info.get('name', 'unknown'),
                            'is_pro': self.is_pro
                        }

                        if port_info['state'] == 'open':
                            if not self.is_pro and port in self.common_vulns:
                                port_data['vulnerabilities'] = {
                                    'level': 'basic',
                                    'description': self.common_vulns[port]
                                }

                        self.socketio.emit('port_data', port_data)
                        sleep(0.1)

                self.socketio.emit('host_data', host_data)

            self.socketio.emit('scan_status', {'status': 'completed'})
        except Exception as e:
            self.socketio.emit('scan_error', {'error': str(e)})
        finally:
            self.scanning = False
