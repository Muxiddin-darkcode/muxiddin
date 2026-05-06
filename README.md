# Tugarak.uz (Frontend Skeleton)

Ushbu loyiha `Next.js + Tailwind CSS + shadcn` uslubida tayyorlangan boshlang'ich LMS dashboard skeleti.

## Nimalar qo'shildi

- Next.js App Router struktura
- Tailwind sozlamalari
- shadcn uslubidagi `Button`, `Card` komponentlari
- O'zbekcha matnlar uchun `lib/i18n/uz.ts`
- `Admin`, `O'qituvchi`, `Talaba` uchun sahifalar
- To'q ko'k sidebar va zamonaviy dashboard jadvali

## Ishga tushirish

```bash
npm install
npm run dev
```

Brauzerda oching: `http://localhost:3000`

## Mock login (backend siz)

`.env.local` yarating va quyidagini yozing:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_AUTH_MODE=mock
```

Login sahifasida test uchun:

- `admin` / istalgan parol -> Admin kabinet
- `teacher` / istalgan parol -> O'qituvchi kabinet
- `student` / istalgan parol -> Talaba kabinet
