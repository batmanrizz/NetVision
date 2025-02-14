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
    if (!svg) {
        initVisualization();
    }

    // Add new node if it doesn't exist
    const existingNode = nodes.find(n => n.id === hostData.host);
    if (!existingNode) {
        nodes.push({
            id: hostData.host,
            status: hostData.status,
            ports: hostData.ports
        });
    }

    // Update visualization
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
        .attr('fill', d => d.status === 'up' ? '#4CAF50' : '#f44336');

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

            node
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });

    simulation.force('link').links(links);
    simulation.alpha(1).restart();
}

function updatePortInfo(portData) {
    // Update port information in the visualization
    const portRadius = 5;
    const portDistance = 40;

    const node = d3.select(`.node:has(text:contains("${portData.host}"))`);
    if (!node.empty()) {
        const portGroup = node.selectAll('.port-group')
            .data([portData])
            .join('g')
            .attr('class', 'port-group')
            .attr('transform', `translate(${portDistance}, 0)`);

        portGroup.selectAll('circle')
            .data([portData])
            .join('circle')
            .attr('r', portRadius)
            .attr('class', d => `port-${d.state}`);

        portGroup.selectAll('text')
            .data([portData])
            .join('text')
            .attr('dx', portRadius + 5)
            .attr('dy', 4)
            .text(d => `${d.port}/${d.service}`);
    }
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
