import { useState, useMemo } from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    AreaChart, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer,
    ReferenceLine, ReferenceDot
} from 'recharts';
import { BarChart2, LineChart as LineIcon, PieChart as PieIcon, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { QueryResult } from '../../types';

interface DataVisualizerProps {
    result: QueryResult;
}

type ChartType = 'bar' | 'line' | 'pie' | 'area';

const CHART_COLORS = [
    '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b',
    '#ef4444', '#06b6d4', '#ec4899', '#84cc16',
    '#f97316', '#6366f1',
];

function isNumeric(value: any): boolean {
    if (value === null || value === undefined || value === '') return false;
    return !isNaN(Number(value));
}

function detectColumns(result: QueryResult): { labelCol: string; numericCols: string[] } {
    if (!result.columns.length || !result.rows.length) {
        return { labelCol: '', numericCols: [] };
    }

    const numericCols: string[] = [];
    const nonNumericCols: string[] = [];

    result.columns.forEach((col) => {
        const sampleValues = result.rows
            .slice(0, Math.min(result.rows.length, 10))
            .map((row) => (Array.isArray(row) ? row[result.columns.indexOf(col)] : row[col]));

        const numericCount = sampleValues.filter(isNumeric).length;

        if (numericCount > sampleValues.length * 0.6) {
            numericCols.push(col);
        } else {
            nonNumericCols.push(col);
        }
    });

    const labelCol = nonNumericCols[0] || result.columns[0];

    return { labelCol, numericCols: numericCols.filter((c) => c !== labelCol) };
}

function normalizeData(result: QueryResult): Record<string, any>[] {
    if (!result.rows.length) return [];

    if (Array.isArray(result.rows[0])) {
        return result.rows.map((row: any[]) => {
            const obj: Record<string, any> = {};
            result.columns.forEach((col, i) => {
                obj[col] = row[i];
            });
            return obj;
        });
    }
    return result.rows as Record<string, any>[];
}

function formatLabel(value: string | number): string {
    const str = String(value);
    if (str.length > 12) return str.substring(0, 12) + '…';
    return str;
}

function formatNumber(val: number): string {
    if (Math.abs(val) >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (Math.abs(val) >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toFixed(1);
}

// ── Statistical computations ──────────────────────────────────────────────────
interface ColStats {
    col: string;
    color: string;
    avg: number;
    min: number;
    max: number;
    minIdx: number;
    maxIdx: number;
    minLabel: string;
    maxLabel: string;
    growthPct: number | null;
}

function computeStats(
    data: Record<string, any>[],
    numericCols: string[],
    labelCol: string
): ColStats[] {
    return numericCols.map((col, i) => {
        const values = data.map((row) => Number(row[col]) || 0);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        let minVal = Infinity, maxVal = -Infinity, minIdx = 0, maxIdx = 0;
        values.forEach((v, idx) => {
            if (v < minVal) { minVal = v; minIdx = idx; }
            if (v > maxVal) { maxVal = v; maxIdx = idx; }
        });
        const first = values[0];
        const last = values[values.length - 1];
        const growthPct = values.length > 1 && Math.abs(first) > 1e-6
            ? ((last - first) / Math.abs(first)) * 100
            : null;

        return {
            col,
            color: CHART_COLORS[i % CHART_COLORS.length],
            avg,
            min: minVal,
            max: maxVal,
            minIdx,
            maxIdx,
            minLabel: String(data[minIdx]?.[labelCol] ?? ''),
            maxLabel: String(data[maxIdx]?.[labelCol] ?? ''),
            growthPct,
        };
    });
}
// ──────────────────────────────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-xl text-sm">
            <p className="font-semibold text-slate-700 mb-1">{label}</p>
            {payload.map((entry: any, i: number) => (
                <div key={i} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: entry.color }} />
                    <span className="text-slate-500">{entry.name}:</span>
                    <span className="font-medium text-slate-800">
                        {typeof entry.value === 'number'
                            ? entry.value.toLocaleString()
                            : entry.value}
                    </span>
                </div>
            ))}
        </div>
    );
};

const PieCustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const entry = payload[0];
    return (
        <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-xl text-sm">
            <p className="font-semibold text-slate-700">{entry.name}</p>
            <p className="text-slate-600">
                <span className="font-medium">{entry.value?.toLocaleString()}</span>
                {' '}({((entry.percent || 0) * 100).toFixed(1)}%)
            </p>
        </div>
    );
};

const CHART_OPTIONS: { type: ChartType; label: string; icon: React.ReactNode }[] = [
    { type: 'bar', label: 'Bar', icon: <BarChart2 className="w-3.5 h-3.5" /> },
    { type: 'line', label: 'Line', icon: <LineIcon className="w-3.5 h-3.5" /> },
    { type: 'area', label: 'Area', icon: <TrendingUp className="w-3.5 h-3.5" /> },
    { type: 'pie', label: 'Pie', icon: <PieIcon className="w-3.5 h-3.5" /> },
];

// ── Stats Summary Panel Component ─────────────────────────────────────────────
const StatsSummary = ({ stats }: { stats: ColStats[] }) => {
    if (!stats.length) return null;
    return (
        <div className="flex flex-wrap gap-3 px-4 py-3 border-t border-slate-100 bg-slate-50/60">
            {stats.map((s) => (
                <div key={s.col} className="flex items-center gap-2 bg-white border border-slate-100 rounded-lg px-3 py-2 shadow-sm text-[11px]">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                    <span className="font-semibold text-slate-700">{s.col}</span>
                    <span className="text-slate-400">|</span>
                    <span className="text-slate-500">Avg: <span className="font-bold text-slate-700">{formatNumber(s.avg)}</span></span>
                    <span className="text-slate-400">|</span>
                    <span className="text-slate-500">Peak: <span className="font-bold text-green-600">{formatNumber(s.max)}</span></span>
                    <span className="text-slate-400">|</span>
                    <span className="text-slate-500">Low: <span className="font-bold text-red-500">{formatNumber(s.min)}</span></span>
                    {s.growthPct !== null && (
                        <>
                            <span className="text-slate-400">|</span>
                            <span className={`flex items-center gap-0.5 font-bold ${s.growthPct >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                {s.growthPct >= 0
                                    ? <TrendingUp className="w-3 h-3" />
                                    : <TrendingDown className="w-3 h-3" />
                                }
                                {s.growthPct >= 0 ? '+' : ''}{s.growthPct.toFixed(1)}%
                            </span>
                        </>
                    )}
                </div>
            ))}
        </div>
    );
};

// ── Annotation elements for Recharts ──────────────────────────────────────────
function renderAnnotations(stats: ColStats[], data: Record<string, any>[], labelCol: string) {
    const elements: React.ReactNode[] = [];

    stats.forEach((s) => {
        // Average reference line
        elements.push(
            <ReferenceLine
                key={`avg-${s.col}`}
                y={s.avg}
                stroke={s.color}
                strokeDasharray="6 4"
                strokeOpacity={0.6}
                strokeWidth={1.5}
                label={{
                    value: `Avg: ${formatNumber(s.avg)}`,
                    position: 'insideTopRight',
                    fill: s.color,
                    fontSize: 10,
                    fontWeight: 700,
                }}
            />
        );

        // Max anomaly dot (green ring)
        const maxLabel = data[s.maxIdx]?.[labelCol];
        if (maxLabel !== undefined) {
            elements.push(
                <ReferenceDot
                    key={`max-${s.col}`}
                    x={maxLabel}
                    y={s.max}
                    r={10}
                    fill="transparent"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    label={{
                        value: `▲ ${formatNumber(s.max)}`,
                        position: 'top',
                        fill: '#10b981',
                        fontSize: 9,
                        fontWeight: 700,
                    }}
                />
            );
        }

        // Min anomaly dot (red ring) — only if different from max
        if (s.minIdx !== s.maxIdx) {
            const minLabel = data[s.minIdx]?.[labelCol];
            if (minLabel !== undefined) {
                elements.push(
                    <ReferenceDot
                        key={`min-${s.col}`}
                        x={minLabel}
                        y={s.min}
                        r={10}
                        fill="transparent"
                        stroke="#ef4444"
                        strokeWidth={2.5}
                        label={{
                            value: `▼ ${formatNumber(s.min)}`,
                            position: 'bottom',
                            fill: '#ef4444',
                            fontSize: 9,
                            fontWeight: 700,
                        }}
                    />
                );
            }
        }
    });

    return elements;
}

// ──────────────────────────────────────────────────────────────────────────────

const DataVisualizer = ({ result }: DataVisualizerProps) => {
    const { labelCol, numericCols } = useMemo(() => detectColumns(result), [result]);
    const data = useMemo(() => normalizeData(result), [result]);

    const stats = useMemo(() => {
        if (!data.length || !numericCols.length) return [];
        return computeStats(data.slice(0, 50), numericCols, labelCol);
    }, [data, numericCols, labelCol]);

    // Suggest best chart type based on data shape
    const defaultChart: ChartType = useMemo(() => {
        if (numericCols.length === 0) return 'bar';
        if (data.length <= 8 && numericCols.length === 1) return 'pie';
        if (data.length > 20) return 'area';
        return 'bar';
    }, [data.length, numericCols.length]);

    const [chartType, setChartType] = useState<ChartType>(defaultChart);

    if (!numericCols.length) {
        return (
            <div className="mt-4 flex flex-col items-center justify-center gap-2 py-10 text-slate-400 text-sm bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <AlertCircle className="w-6 h-6" />
                <p>No numeric columns detected for visualization.</p>
                <p className="text-xs text-slate-400">Charts require at least one numeric column in the results.</p>
            </div>
        );
    }

    if (!data.length) {
        return (
            <div className="mt-4 py-10 text-center text-sm text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                No data to visualize.
            </div>
        );
    }

    // For pie chart, only use first numeric col
    const pieDataKey = numericCols[0];

    const renderChart = () => {
        const commonProps = {
            data,
            margin: { top: 20, right: 20, left: 0, bottom: 40 },
        };

        const displayData = data.slice(0, 50);
        const annotations = renderAnnotations(stats, displayData, labelCol);

        if (chartType === 'pie') {
            const pieData = data.slice(0, 20).map((row) => ({
                name: formatLabel(row[labelCol] ?? ''),
                value: Number(row[pieDataKey]) || 0,
            }));

            return (
                <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                        <Pie
                            data={pieData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="45%"
                            outerRadius={100}
                            innerRadius={40}
                            paddingAngle={3}
                            label={({ name, percent }) =>
                                percent > 0.04 ? `${name} ${(percent * 100).toFixed(0)}%` : ''
                            }
                            labelLine={true}
                        >
                            {pieData.map((_, index) => (
                                <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<PieCustomTooltip />} />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            );
        }

        const xKey = labelCol;

        if (chartType === 'line') {
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart {...commonProps} data={displayData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} tickFormatter={formatLabel} angle={-30} textAnchor="end" height={50} />
                        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} width={60} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        {numericCols.map((col, i) => (
                            <Line
                                key={col}
                                type="monotone"
                                dataKey={col}
                                stroke={CHART_COLORS[i % CHART_COLORS.length]}
                                strokeWidth={2.5}
                                dot={{ r: 3 }}
                                activeDot={{ r: 5 }}
                            />
                        ))}
                        {annotations}
                    </LineChart>
                </ResponsiveContainer>
            );
        }

        if (chartType === 'area') {
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <AreaChart {...commonProps} data={displayData}>
                        <defs>
                            {numericCols.map((col, i) => (
                                <linearGradient key={col} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.02} />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} tickFormatter={formatLabel} angle={-30} textAnchor="end" height={50} />
                        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} width={60} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        {numericCols.map((col, i) => (
                            <Area
                                key={col}
                                type="monotone"
                                dataKey={col}
                                stroke={CHART_COLORS[i % CHART_COLORS.length]}
                                strokeWidth={2.5}
                                fill={`url(#grad-${i})`}
                            />
                        ))}
                        {annotations}
                    </AreaChart>
                </ResponsiveContainer>
            );
        }

        // Default: Bar
        return (
            <ResponsiveContainer width="100%" height={300}>
                <BarChart {...commonProps} data={displayData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey={xKey} tick={{ fontSize: 11 }} tickFormatter={formatLabel} angle={-30} textAnchor="end" height={50} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} width={60} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {numericCols.map((col, i) => (
                        <Bar
                            key={col}
                            dataKey={col}
                            fill={CHART_COLORS[i % CHART_COLORS.length]}
                            radius={[4, 4, 0, 0]}
                            maxBarSize={50}
                        />
                    ))}
                    {annotations}
                </BarChart>
            </ResponsiveContainer>
        );
    };

    return (
        <div className="mt-3 bg-white border border-slate-100 rounded-xl shadow-sm overflow-hidden">
            {/* Chart toolbar */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50/60">
                <div className="flex items-center gap-1.5">
                    <BarChart2 className="w-4 h-4 text-purple-500" />
                    <span className="text-xs font-semibold text-slate-600">Visualization</span>
                    {data.length > 50 && (
                        <span className="text-[10px] bg-amber-100 text-amber-700 rounded-full px-2 py-0.5 font-medium">
                            Showing first 50 rows
                        </span>
                    )}
                </div>
                <div className="flex gap-1">
                    {CHART_OPTIONS.map(({ type, label, icon }) => (
                        <Button
                            key={type}
                            variant={chartType === type ? 'default' : 'ghost'}
                            size="sm"
                            className={`h-7 px-2.5 gap-1 text-xs font-medium transition-all ${chartType === type
                                ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-sm'
                                : 'text-slate-500 hover:text-slate-700'
                                }`}
                            onClick={() => setChartType(type)}
                        >
                            {icon}
                            {label}
                        </Button>
                    ))}
                </div>
            </div>

            {/* Chart area */}
            <div className="px-3 pt-3 pb-1">
                {renderChart()}
            </div>

            {/* Statistical Annotations Summary */}
            {chartType !== 'pie' && <StatsSummary stats={stats} />}

            {/* Legend info */}
            <div className="px-4 py-2 border-t border-slate-50 text-[10px] text-slate-400 flex items-center gap-3">
                <span>X-axis: <span className="font-medium text-slate-500">{labelCol}</span></span>
                <span>Y-axis: <span className="font-medium text-slate-500">{numericCols.join(', ')}</span></span>
                <span>{data.length} data point{data.length !== 1 ? 's' : ''}</span>
            </div>
        </div>
    );
};

export default DataVisualizer;

