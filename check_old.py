import subprocess
out = subprocess.check_output(['git', 'show', 'HEAD~1:index.html']).decode('utf-8')
print('Old count:', out.count('<a href="blog/'))
