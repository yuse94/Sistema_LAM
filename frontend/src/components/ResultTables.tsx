import type { ResultTable } from "@/lib/types";

export default function ResultTables({ tables }: { tables: ResultTable[] }) {
  return (
    <div className="space-y-4">
      {tables.map((t) => (
        <table key={t.key} className="w-full overflow-hidden rounded border bg-white text-sm">
          <caption className="py-1 text-left font-medium">{t.title}</caption>
          <thead className="bg-slate-100">
            <tr>{t.columns.map((c) => <th key={c} className="px-3 py-1 text-left">{c}</th>)}</tr>
          </thead>
          <tbody>
            {t.rows.map((r) => (
              <tr key={r.item} className="border-t">
                <td className="px-3 py-1">{r.item}</td>
                <td className="px-3 py-1">{r.direction}</td>
                <td className="px-3 py-1 tabular-nums">{r.value.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
    </div>
  );
}
