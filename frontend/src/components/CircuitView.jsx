import React from 'react';


export default function CircuitView({ circuit, width = 520, height = 160 }) {
	if (!circuit || !circuit.gates) {
		return null;
	}

	const qubitCount = circuit.qubits;
	const gateList = circuit.gates;

	// layout
	const padding = 12;
	const lineGap = (height - padding * 2) / Math.max(1, qubitCount - 1);
	const gateCount = Math.max(1, gateList.length);
	const xStep = Math.max(24, Math.floor((width - padding * 2) / gateCount));

	// get y position for a given qubit index
	const yForQubit = (qIndex) => padding + qIndex * lineGap;
	// get x position for a gate based on its order
	const xForGateIndex = (gateIndex) => padding + 8 + gateIndex * xStep;

	// draw one gate
	function renderGate(gate, gateIndex) {
		const x = xForGateIndex(gateIndex);
		const targets = gate.targets || [];
		const controls = gate.controls || [];

		// rx, ry, rz
		if (gate.type === 'rx' || gate.type === 'ry' || gate.type === 'rz') {
			const targetQ = targets[0];
			const y = yForQubit(targetQ);
			return (
				<g key={gateIndex}>
					<rect x={x - 14} y={y - 10} width={28} height={20} rx={3} fill="#f5f5f5" stroke="#333" />
					<text x={x} y={y + 4} fontSize={10} textAnchor="middle" fill="#111">
						{gate.type} {gate.param}
					</text>
				</g>
			);
		}

		// cry, crx
		if (gate.type === 'cry' || gate.type === 'crx') {
			const controlQ = controls[0];
			const targetQ = targets[0];
			const yC = yForQubit(controlQ);
			const yT = yForQubit(targetQ);
			return (
				<g key={gateIndex}>
					<circle cx={x} cy={yC} r={3} fill="#000" />
					<line x1={x} y1={yC} x2={x} y2={yT} stroke="#444" strokeWidth={1} />
					<rect x={x - 14} y={yT - 10} width={28} height={20} rx={3} fill="#f5f5f5" stroke="#333" />
					<text x={x} y={yT + 4} fontSize={10} textAnchor="middle" fill="#111">
						{gate.type.replace('c', '')}{gate.param ? ` ${gate.param}` : ''}
					</text>
				</g>
			);
		}

		// cx
		if (gate.type === 'cx') {
			let controlQList = [];
			if (Array.isArray(controls)) {
				if (controls.length > 0 && Array.isArray(controls[0])) {
					controlQList = controls[0];
				} else {
					controlQList = controls;
				}
			}

			const targetQ = targets[0];
			const yT = yForQubit(targetQ);
			return (
				<g key={gateIndex}>
					{controlQList.map((cQ, idx) => (
						<circle key={`ctrl-${idx}`} cx={x} cy={yForQubit(cQ)} r={3} fill="#000" />
					))}
					<line x1={x} y1={yForQubit(controlQList[0] || 0)} x2={x} y2={yT} stroke="#444" strokeWidth={1} />
					<rect x={x - 10} y={yT - 8} width={20} height={16} rx={3} fill="#fff" stroke="#333" />
					<text x={x} y={yT + 4} fontSize={10} textAnchor="middle" fill="#111">X</text>
				</g>
			);
		}

		// measurement gate
		if (gate.type === 'measure') {
			const targetList = [5, 6];
			return (
				<g key={gateIndex}>
					{targetList.map((tQ, i) => (
						<g key={`m-${i}`}>
							<rect x={x - 10} y={yForQubit(tQ) - 8} width={20} height={16} rx={3} fill="#fff6" stroke="#666" />
							<text x={x + 12} y={yForQubit(tQ) + 4} fontSize={10} fill="#333">M</text>
						</g>
					))}
				</g>
			);
		}
	}

	// build qubit line
	const qubitLines = [];
	for (let q = 0; q < qubitCount; q++) {
		qubitLines.push(
			<line
				key={`q-${q}`}
				x1={padding}
				y1={yForQubit(q)}
				x2={width - padding}
				y2={yForQubit(q)}
				stroke="#bbb"
				strokeWidth={1}
			/>
		);
	}

	return (
		<div style={{ marginTop: 12, textAlign: 'center' }}>
			<svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
				{qubitLines}

				{gateList.map((g, idx) => renderGate(g, idx))}
			</svg>
		</div>
	);
}
