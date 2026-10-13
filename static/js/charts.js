/**
 * Native SVG & Canvas Histogram Renderer
 */

export function renderHistogram(canvasOrSvgContainer, counts, probabilities) {
    if (typeof canvasOrSvgContainer === 'string') {
        canvasOrSvgContainer = document.getElementById(canvasOrSvgContainer);
    }
    if (!canvasOrSvgContainer) return;

    canvasOrSvgContainer.innerHTML = '';
    const entries = Object.entries(probabilities || {});
    if (entries.length === 0) {
        canvasOrSvgContainer.innerHTML = '<div style="color: var(--color-text-dim); text-align: center; padding: 2rem;">No measurement shots collected.</div>';
        return;
    }

    // Sort bitstrings in computational order
    entries.sort((a, b) => a[0].localeCompare(b[0]));

    const width = canvasOrSvgContainer.clientWidth || 500;
    const height = 240;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const maxProb = Math.max(...entries.map(e => e[1]), 0.1);
    const barWidth = Math.max(16, Math.min(48, chartWidth / entries.length - 12));

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', height.toString());
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

    // Y Axis line
    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', padding.left);
    yAxis.setAttribute('y1', padding.top);
    yAxis.setAttribute('x2', padding.left);
    yAxis.setAttribute('y2', padding.top + chartHeight);
    yAxis.setAttribute('stroke', 'var(--color-border)');
    yAxis.setAttribute('stroke-width', '1');
    svg.appendChild(yAxis);

    // X Axis line
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    xAxis.setAttribute('x1', padding.left);
    xAxis.setAttribute('y1', padding.top + chartHeight);
    xAxis.setAttribute('x2', padding.left + chartWidth);
    xAxis.setAttribute('y2', padding.top + chartHeight);
    xAxis.setAttribute('stroke', 'var(--color-border)');
    xAxis.setAttribute('stroke-width', '1');
    svg.appendChild(xAxis);

    // Bars
    entries.forEach(([bitstring, prob], i) => {
        const x = padding.left + (i * (chartWidth / entries.length)) + ((chartWidth / entries.length - barWidth) / 2);
        const barH = (prob / maxProb) * chartHeight;
        const y = padding.top + chartHeight - barH;

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x.toString());
        rect.setAttribute('y', y.toString());
        rect.setAttribute('width', barWidth.toString());
        rect.setAttribute('height', barH.toString());
        rect.setAttribute('fill', 'var(--color-accent-blue)');
        rect.setAttribute('rx', '3');
        svg.appendChild(rect);

        // Bitstring label
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', (x + barWidth / 2).toString());
        text.setAttribute('y', (padding.top + chartHeight + 20).toString());
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', 'var(--color-text-muted)');
        text.setAttribute('font-size', '11');
        text.setAttribute('font-family', 'var(--font-family-mono)');
        text.textContent = `|${bitstring}⟩`;
        svg.appendChild(text);

        // Value text
        const probText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        probText.setAttribute('x', (x + barWidth / 2).toString());
        probText.setAttribute('y', (y - 5).toString());
        probText.setAttribute('text-anchor', 'middle');
        probText.setAttribute('fill', 'var(--color-text-main)');
        probText.setAttribute('font-size', '10');
        probText.setAttribute('font-weight', '600');
        probText.textContent = `${(prob * 100).toFixed(1)}%`;
        svg.appendChild(probText);
    });

    canvasOrSvgContainer.appendChild(svg);
}
