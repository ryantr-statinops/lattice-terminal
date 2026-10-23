import {useEffect,useRef,useState} from 'react';
import {useAppearance} from '../theme/store';
import {Button} from '../ui/buttons';

type Props = {
  x: number[];
  y: number[];
  z: number[][]; // z[yIndex][xIndex]
  xLabel?: string;
  yLabel?: string;
  zLabel?: string;
  title?: string;
};

type ViewMode = 'isometric' | 'top' | 'front';

export function SurfacePlot3D({
  x,
  y,
  z,
  xLabel = 'Param X',
  yLabel = 'Param Y',
  zLabel = 'Metric Z',
  title = '3D Parameter Surface',
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appearance = useAppearance();

  const [azimuth, setAzimuth] = useState<number>(-45);
  const [elevation, setElevation] = useState<number>(30);
  const [zoom, setZoom] = useState<number>(1);
  const [viewMode, setViewMode] = useState<ViewMode>('isometric');

  const dragRef = useRef<{active: boolean; startX: number; startY: number; startAzimuth: number; startElevation: number}>({
    active: false,
    startX: 0,
    startY: 0,
    startAzimuth: -45,
    startElevation: 30,
  });

  const setPreset = (mode: ViewMode) => {
    setViewMode(mode);
    if (mode === 'isometric') {
      setAzimuth(-45);
      setElevation(30);
    } else if (mode === 'top') {
      setAzimuth(0);
      setElevation(90);
    } else if (mode === 'front') {
      setAzimuth(0);
      setElevation(0);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (x.length < 2 || y.length < 2 || z.length === 0) {
      ctx.fillStyle = appearance.colors.muted;
      ctx.font = '12px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('Insufficient data for 3D surface plot', width / 2, height / 2);
      return;
    }

    // Find min and max
    let minZ = Infinity;
    let maxZ = -Infinity;
    for (let r = 0; r < z.length; r++) {
      for (let c = 0; c < (z[r]?.length ?? 0); c++) {
        const val = z[r][c];
        if (Number.isFinite(val)) {
          if (val < minZ) minZ = val;
          if (val > maxZ) maxZ = val;
        }
      }
    }
    if (minZ === maxZ) {
      maxZ = minZ + 1;
    }

    const minX = Math.min(...x);
    const maxX = Math.max(...x);
    const minY = Math.min(...y);
    const maxY = Math.max(...y);

    const radAz = (azimuth * Math.PI) / 180;
    const radEl = (elevation * Math.PI) / 180;
    const cosAz = Math.cos(radAz);
    const sinAz = Math.sin(radAz);
    const cosEl = Math.cos(radEl);
    const sinEl = Math.sin(radEl);

    const project = (px: number, py: number, pz: number) => {
      // Normalize to [-1, 1]
      const nx = ((px - minX) / (maxX - minX || 1) - 0.5) * 2;
      const ny = ((py - minY) / (maxY - minY || 1) - 0.5) * 2;
      const nz = ((pz - minZ) / (maxZ - minZ || 1) - 0.5) * 2;

      // Rotate around Y axis (azimuth)
      const x1 = nx * cosAz - ny * sinAz;
      const y1 = nx * sinAz + ny * cosAz;
      const z1 = nz;

      // Rotate around X axis (elevation)
      const x2 = x1;
      const y2 = y1 * cosEl - z1 * sinEl;
      const z2 = y1 * sinEl + z1 * cosEl;

      const scale = 120 * zoom;
      const screenX = width / 2 + x2 * scale;
      const screenY = height / 2 - z2 * scale;

      return {x: screenX, y: screenY, depth: y2};
    };

    // Build quadrilateral meshes
    type Quad = {
      p0: {x: number; y: number; depth: number};
      p1: {x: number; y: number; depth: number};
      p2: {x: number; y: number; depth: number};
      p3: {x: number; y: number; depth: number};
      avgZ: number;
      avgDepth: number;
    };
    const quads: Quad[] = [];

    for (let r = 0; r < y.length - 1; r++) {
      for (let c = 0; c < x.length - 1; c++) {
        const z00 = z[r]?.[c] ?? minZ;
        const z10 = z[r]?.[c + 1] ?? minZ;
        const z11 = z[r + 1]?.[c + 1] ?? minZ;
        const z01 = z[r + 1]?.[c] ?? minZ;

        const p0 = project(x[c], y[r], z00);
        const p1 = project(x[c + 1], y[r], z10);
        const p2 = project(x[c + 1], y[r + 1], z11);
        const p3 = project(x[c], y[r + 1], z01);

        const avgVal = (z00 + z10 + z11 + z01) / 4;
        const avgDepth = (p0.depth + p1.depth + p2.depth + p3.depth) / 4;

        quads.push({p0, p1, p2, p3, avgZ: avgVal, avgDepth});
      }
    }

    // Sort by depth (back to front painter's algorithm)
    quads.sort((a, b) => b.avgDepth - a.avgDepth);

    // Render quads
    for (const q of quads) {
      const norm = Math.max(0, Math.min(1, (q.avgZ - minZ) / (maxZ - minZ || 1)));
      // Interpolate color from negative to positive
      const r = Math.round(norm < 0.5 ? 200 * (1 - norm * 2) + 60 : 40);
      const g = Math.round(norm >= 0.5 ? 200 * (norm - 0.5) * 2 + 60 : 60);
      const b = Math.round(100 + 80 * Math.sin(norm * Math.PI));

      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.75)`;
      ctx.strokeStyle = appearance.colors.border;
      ctx.lineWidth = 0.5;

      ctx.beginPath();
      ctx.moveTo(q.p0.x, q.p0.y);
      ctx.lineTo(q.p1.x, q.p1.y);
      ctx.lineTo(q.p2.x, q.p2.y);
      ctx.lineTo(q.p3.x, q.p3.y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Render Bounding Box Axes
    ctx.strokeStyle = appearance.colors.borderStrong;
    ctx.lineWidth = 1;
    const origin = project(minX, minY, minZ);
    const xEnd = project(maxX, minY, minZ);
    const yEnd = project(minX, maxY, minZ);
    const zEnd = project(minX, minY, maxZ);

    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(xEnd.x, xEnd.y);
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(yEnd.x, yEnd.y);
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(zEnd.x, zEnd.y);
    ctx.stroke();

    // Axis labels
    ctx.fillStyle = appearance.colors.text;
    ctx.font = '11px monospace';
    ctx.fillText(`${xLabel} (${minX}..${maxX})`, xEnd.x + 4, xEnd.y);
    ctx.fillText(`${yLabel} (${minY}..${maxY})`, yEnd.x + 4, yEnd.y);
    ctx.fillText(`${zLabel} (${minZ.toFixed(1)}..${maxZ.toFixed(1)})`, zEnd.x - 4, zEnd.y - 6);
  }, [x, y, z, azimuth, elevation, zoom, appearance, xLabel, yLabel, zLabel]);

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = {
      active: true,
      startX: e.clientX,
      startY: e.clientY,
      startAzimuth: azimuth,
      startElevation: elevation,
    };
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!dragRef.current.active) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    setAzimuth((dragRef.current.startAzimuth + dx * 0.5) % 360);
    setElevation(Math.max(-85, Math.min(85, dragRef.current.startElevation - dy * 0.5)));
  };

  const handlePointerUp = () => {
    dragRef.current.active = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom(zVal => Math.max(0.4, Math.min(3, zVal * delta)));
  };

  return (
    <div className="surface-plot-3d" style={{background: 'var(--panel)', border: '1px solid var(--border)', padding: 12}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8}}>
        <strong style={{fontSize: 12, color: 'var(--text)'}}>{title}</strong>
        <div style={{display: 'flex', gap: 6}}>
          <Button aria-pressed={viewMode === 'isometric'} onClick={() => setPreset('isometric')}>
            3D Iso
          </Button>
          <Button aria-pressed={viewMode === 'top'} onClick={() => setPreset('top')}>
            Top View
          </Button>
          <Button aria-pressed={viewMode === 'front'} onClick={() => setPreset('front')}>
            Front
          </Button>
          <Button onClick={() => setZoom(1)}>Reset Zoom</Button>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        width={720}
        height={360}
        role="img"
        aria-label={title}
        style={{
          width: '100%',
          height: 360,
          display: 'block',
          cursor: 'grab',
          background: 'var(--canvas)',
          touchAction: 'none',
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onWheel={handleWheel}
      />
      <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 11, color: 'var(--muted)'}}>
        <span>Drag to rotate · Scroll to zoom</span>
        <span>
          Azimuth: {Math.round(azimuth)}° · Elevation: {Math.round(elevation)}° · Zoom: {zoom.toFixed(1)}x
        </span>
      </div>
    </div>
  );
}
