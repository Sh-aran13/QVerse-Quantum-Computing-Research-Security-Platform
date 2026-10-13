/**
 * QVerse Interactive Quantum Circuit Canvas Editor
 */

export class CircuitEditor {
    constructor(canvasContainerId, options = {}) {
        this.container = document.getElementById(canvasContainerId);
        this.numQubits = options.numQubits || 2;
        this.numClbits = options.numClbits || 2;
        this.operations = options.operations || [];
        this.selectedGate = 'h';
        this.onCircuitChange = options.onCircuitChange || (() => {});
        this.render();
    }

    setNumQubits(n) {
        this.numQubits = Math.max(1, Math.min(16, parseInt(n) || 2));
        this.operations = this.operations.filter(op => op.targets.every(t => t < this.numQubits));
        this.render();
        this.onCircuitChange(this.getDefinition());
    }

    addGate(gate, targets, params = [], cbits = []) {
        this.operations.push({
            gate,
            targets,
            params,
            cbits
        });
        this.render();
        this.onCircuitChange(this.getDefinition());
    }

    removeGate(index) {
        if (index >= 0 && index < this.operations.length) {
            this.operations.splice(index, 1);
            this.render();
            this.onCircuitChange(this.getDefinition());
        }
    }

    clear() {
        this.operations = [];
        this.render();
        this.onCircuitChange(this.getDefinition());
    }

    loadDefinition(definition) {
        this.numQubits = definition.num_qubits || 2;
        this.numClbits = definition.num_classical_bits || 2;
        this.operations = definition.operations || [];
        this.render();
        this.onCircuitChange(this.getDefinition());
    }

    getDefinition() {
        return {
            schema_version: "1.0",
            num_qubits: this.numQubits,
            num_classical_bits: this.numClbits,
            operations: [...this.operations]
        };
    }

    render() {
        if (!this.container) return;
        this.container.innerHTML = '';

        const wireSpacing = 56;
        const colSpacing = 64;
        const leftPadding = 80;
        const topPadding = 30;

        const maxCol = Math.max(8, this.operations.length + 2);
        const svgWidth = Math.max(this.container.clientWidth || 600, leftPadding + (maxCol * colSpacing) + 60);
        const svgHeight = topPadding + (this.numQubits * wireSpacing) + 20;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', svgWidth.toString());
        svg.setAttribute('height', svgHeight.toString());
        svg.style.userSelect = 'none';

        // Qubit Wires
        for (let q = 0; q < this.numQubits; q++) {
            const y = topPadding + (q * wireSpacing);

            // Wire label
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', '20');
            label.setAttribute('y', (y + 5).toString());
            label.setAttribute('fill', 'var(--color-text-main)');
            label.setAttribute('font-family', 'var(--font-family-mono)');
            label.setAttribute('font-size', '13');
            label.setAttribute('font-weight', '600');
            label.textContent = `q[${q}]`;
            svg.appendChild(label);

            // Wire line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', leftPadding.toString());
            line.setAttribute('y1', y.toString());
            line.setAttribute('x2', (svgWidth - 40).toString());
            line.setAttribute('y2', y.toString());
            line.setAttribute('stroke', 'var(--color-border)');
            line.setAttribute('stroke-width', '2');
            svg.appendChild(line);
        }

        // Render Operations
        this.operations.forEach((op, colIdx) => {
            const x = leftPadding + (colIdx * colSpacing) + 30;

            if (op.gate === 'cx' && op.targets.length === 2) {
                const ctrlY = topPadding + (op.targets[0] * wireSpacing);
                const tgtY = topPadding + (op.targets[1] * wireSpacing);

                // Control-target connector line
                const cLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                cLine.setAttribute('x1', x.toString());
                cLine.setAttribute('y1', ctrlY.toString());
                cLine.setAttribute('x2', x.toString());
                cLine.setAttribute('y2', tgtY.toString());
                cLine.setAttribute('stroke', 'var(--color-accent-blue)');
                cLine.setAttribute('stroke-width', '2');
                svg.appendChild(cLine);

                // Control dot
                const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                dot.setAttribute('cx', x.toString());
                dot.setAttribute('cy', ctrlY.toString());
                dot.setAttribute('r', '5');
                dot.setAttribute('fill', 'var(--color-accent-blue)');
                svg.appendChild(dot);

                // Target cross/circle
                const targetCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                targetCircle.setAttribute('cx', x.toString());
                targetCircle.setAttribute('cy', tgtY.toString());
                targetCircle.setAttribute('r', '14');
                targetCircle.setAttribute('fill', 'var(--color-surface-dark)');
                targetCircle.setAttribute('stroke', 'var(--color-accent-blue)');
                targetCircle.setAttribute('stroke-width', '2');
                svg.appendChild(targetCircle);

                const crossH = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                crossH.setAttribute('x1', (x - 14).toString());
                crossH.setAttribute('y1', tgtY.toString());
                crossH.setAttribute('x2', (x + 14).toString());
                crossH.setAttribute('y2', tgtY.toString());
                crossH.setAttribute('stroke', 'var(--color-accent-blue)');
                crossH.setAttribute('stroke-width', '2');
                svg.appendChild(crossH);

                const crossV = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                crossV.setAttribute('x1', x.toString());
                crossV.setAttribute('y1', (tgtY - 14).toString());
                crossV.setAttribute('x2', x.toString());
                crossV.setAttribute('y2', (tgtY + 14).toString());
                crossV.setAttribute('stroke', 'var(--color-accent-blue)');
                crossV.setAttribute('stroke-width', '2');
                svg.appendChild(crossV);

                // Click to delete
                [dot, targetCircle, crossH, crossV].forEach(el => {
                    el.style.cursor = 'pointer';
                    el.addEventListener('click', () => this.removeGate(colIdx));
                });
            } else {
                // 1-Qubit Gate Box (H, X, Y, Z, Measure, etc.)
                const targetQ = op.targets[0];
                const y = topPadding + (targetQ * wireSpacing);
                const boxSize = 34;

                const gBox = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                gBox.setAttribute('x', (x - boxSize / 2).toString());
                gBox.setAttribute('y', (y - boxSize / 2).toString());
                gBox.setAttribute('width', boxSize.toString());
                gBox.setAttribute('height', boxSize.toString());
                gBox.setAttribute('rx', '4');

                const isMeasure = op.gate === 'measure';
                gBox.setAttribute('fill', isMeasure ? 'var(--color-surface-dark)' : 'var(--color-accent-blue)');
                gBox.setAttribute('stroke', isMeasure ? 'var(--color-accent-teal)' : 'var(--color-accent-blue-hover)');
                gBox.setAttribute('stroke-width', '1.5');
                gBox.style.cursor = 'pointer';

                const gText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                gText.setAttribute('x', x.toString());
                gText.setAttribute('y', (y + 4).toString());
                gText.setAttribute('text-anchor', 'middle');
                gText.setAttribute('fill', isMeasure ? 'var(--color-accent-teal)' : '#FFFFFF');
                gText.setAttribute('font-family', 'var(--font-family-mono)');
                gText.setAttribute('font-size', '12');
                gText.setAttribute('font-weight', '700');
                gText.textContent = isMeasure ? 'M' : op.gate.toUpperCase();
                gText.style.cursor = 'pointer';

                [gBox, gText].forEach(el => {
                    el.addEventListener('click', () => this.removeGate(colIdx));
                });

                svg.appendChild(gBox);
                svg.appendChild(gText);
            }
        });

        this.container.appendChild(svg);
    }
}
