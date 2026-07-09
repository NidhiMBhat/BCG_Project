import os

chart_dir = 'frontend/src/components/charts'

def replace_in_file(path, old, new):
    with open(path, 'r') as f:
        c = f.read()
    c = c.replace(old, new)
    with open(path, 'w') as f:
        f.write(c)

def fix_all():
    for f in os.listdir(chart_dir):
        if not f.endswith('.jsx'): continue
        path = os.path.join(chart_dir, f)
        
        # tick fix
        replace_in_file(path, "tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false}", "tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }}")
        
        # make dots more visible (matplotlib style)
        replace_in_file(path, "fill: 'currentColor'", "fill: '#1f77b4'")
        replace_in_file(path, "stroke=\"#f43f5e\"", "stroke=\"#1f77b4\"")
        replace_in_file(path, "stroke=\"#06b6d4\"", "stroke=\"#1f77b4\"")
        replace_in_file(path, "stroke=\"#8b5cf6\"", "stroke=\"#1f77b4\"")
        replace_in_file(path, "stroke=\"#f59e0b\"", "stroke=\"#1f77b4\"")
        replace_in_file(path, "strokeWidth={2}", "strokeWidth={1.5}")

fix_all()
print("Charts fixed")
