import React, { useEffect, useRef, useState } from 'react';
import api from '../api';

const CELL_SIZE = 40;
const GRID_SIZE = 5;

export default function CreatureCanvas() {
  const canvasReference = useRef(null);
  const [creature, setCreature] = useState(null);

  useEffect(() => {
    async function fetchCreature() {
      try {
        const response = await api.get('/creature');
        setCreature(response.data);
      } catch (error) {
        console.error('Failed to fetch creature:', error);
      }
    }
    fetchCreature();
  }, []);

  useEffect(() => {
    const canvasElement = canvasReference.current;
    if (!canvasElement) {
      return;
    }

    const drawingContext = canvasElement.getContext('2d');
    const totalSizePx = CELL_SIZE * GRID_SIZE;
    canvasElement.width = totalSizePx;
    canvasElement.height = totalSizePx;

    drawingContext.clearRect(0, 0, totalSizePx, totalSizePx);

    const defaultGrid = Array.from({ length: GRID_SIZE }, () => Array(GRID_SIZE).fill(0));
    const gridToDraw = creature && creature.grid ? creature.grid : defaultGrid;

    const COLOR_EMPTY = '#ffffff';
    const COLOR_CREATURE = '#3264ff';
    const COLOR_FOOD = '#32c832';
    const GRID_LINE_COLOR = '#b4b4b4';
    const TRIANGLE_COLOR = '#000000';

    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        const value = gridToDraw[row][col];
        let fill = COLOR_EMPTY;
        if (value === 1) {
          fill = COLOR_CREATURE;
        } else if (value === 2) {
          fill = COLOR_FOOD;
        }
        drawingContext.fillStyle = fill;
        drawingContext.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE);
      }
    }

    // draw grid lines
    drawingContext.strokeStyle = GRID_LINE_COLOR;
    drawingContext.lineWidth = 1;
    for (let i = 0; i <= GRID_SIZE; i++) {
      const position = i * CELL_SIZE + 0.5;
      drawingContext.beginPath();
      drawingContext.moveTo(position, 0);
      drawingContext.lineTo(position, totalSizePx);
      drawingContext.stroke();

      drawingContext.beginPath();
      drawingContext.moveTo(0, position);
      drawingContext.lineTo(totalSizePx, position);
      drawingContext.stroke();
    }

    if (creature) {
      const playerPosition = Array.isArray(creature.pos) ? creature.pos : [Math.floor(GRID_SIZE / 2), Math.floor(GRID_SIZE / 2)];
      const row = playerPosition[0];
      const col = playerPosition[1];
      const orientation = typeof creature.orientation === 'number' ? creature.orientation : 0;

      const centerX = col * CELL_SIZE + CELL_SIZE / 2;
      const centerY = row * CELL_SIZE + CELL_SIZE / 2;
      const triSize = CELL_SIZE * 0.35;
      const half = triSize / 2;

      let points;
      if (orientation === 0) {
        points = [[centerX, centerY - half], [centerX - half, centerY + half], [centerX + half, centerY + half]];
      } else if (orientation === 1) {
        points = [[centerX + half, centerY], [centerX - half, centerY - half], [centerX - half, centerY + half]];
      } else if (orientation === 2) {
        points = [[centerX, centerY + half], [centerX - half, centerY - half], [centerX + half, centerY - half]];
      } else {
        points = [[centerX - half, centerY], [centerX + half, centerY - half], [centerX + half, centerY + half]];
      }

      drawingContext.fillStyle = TRIANGLE_COLOR;
      drawingContext.beginPath();
      drawingContext.moveTo(points[0][0], points[0][1]);
      drawingContext.lineTo(points[1][0], points[1][1]);
      drawingContext.lineTo(points[2][0], points[2][1]);
      drawingContext.closePath();
      drawingContext.fill();
    }
  }, [creature]);

  return (
    <div>
      <h2>Creature Grid</h2>
      <canvas
        ref={canvasReference}
        style={{ border: '1px solid #dddddd', display: 'block' }}
        aria-label="Creature grid"
      />
    </div>
  );
}
