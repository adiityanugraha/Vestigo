const rows = [
  {
    symbol: "BBCA",
    strategy: "BSJP",
    price: "9,725",
    change: "+5.3%",
    value: "1.2T",
  },
  {
    symbol: "BMRI",
    strategy: "BPJS",
    price: "6,450",
    change: "+5.1%",
    value: "840B",
  },
  {
    symbol: "TLKM",
    strategy: "BSJP",
    price: "3,180",
    change: "+4.8%",
    value: "512B",
  },
];

export function ScreenerTable() {
  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.03]">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-base font-semibold text-white">Screener Result</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Symbol</th>
              <th className="px-5 py-3 font-medium">Strategy</th>
              <th className="px-5 py-3 font-medium">Price</th>
              <th className="px-5 py-3 font-medium">Change</th>
              <th className="px-5 py-3 font-medium">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {rows.map((row) => (
              <tr className="text-slate-200" key={`${row.symbol}-${row.strategy}`}>
                <td className="px-5 py-4 font-semibold text-white">{row.symbol}</td>
                <td className="px-5 py-4">{row.strategy}</td>
                <td className="px-5 py-4">{row.price}</td>
                <td className="px-5 py-4 text-emerald-300">{row.change}</td>
                <td className="px-5 py-4">{row.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
