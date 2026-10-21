path = 'D:/AEGIS-local/frontend/src/components/MonitorForecast.tsx'
bt = chr(96)
ds = chr(36)
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

lines[39] = '          { label: "Escalation Prob", value: ' + bt + ds + '{(latest.escalation_probability * 100).toFixed(1)}%' + bt + ', hot: latest.escalation_probability > 0.5 },\n'
lines[43] = '          <div key={k.label} className={' + bt + 'rounded-lg border p-3 ' + ds + '{k.hot ? "border-red-500/50 bg-red-900/10" : "border-zinc-700 bg-zinc-900"}' + bt + '}>\n'
lines[45] = '      <div className={' + bt + 'text-xl font-mono font-bold ' + ds + '{k.hot ? "text-red-400" : "text-zinc-100"}' + bt + '}>{k.value}</div>\n'

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done')
for i in [39, 43, 45]:
    print(f'{i+1}: {repr(lines[i])}')
