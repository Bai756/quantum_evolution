import React, { useEffect, useRef, useState } from 'react';
import api from '../api';

const CELL_SIZE = 40;

export default function CreatureCanvas({ snapshot, gridSize = 10 }) {
	const canvasReference = useRef(null);
	const canvasContainerRef = useRef(null);
	const [creature, setCreature] = useState(null);
	const [lastGen, setLastGen] = useState(null);
	const [lastFitness, setLastFitness] = useState(null);
	const [best, setBest] = useState(null);
	const [energy, setEnergy] = useState(null);
	const [maxEnergy, setMaxEnergy] = useState(null);
	const initializedRef = useRef(false);

	useEffect(() => {
		// Only run this once on start
		if (initializedRef.current) {
			return;
		}
		initializedRef.current = true;

		async function fetchInitialCreature() {
			try {
				const res = await api.get('/creature');
				const data = res.data;
				setCreature((prev) => prev ?? data);
				setLastGen(data.generation);
				setLastFitness(data.fitness);
				setEnergy(data.energy);
				setMaxEnergy(data.max_energy);
			} catch (err) {
				console.error('Failed to fetch initial creature:', err);
			}
		}

		fetchInitialCreature();
	}, []);

	// Handle incoming snapshots from the ws
	useEffect(() => {
		if (!snapshot) {
			return;
		}
		if (snapshot.best) {
			setBest(snapshot.best);
		}
		if (snapshot.grid) {
			setCreature(snapshot);
			setLastGen(snapshot.generation);
			setLastFitness(snapshot.fitness);
			setEnergy(snapshot.energy);
			setMaxEnergy(snapshot.max_energy);
		}
	}, [snapshot]);

	useEffect(() => {
		const canvasElement = canvasReference.current;
		const container = canvasContainerRef.current;
		if (!canvasElement || !creature) {
			return;
		}

		const drawingContext = canvasElement.getContext('2d');
		const size = (creature.grid && creature.grid.length) ? creature.grid.length : gridSize;
		const totalSizePx = CELL_SIZE * size;
		canvasElement.width = totalSizePx;
		canvasElement.height = totalSizePx;

		// adjust container size to be same as canvas
		if (container) {
			container.style.width = totalSizePx + 'px';
		}

		drawingContext.clearRect(0, 0, totalSizePx, totalSizePx);

		const gridToDraw = creature.grid;

		const COLOR_EMPTY = '#ffffff';
		const COLOR_CREATURE = '#3264ff';
		const COLOR_FOOD = '#32c832';
		const GRID_LINE_COLOR = '#b4b4b4';
		const TRIANGLE_COLOR = '#000000';
		const WALL_COLOR = '#777777';

		for (let row = 0; row < size; row++) {
			for (let col = 0; col < size; col++) {
				const value = gridToDraw[row][col];
				let fill = COLOR_EMPTY;
				if (value === 1) {
					fill = COLOR_CREATURE;
				} else if (value === 2) {
					fill = COLOR_FOOD;
				} else if (value === 3) {
					fill = WALL_COLOR;
				}
				drawingContext.fillStyle = fill;
				drawingContext.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE);
			}
		}

		// draw grid lines
		drawingContext.strokeStyle = GRID_LINE_COLOR;
		drawingContext.lineWidth = 1;
		for (let i = 0; i <= size; i++) {
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

		const playerPosition = creature.pos;
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
	}, [creature, gridSize]);

	let bestFitnessText = '';
	if (best && typeof best.fitness === 'number') {
		bestFitnessText = best.fitness.toFixed(1);
	}
	let energyPercent = 0;
	if (maxEnergy != null && energy != null) {
		energyPercent = Math.max(0, Math.min(1, energy / maxEnergy));
	}
	return (
		<div>
			<div style={{ marginBottom: 8 }}>
				{lastGen !== null && lastFitness !== null && (
					<div>
						Gen {lastGen} | Fitness {lastFitness.toFixed(1)}
					</div>
				)}
				{best && (
					<div style={{ marginTop: 8 }}>
						Best: Fitness {bestFitnessText}
					</div>
				)}
			</div>
			<div ref={canvasContainerRef} style={{ margin: '0 auto', textAlign: 'center' }}>
				<canvas
					ref={canvasReference}
					style={{ border: '1px solid #dddddd', display: 'block' }}
					aria-label="Creature grid"
				/>
				{maxEnergy != null && energy != null && (
					<div style={{ marginTop: 8 }}>
						<div style={{ height: 8, width: '100%', background: '#eee', borderRadius: 4 }}>
							<div style={{ width: `${Math.round(energyPercent*100)}%`, height: '100%', background: '#3264ff', borderRadius: 4 }} />
						</div>
						<div style={{ marginTop: 4 }}>
							Energy: {energy} / {maxEnergy}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
