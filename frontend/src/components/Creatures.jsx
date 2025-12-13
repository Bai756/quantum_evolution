import React, { useEffect, useRef, useState } from 'react';
import api from '../api';

const CELL_SIZE = 40;
const GRID_SIZE = 5;

export default function CreatureCanvas({ snapshot }) {
	const canvasReference = useRef(null);
	const [creature, setCreature] = useState(null);
	const [lastGen, setLastGen] = useState(null);
	const [lastFitness, setLastFitness] = useState(null);
	const [best, setBest] = useState(null);

	useEffect(() => {
		async function fetchCreature() {
			try {
				const response = await api.get('/creature');
				setCreature(response.data);
				setLastGen(response.data.generation);
				setLastFitness(response.data.fitness);
			} catch (error) {
				console.error('Failed to fetch creature:', error);
			}
		}

		fetchCreature();
	}, []);

	// update from external snapshot prop
	useEffect(() => {
		if (!snapshot) return;
		if (snapshot.best) {
			setBest(snapshot.best);
		}
		if (snapshot.angles) {
			setCreature(snapshot);
			setLastGen(snapshot.generation);
			setLastFitness(snapshot.fitness);
		}
	}, [snapshot]);

	useEffect(() => {
		const canvasElement = canvasReference.current;
		if (!canvasElement || !creature) {
			return;
		}

		const drawingContext = canvasElement.getContext('2d');
		const totalSizePx = CELL_SIZE * GRID_SIZE;
		canvasElement.width = totalSizePx;
		canvasElement.height = totalSizePx;

		drawingContext.clearRect(0, 0, totalSizePx, totalSizePx);

		const gridToDraw = creature.grid;

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

		const playerPosition = Array.isArray(creature.pos)
			? creature.pos
			: [Math.floor(GRID_SIZE / 2), Math.floor(GRID_SIZE / 2)];
		const row = playerPosition[0];
		const col = playerPosition[1];
		const orientation = creature.orientation;

		const centerX = col * CELL_SIZE + CELL_SIZE / 2;
		const centerY = row * CELL_SIZE + CELL_SIZE / 2;
		const triSize = CELL_SIZE * 0.35;
		const half = triSize / 2;

		let points;
		if (orientation === 0) {
			points = [
				[centerX, centerY - half],
				[centerX - half, centerY + half],
				[centerX + half, centerY + half],
			];
		} else if (orientation === 1) {
			points = [
				[centerX + half, centerY],
				[centerX - half, centerY - half],
				[centerX - half, centerY + half],
			];
		} else if (orientation === 2) {
			points = [
				[centerX, centerY + half],
				[centerX - half, centerY - half],
				[centerX + half, centerY - half],
			];
		} else {
			points = [
				[centerX - half, centerY],
				[centerX + half, centerY - half],
				[centerX + half, centerY + half],
			];
		}

		drawingContext.fillStyle = TRIANGLE_COLOR;
		drawingContext.beginPath();
		drawingContext.moveTo(points[0][0], points[0][1]);
		drawingContext.lineTo(points[1][0], points[1][1]);
		drawingContext.lineTo(points[2][0], points[2][1]);
		drawingContext.closePath();
		drawingContext.fill();
	}, [creature]);

	let bestAnglesText = '';
	if (best) {
		bestAnglesText = best.angles.map((a) => Number(a).toFixed(3)).join(', ');
	}

    return (
        <div>
            <div style={{ marginBottom: 8 }}>
                {lastGen !== null && (
                    <div>
                        Gen {lastGen} | Fitness{' '}
                        {lastFitness.toFixed(1)}
                    </div>
                )}
                {best && (
                    <div style={{ marginTop: 8 }}>
                        <strong>Final Best:</strong> Fitness{' '}
                        {best.fitness.toFixed(1)}
                        <br />
                        Angles: {bestAnglesText}
                    </div>
                )}
            </div>
            <canvas
                ref={canvasReference}
                style={{ border: '1px solid #dddddd', display: 'block' }}
                aria-label="Creature grid"
            />
        </div>
    );
}