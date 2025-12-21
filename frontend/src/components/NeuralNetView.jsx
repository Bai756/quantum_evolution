import React from 'react';


export default function NeuralNetView({ network, width = 520, height = 200 }) {
  if (!network || !Array.isArray(network.layers)) {
    return null;
  }

  const layers = network.layers;
  const pad = 12;
  const layerCount = layers.length;
  const xStep = Math.max(60, Math.floor((width - pad * 2) / Math.max(1, layerCount - 1)));

  // nodes per layer
  const nodes = layers.map(l => l.weights.length);
  const maxNodes = Math.max(1, ...nodes);
  const yStep = Math.max(12, Math.floor((height - pad * 2) / Math.max(1, maxNodes - 1)));

  const xFor = (i) => pad + i * xStep;
  const yFor = (layerIdx, nodeIdx, layerSize) => {
    const start = pad + (height - pad * 2 - (layerSize - 1) * yStep) / 2;
    return start + nodeIdx * yStep;
  };

  function renderConnections(layerIdx) {
    const layer = layers[layerIdx];
    const next = layers[layerIdx + 1];
    if (!next) {
      return null;
    }
    const w = layer.weights;
    const is2D = Array.isArray(w[0]);

    if (is2D) {
      return w.flatMap((row, rIdx) => (
        row.map((val, cIdx) => (
          <line
            key={`e-${layerIdx}-${rIdx}-${cIdx}`}
            x1={xFor(layerIdx)}
            y1={yFor(layerIdx, rIdx, nodes[layerIdx])}
            x2={xFor(layerIdx + 1)}
            y2={yFor(layerIdx + 1, cIdx, nodes[layerIdx + 1])}
            stroke="#444"
            strokeWidth={Math.max(0.5, Math.min(2, Math.abs(val) || 0.5))}
            strokeOpacity={0.9}
          />
        ))
      ));
    }

    return Array.from({ length: nodes[layerIdx] }).flatMap((_, rIdx) => (
      Array.from({ length: nodes[layerIdx + 1] || 0 }).map((__, cIdx) => {
        const val = (w && w[cIdx]) || 0;
        return (
          <line
            key={`e-${layerIdx}-${rIdx}-${cIdx}`}
            x1={xFor(layerIdx)}
            y1={yFor(layerIdx, rIdx, nodes[layerIdx])}
            x2={xFor(layerIdx + 1)}
            y2={yFor(layerIdx + 1, cIdx, nodes[layerIdx + 1])}
            stroke="#444"
            strokeWidth={Math.max(0.5, Math.min(2, Math.abs(val) || 0.5))}
            strokeOpacity={0.9}
          />
        );
      })
    ));
  }

  return (
    <div style={{ marginTop: 12, textAlign: 'center' }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {layers.map((L, li) => (
          <g key={`layer-${li}`}>
            {Array.from({ length: nodes[li] }).map((_, ni) => (
              <circle key={`n-${li}-${ni}`} cx={xFor(li)} cy={yFor(li, ni, nodes[li])} r={6} fill="#fff" stroke="#333" />
            ))}

            {li < layers.length - 1 && renderConnections(li)}
          </g>
        ))}
      </svg>
    </div>
  );
}
