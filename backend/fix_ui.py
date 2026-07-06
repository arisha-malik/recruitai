import os, re

frontend_dir = r'c:\Users\HP\Documents\VS Code\AATA\frontend\src'

for root, dirs, files in os.walk(frontend_dir):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace light text in white inputs
            new_content = re.sub(r'bg-white(.*?)text-slate-100', r'bg-white\1text-slate-900', content, flags=re.DOTALL)
            
            # Replace text-slate-100 in main page headers (that don't have bg-gradient)
            if 'candidates\\[id]' not in path and 'jobs\\[id]' not in path:
                if '<h1 className="text-3xl font-extrabold tracking-tight text-slate-100' in new_content:
                    new_content = new_content.replace('<h1 className="text-3xl font-extrabold tracking-tight text-slate-100', '<h1 className="text-3xl font-extrabold tracking-tight text-slate-900')
                    
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Fixed contrast in {file}')
