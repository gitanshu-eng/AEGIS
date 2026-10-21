path = 'D:/AEGIS-local/frontend/src/components/MonitorForecast.tsx'
with open(path, encoding='utf-8') as f:
    content = f.read()

content = content.replace('r.escalation_probability', 'r.p_escalation')
content = content.replace('latest.escalation_probability', 'latest.p_escalation')
content = content.replace('r.actual_escalation === 1', 'false')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
