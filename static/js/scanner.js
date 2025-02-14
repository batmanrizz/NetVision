document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const scanForm = document.getElementById('scanForm');
    const startScanBtn = document.getElementById('startScan');
    const stopScanBtn = document.getElementById('stopScan');
    const scanStatus = document.getElementById('scanStatus');
    const proBanner = document.querySelector('.pro-banner');

    setTimeout(() => proBanner.style.display = 'block', 2000);

    socket.on('connect', () => {});

    socket.on('scan_status', (data) => {
        switch(data.status) {
            case 'starting':
                scanStatus.className = 'alert alert-info';
                scanStatus.textContent = 'Scan in progress...';
                startScanBtn.disabled = true;
                stopScanBtn.disabled = false;
                break;
            case 'completed':
                scanStatus.className = 'alert alert-success';
                scanStatus.textContent = 'Scan completed';
                startScanBtn.disabled = false;
                stopScanBtn.disabled = true;
                break;
        }
    });

    socket.on('scan_error', (data) => {
        scanStatus.className = 'alert alert-danger';
        scanStatus.textContent = `Error: ${data.error}`;
        startScanBtn.disabled = false;
        stopScanBtn.disabled = true;
    });

    socket.on('host_data', (data) => {
        updateVisualization(data);
        if (data.os) {
            const osInfo = document.createElement('div');
            osInfo.className = 'alert alert-info mt-2';
            osInfo.textContent = `OS Detection: ${data.os[0].name} (${data.os[0].accuracy}% accuracy)`;
            scanStatus.parentNode.appendChild(osInfo);
        }
    });

    socket.on('port_data', (data) => updatePortInfo(data));

    scanForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const target = document.getElementById('target').value;
        const ports = document.getElementById('ports').value;
        socket.emit('start_scan', { target, ports });
    });

    stopScanBtn.addEventListener('click', () => {
        socket.emit('stop_scan');
        startScanBtn.disabled = false;
        stopScanBtn.disabled = true;
        scanStatus.className = 'alert alert-warning';
        scanStatus.textContent = 'Scan stopped by user';
    });
});