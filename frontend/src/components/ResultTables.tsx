import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ResultTable } from "@/lib/types";

/** Abreviaturas de la versión de consola, con su significado para el lector. */
const DIRECTION_NAMES: Record<string, string> = {
  "Der.": "Derecha", "Izq.": "Izquierda", "Alin.": "Alineado", "Ant.": "Anterior", "Pos.": "Posterior",
  "Rot.Ext.": "Rotación externa", "Rot.Int.": "Rotación interna",
};
const NEUTRAL = new Set(["Alin.", "Normal", "N/A", "Centrada", "Ideal"]);

export function Direction({ value }: { value: string }) {
  const neutral = NEUTRAL.has(value);
  return (
    <Badge variant={neutral ? "outline" : "secondary"} title={DIRECTION_NAMES[value] ?? value}
      className={neutral ? "text-muted-foreground" : "bg-accent text-accent-foreground"}>
      {value}
    </Badge>
  );
}

const unit = (column: string) => (column === "Ángulo" ? "°" : column === "Distancia" ? " cm" : "");

export default function ResultTables({ tables }: { tables: ResultTable[] }) {
  return (
    <div className="space-y-6">
      {tables.map((t) => (
        <section key={t.key} aria-label={t.title}>
          <h4 className="mb-1 text-sm font-medium">{t.title}</h4>
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-muted-foreground">{t.columns[0]}</TableHead>
                <TableHead className="text-muted-foreground">{t.columns[1]}</TableHead>
                <TableHead className="text-right text-muted-foreground">{t.columns[2]}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {t.rows.map((r) => (
                <TableRow key={r.item}>
                  <TableCell>{r.item}</TableCell>
                  <TableCell><Direction value={r.direction} /></TableCell>
                  <TableCell className="text-right tabular-nums">
                    {r.value.toFixed(2)}{unit(t.columns[2])}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
      ))}
    </div>
  );
}
