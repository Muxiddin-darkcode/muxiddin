import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uz } from "@/lib/i18n/uz";

const rows = [
  { mavzu: "Matematika 7-sinf", guruh: "A-101", muddat: "2026-05-10", holat: "Tekshiruvda" },
  { mavzu: "Fizika laboratoriya", guruh: "B-204", muddat: "2026-05-12", holat: "Yangi" },
  { mavzu: "Ingliz tili essay", guruh: "C-301", muddat: "2026-05-14", holat: "Baholangan" }
];

export function AssignmentsTable() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{uz.dashboard.songgiTopshiriqlar}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="py-3 pr-4 font-medium">Mavzu</th>
                <th className="py-3 pr-4 font-medium">Guruh</th>
                <th className="py-3 pr-4 font-medium">Muddat</th>
                <th className="py-3 pr-4 font-medium">Holat</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.mavzu}-${row.guruh}`} className="border-b last:border-0">
                  <td className="py-3 pr-4 font-medium text-slate-900">{row.mavzu}</td>
                  <td className="py-3 pr-4 text-slate-700">{row.guruh}</td>
                  <td className="py-3 pr-4 text-slate-700">{row.muddat}</td>
                  <td className="py-3 pr-4 text-slate-700">{row.holat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
