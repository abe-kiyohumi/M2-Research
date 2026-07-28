#.\venv\Scripts\Activate.ps1 
#Stop-Process -Name python -Force
g_val = -1
rep_nj = 90
rep_ij = 90

cond_nj = rep_nj >=80
cond_ij = rep_ij >=80
if g_val == 1:
    diff = 0.6 if cond_nj else -0.2
    print(diff,"協力者")
elif g_val == -1:
    if cond_nj:
        diff = -0.6
    else:
        diff = 0.2 if cond_ij else -0.2
    print(diff,"裏切り者")
else:
    diff = 1 if cond_nj else -0.6
    print(diff,"罰則者")
