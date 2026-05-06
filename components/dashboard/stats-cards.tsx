import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uz } from "@/lib/i18n/uz";

const cards = [
  { title: uz.dashboard.jamiTalabalar, value: "1,240" },
  { title: uz.dashboard.jamiOqituvchilar, value: "86" },
  { title: uz.dashboard.faolGuruhlar, value: "54" },
  { title: uz.dashboard.davomat, value: "92%" }
];

export function StatsCards() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-500">{card.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-slate-900">{card.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
