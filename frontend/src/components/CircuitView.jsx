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

	const gateWidth = 53;
	const gateGap = 10;
	const xStep = gateWidth + gateGap;
	const labelWidth = 30; // space on the left for q0 labels
	const contentLeft = padding + labelWidth; // left edge where qubit lines and gates start
	const totalWidth = padding * 2 + gateCount * xStep + labelWidth;

	// get y position for a given qubit index
	const yForQubit = (qIndex) => padding + qIndex * lineGap;
	// get x position for a gate based on its order
	const xForGateIndex = (gateIndex) => contentLeft + gateWidth / 2 + gateIndex * xStep;

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
					<rect x={x - gateWidth / 2} y={y - 10} width={gateWidth} height={20} rx={3} fill="#f5f5f5"/>
					<text x={x} y={y + 4} fontSize={10} textAnchor="middle" fill="#111">
						{gate.type}: {gate.param}
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
					<circle cx={x} cy={yC} r={5} fill="#666" />
					<line x1={x} y1={yC} x2={x} y2={yT} stroke="#666" strokeWidth={3} />
					<rect x={x - gateWidth / 2} y={yT - 10} width={gateWidth} height={20} rx={3} fill="#f5f5f5"/>
					<text x={x} y={yT + 4} fontSize={10} textAnchor="middle" fill="#111">
						{gate.type.replace('c', '')}: {gate.param}
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
						<circle key={`ctrl-${idx}`} cx={x} cy={yForQubit(cQ)} r={5} fill="#666" />
					))}
					<line x1={x} y1={yForQubit(controlQList[0])} x2={x} y2={yT} stroke="#666" strokeWidth={3} />
					<rect x={x - gateWidth / 2} y={yT - 10} width={gateWidth} height={20} rx={3} fill="#fff"/>
					<text x={x} y={yT + 4} fontSize={10} textAnchor="middle" fill="#111">X</text>
				</g>
			);
		}

		// measurement gate
		if (gate.type === 'measure') {
			const targetList = gate.targets;
			return (
				<g key={gateIndex}>
					{targetList.map((tQ, i) => (
						<g key={`m-${i}`}>
							<rect x={x - gateWidth / 2} y={yForQubit(tQ) - 8} width={gateWidth} height={16} rx={3} fill="#ffffff"/>
							<text x={x} y={yForQubit(tQ)} fontSize={12} textAnchor="middle" dominantBaseline="middle" fill="#333">Measure</text>
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
				x1={contentLeft}
				y1={yForQubit(q)}
				x2={totalWidth - padding}
				y2={yForQubit(q)}
				stroke="#fff"
				strokeWidth={1}
			/>
		);
	}

	const qubitLabels = [];
	for (let q = 0; q < qubitCount; q++) {
		qubitLabels.push(
			<text key={`label-${q}`} x={padding + labelWidth - 6} y={yForQubit(q)} fontSize={12} textAnchor="end" dominantBaseline="middle" fill="#fff">{`q${q}`}</text>
		);
	}

	return (
		<div>
			<div style={{ marginTop: 12, textAlign: 'center', overflowX: 'auto', whiteSpace: 'nowrap', width: width }}>
				<svg width={totalWidth} height={height} viewBox={`0 0 ${totalWidth} ${height}`} style={{ display: 'block' }}>
					{qubitLabels}
					{qubitLines}

					{gateList.map((g, idx) => renderGate(g, idx))}
				</svg>
			</div>
				<div style={{ marginTop: 8 }}>
					Legend:<br/>
					value after colon = rotation angle in radians<br/>
					lines with dots = controlled gate<br/>
					v = vision input<br/>
					rx = x rotation<br/>
					ry = y rotation<br/>
					rz = z rotation<br/>
					x = not gate<br/>
					Search up quantum gates for more information
				</div>
		</div>
	);
}
