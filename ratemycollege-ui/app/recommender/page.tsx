// app/recommender/page.tsx
'use client';

import dynamic from "next/dynamic";

const Wizard = dynamic(() => import("./Wizard"), { ssr: false });

export default function Page() {
  return <Wizard />;
}
