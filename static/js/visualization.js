document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const scanForm = document.getElementById('scanForm');
    const startScanBtn = document.getElementById('startScan');
    const stopScanBtn = document.getElementById('stopScan');
    const scanStatus = document.getElementById('scanStatus');
    const proBanner = document.querySelector('.pro-banner');
    const scanResults = document.querySelector('.scan-results');

    setTimeout(() => proBanner.style.display = 'block', 2000);

    socket.on('connect', () => console.log('Connected to server'));

    socket.on('scan_status', (data) => {
        switch(data.status) {
            case 'starting':
                scanStatus.className = 'alert alert-info';
                scanStatus.textContent = 'Scan in progress...';
                startScanBtn.disabled = true;
                stopScanBtn.disabled = false;
                scanResults.innerHTML = '';
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

let simulation;
let svg;
let width;
let height;
let nodes = [];
let links = [];

function initVisualization() {
    const container = document.getElementById('networkVisualization');
    width = container.clientWidth;
    height = container.clientHeight;

    svg = d3.select('#networkVisualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));
}

function updateVisualization(hostData) {
    if (!svg) initVisualization();

    const existingNode = nodes.find(n => n.id === hostData.host);
    if (!existingNode) {
        nodes.push({
            id: hostData.host,
            status: hostData.status,
            ports: hostData.ports
        });
    }

    const link = svg.selectAll('.link')
        .data(links)
        .join('line')
        .attr('class', 'link');

    const node = svg.selectAll('.node')
        .data(nodes)
        .join('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.selectAll('circle')
        .data(d => [d])
        .join('circle')
        .attr('r', 20)
        .attr('fill', d => getNodeColor(d));

    node.selectAll('text')
        .data(d => [d])
        .join('text')
        .attr('dx', 25)
        .attr('dy', 5)
        .text(d => d.id);

    simulation
        .nodes(nodes)
        .on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

    simulation.force('link').links(links);
    simulation.alpha(1).restart();
}

function getNodeColor(node) {
    return node.ports && node.ports.some(p => p.vulnerabilities) ? '#ff4444' : 
           node.status === 'up' ? '#4CAF50' : '#666';
}

function updatePortInfo(portData) {
    const scanResults = document.querySelector('.scan-results');
    let portDiv = document.getElementById(`port-${portData.port}`);

    if (!portDiv) {
        portDiv = document.createElement('div');
        portDiv.id = `port-${portData.port}`;
        portDiv.className = 'card bg-dark mb-3';
        scanResults.appendChild(portDiv);
    }

    const statusColor = portData.state === 'open' ? 'success' : 'danger';
    let html = `
        <div class="card-body">
            <h5 class="card-title">Port ${portData.port} - ${portData.service}</h5>
            <p class="card-text">
                <span class="badge bg-${statusColor}">${portData.state}</span>
                ${portData.state === 'open' ? `<span class="badge bg-secondary ms-2">${portData.service}</span>` : ''}
            </p>`;

    if (portData.vulnerabilities) {
        const vulnInfo = portData.vulnerabilities;
        html += `
            <div class="alert alert-warning mt-2">
                <h6>Security Warning${vulnInfo.level === 'advanced' ? ' (Pro)' : ''}</h6>
                <p>${vulnInfo.description || vulnInfo.details || 'Potential security risk detected'}</p>
                ${vulnInfo.recommendations ? `<ul>${vulnInfo.recommendations.map(rec => `<li>${rec}</li>`).join('')}</ul>` : ''}
            </div>`;
    }

    if (!portData.is_pro && portData.state === 'open') {
        html += `
            <div class="alert alert-info mt-2">
                <small>🔒 Upgrade to Pro for detailed vulnerability analysis</small>
            </div>`;
    }

    html += '</div>';
    portDiv.innerHTML = html;
}

function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
}

function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
}

function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
}

document.addEventListener('DOMContentLoaded', initVisualization);