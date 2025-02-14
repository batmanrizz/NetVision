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

        # Common vulnerabilities database
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

    def _get_basic_vulnerability_info(self, port, service):
        """Get basic vulnerability information for free version"""
        if port in self.common_vulns:
            return {
                'level': 'basic',
                'description': self.common_vulns[port],
                'recommendations': ['Update to latest version', 'Configure proper authentication']
            }
        return None

    def _scan_worker(self, target, ports):
        try:
            self.socketio.emit('scan_status', {'status': 'starting'})

            # Basic scan arguments - TCP Connect scan doesn't require root
            scan_args = '-sT'  # TCP Connect scan

            # Enhanced scanning for pro version
            if self.is_pro:
                scan_args = '-sT -sV --script=vuln'  # Include vulnerability scripts

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

                        # Add vulnerability information
                        if self.is_pro:
                            # Pro version: Get detailed vulnerability data from scripts
                            if 'script' in port_info:
                                port_data['vulnerabilities'] = {
                                    'level': 'advanced',
                                    'details': port_info['script'],
                                    'version_info': port_info.get('version', ''),
                                    'cpe': port_info.get('cpe', ''),
                                    'recommendations': self._get_advanced_recommendations(port_info)
                                }
                        else:
                            # Free version: Basic vulnerability checks
                            vuln_info = self._get_basic_vulnerability_info(port, port_info.get('name', ''))
                            if vuln_info:
                                port_data['vulnerabilities'] = vuln_info

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

    def _get_advanced_recommendations(self, port_info):
        """Generate advanced security recommendations based on scan results"""
        recommendations = []
        if 'version' in port_info:
            recommendations.append(f"Update {port_info['name']} from version {port_info['version']}")
        if 'script' in port_info:
            for script_name, result in port_info['script'].items():
                if 'VULNERABLE' in result.upper():
                    recommendations.append(f"Address {script_name} vulnerability")
        return recommendations