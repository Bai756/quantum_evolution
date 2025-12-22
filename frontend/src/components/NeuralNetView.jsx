import React from 'react';


export default function NeuralNetView({ network, width, height }) {
	if (!network || !Array.isArray(network.layers)) {
		return null;
	}

	// Group 2D weight matrices and following 1D bias vectors
	const rawLayers = network.layers;
	const grouped = [];
	for (let i = 0; i < rawLayers.length; i++) {
		const item = rawLayers[i];
		const w = item.weights;
		// treat a 2D array as a weight matrix
		if (Array.isArray(w) && Array.isArray(w[0])) {
			let biases = null;
			// if next item is a 1D array, it's the biases for this layer
			if (i + 1 < rawLayers.length) {
				const next = rawLayers[i + 1];
				const nw = next.weights;
				if (Array.isArray(nw) && !Array.isArray(nw[0])) {
					biases = nw;
					i++; // skip bias entry
				}
			}
			grouped.push({ weights: w, biases });
		}
	}

	// nodes per layer
	// input nodes = rows of first weight matrix
	// each layer's output nodes = # of cols
	const nodes = [];
	const firstW = grouped[0].weights;
	const inputCount = firstW.length;
	nodes.push(inputCount);
	for (let g of grouped) {
		const w = g.weights;
		let outCount = 0;
		if (Array.isArray(w) && Array.isArray(w[0])) {
			outCount = w[0].length;
		} else if (Array.isArray(w)) {
			outCount = w.length;
		}
		nodes.push(outCount);
	}

	// global max for weights and biases
	let globalMaxWeight = 1;
	let globalMaxBias = 1;
	for (let i = 1; i < grouped.length; i++) {
		const g = grouped[i];
		if (Array.isArray(g.weights) && Array.isArray(g.weights[0])) {
			for (let r = 0; r < g.weights.length; r++) {
				for (let c = 0; c < g.weights[r].length; c++) {
					const v = Math.abs(Number(g.weights[r][c]));
					if (v > globalMaxWeight) {
						globalMaxWeight = v;
					}
				}
			}
		}
		if (Array.isArray(g.biases)) {
			for (let b of g.biases) {
				const bv = Math.abs(Number(b));
				if (bv > globalMaxBias) {
					globalMaxBias = bv;
				}
			}
		}
	}

	const pad = 12;
	const layerCount = nodes.length;
	const xStep = Math.max(60, Math.floor((width - pad * 2) / Math.max(1, layerCount - 1)));

	const maxNodes = Math.max(1, ...nodes);
	const yStep = Math.max(12, Math.floor((height - pad * 2) / Math.max(1, maxNodes - 1)));

	const xFor = (i) => pad + i * xStep;
	const yFor = (layerIdx, nodeIdx, layerSize) => {
		const start = pad + (height - pad * 2 - (layerSize - 1) * yStep) / 2;
		return start + nodeIdx * yStep;
	};

	// render connections for a grouped layer index
	function renderConnections(layerIdx) {
		const g = grouped[layerIdx];
		const w = g.weights; // w is rows x cols

		return w.flatMap((row, rIdx) => (
			row.map((val, cIdx) => {
				const absv = Math.abs(Number(val));
				// opacity scaled 0.1-1.0 based on global relative magnitude
				const op = Math.max(0.1, Math.min(1.0, absv / globalMaxWeight));
				return (
					<line
						key={`e-${layerIdx}-${rIdx}-${cIdx}`}
						x1={xFor(layerIdx)}
						y1={yFor(layerIdx, rIdx, nodes[layerIdx])}
						x2={xFor(layerIdx + 1)}
						y2={yFor(layerIdx + 1, cIdx, nodes[layerIdx + 1])}
						stroke="#444"
						strokeWidth={1}
						strokeOpacity={op}
					/>
				);
			})
		));
	}

	return (
		<div style={{ marginTop: 12, textAlign: 'center' }}>
			<svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
				{nodes.map((count, layerIdx) => (
					<g key={`layer-${layerIdx}`}>
						{Array.from({ length: count }).map((_, ni) => {
							// determine fill opacity from global bias magnitude
							let fillOpacity = 1.0;
							if (layerIdx > 0) {
								const biasArr = grouped[layerIdx - 1] && grouped[layerIdx - 1].biases;
								if (Array.isArray(biasArr)) {
									const biasVal = Math.abs(Number(biasArr[ni]));
									fillOpacity = Math.max(0.1, Math.min(1.0, biasVal / globalMaxBias));
								}
							}

							return (
								<circle key={`n-${layerIdx}-${ni}`} cx={xFor(layerIdx)} cy={yFor(layerIdx, ni, count)} r={6} fill="#fff" stroke="#333" fillOpacity={fillOpacity} />
							);
						})}

						{layerIdx < grouped.length && renderConnections(layerIdx)}
					</g>
				))}
			</svg>
		</div>
	);
}
