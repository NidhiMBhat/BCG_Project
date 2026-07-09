import os
import re

chart_dir = 'frontend/src/components/charts'

def update_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # Grid
    content = re.sub(r'stroke="rgba\(255,255,255,0\.05\)"', 'stroke="#e5e7eb"', content)
    # Ticks
    content = re.sub(r'tick={{ fontSize: 10, fill: ''#64748b'' }} tickLine={false}', 'tick={{ fontSize: 10, fill: \'#374151\' }} tickLine={{ stroke: \'#374151\' }} axisLine={{ stroke: \'#374151\' }}', content)
    # Line
    content = re.sub(r'type="monotone"', 'type="linear"', content)
    content = re.sub(r'strokeWidth={2}', 'strokeWidth={1.5}', content)
    content = re.sub(r'dot={false}', 'dot={{ r: 3, fill: \'currentColor\', strokeWidth: 0 }}', content)
    
    # Adjust specific AreaChart to LineChart for AIScoreChart if any
    content = content.replace('AreaChart', 'LineChart')
    content = content.replace('Area', 'Line')
    content = re.sub(r'fill="url\(#color.*\)"', '', content)
    content = re.sub(r'<defs>.*?</defs>', '', content, flags=re.DOTALL)
    
    with open(path, 'w') as f:
        f.write(content)

for f in os.listdir(chart_dir):
    if f.endswith('.jsx'):
        update_file(os.path.join(chart_dir, f))

print("Charts updated for matplotlib style")
