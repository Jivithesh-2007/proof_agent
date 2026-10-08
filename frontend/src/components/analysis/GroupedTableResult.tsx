import React from 'react';
import { Table, BarChart3 } from 'lucide-react';

interface GroupedTableResultProps {
  data: Record<string, any>[];
  metric?: string;
  unit?: string;
}

export const GroupedTableResult: React.FC<GroupedTableResultProps> = ({ data, metric, unit }) => {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const groupCol = columns[0];
  const valCol = columns[1] || columns[0];

  // Compute max value for bar chart visualization
  const numericValues = data.map((row) => {
    const v = row[valCol];
    return typeof v === 'number' ? v : parseFloat(v) || 0;
  });
  const maxVal = Math.max(...numericValues, 1);

  return (
    <div className="bg-[#242726] border border-[#3C3B39] rounded-xl p-6 shadow-md space-y-6">
      <div className="flex items-center justify-between border-b border-[#3C3B39] pb-4">
        <div className="flex items-center gap-2">
          <Table className="w-5 h-5 text-[#E64A32]" />
          <h3 className="text-base font-bold text-[#F4F5EC]">
            Aggregated Group Results ({data.length} Groups)
          </h3>
        </div>
        <span className="text-xs font-mono text-[#F4F5EC]/60">
          Metric: <strong className="text-[#E18230]">{metric || valCol}</strong> {unit ? `(${unit})` : ''}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Table View */}
        <div className="overflow-x-auto border border-[#3C3B39] rounded-lg">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="bg-[#151918] text-[#F4F5EC]/70 border-b border-[#3C3B39]">
                {columns.map((c) => (
                  <th key={c} className="p-3 uppercase tracking-wider font-semibold">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#3C3B39] bg-[#242726]">
              {data.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#151918]/60 transition-colors">
                  {columns.map((c, cIdx) => (
                    <td
                      key={c}
                      className={`p-3 ${
                        cIdx === 1 ? 'text-[#E64A32] font-bold' : 'text-[#F4F5EC]'
                      }`}
                    >
                      {typeof row[c] === 'number' ? row[c].toLocaleString() : String(row[c])}
                      {cIdx === 1 && unit ? ` ${unit}` : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Bar Visualizer */}
        <div className="bg-[#151918] border border-[#3C3B39] rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-[#E18230] uppercase tracking-wider mb-2">
            <BarChart3 className="w-4 h-4" /> Group Breakdown
          </div>

          <div className="space-y-2 font-mono text-xs">
            {data.slice(0, 10).map((row, idx) => {
              const label = String(row[groupCol]);
              const rawVal = row[valCol];
              const numVal = typeof rawVal === 'number' ? rawVal : parseFloat(rawVal) || 0;
              const pct = Math.min(100, Math.max(5, (numVal / maxVal) * 100));

              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-[#F4F5EC] font-semibold">{label}</span>
                    <span className="text-[#E64A32] font-bold">
                      {numVal.toLocaleString()} {unit || ''}
                    </span>
                  </div>
                  <div className="w-full bg-[#242726] rounded-full h-2 overflow-hidden border border-[#3C3B39]">
                    <div
                      className="bg-gradient-to-r from-[#E18230] to-[#E64A32] h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
